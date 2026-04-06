import asyncio
import json
import re
import requests
from bs4 import BeautifulSoup

from langgraph.types import interrupt

from MCP.research.search_docs import search_docs
from MCP.research.youtube_tools import youtube_search, youtube_transcript

from states import State, Roadmap, Task, Resource, FetchedContent, QuizQuestion
from utils.llm import llm


# ============================================================
# CONSTANTS — domain filter lists
# ============================================================

_BLOCKED_DOMAINS = {
    "medium.com",
    "towardsdatascience.com",
    "analyticsvidhya.com",
    "kdnuggets.com",
    "dzone.com",
    "substack.com",
}

_PREFERRED_DOMAINS = {
    "docs.langchain.com":       1.00,
    "python.langchain.com":     1.00,
    "langchain-ai.github.io":   1.00,
    "api.python.langchain.com": 0.98,
    "docs.smith.langchain.com": 0.98,
    "readthedocs.io":           0.97,
    "docs.":                    0.96,
    "documentation":            0.96,
    "freecodecamp.org":         0.95,
    "mintlify.app":             0.95,
    "github.com":               0.90,
    "realpython.com":           0.90,
    "learnpython.org":          0.88,
    "dev.to":                   0.82,
    "hashnode.com":             0.82,
    "tutorial":                 0.80,
    "guide":                    0.78,
}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

_MIN_CONTENT_CHARS = 1000


# ============================================================
# ROADMAP NODE
# ============================================================

def roadmap_to_tasks(roadmap: Roadmap) -> list[Task]:
    return [Task(title=t) for t in roadmap.tasks]


def roadmap_node(state: State) -> dict:

    print(f"[roadmap_node] Generating roadmap for topic: '{state.topic}'")

    prompt = f"""
    You are an expert tutor who creates precise, topic-specific learning roadmaps.

    Create a step-by-step roadmap to learn: {state.topic}

    STRICT RULES:
    - Every task MUST be directly about "{state.topic}".
    - Do NOT include unrelated subjects unless they are a direct prerequisite.
    - Generate between 6 and 10 tasks.
    - Tasks must progress from beginner to advanced.
    - Each task title: 5–10 words max.
    - Use "{state.topic}" in titles where appropriate.

    Example for "LangGraph":
    1. What is LangGraph and Why Use It
    2. LangGraph State Management
    3. Nodes and Edges in LangGraph
    4. Conditional Routing in LangGraph
    5. Memory and Checkpointing in LangGraph
    6. Building Agents with LangGraph
    7. Multi-agent Systems with LangGraph
    8. Deploying LangGraph Agents

    Now generate the roadmap for: {state.topic}
    """

    roadmap_llm = llm.with_structured_output(Roadmap)
    tasks = roadmap_to_tasks(roadmap_llm.invoke(prompt))

    print(f"[roadmap_node] Generated {len(tasks)} tasks:")
    for i, t in enumerate(tasks):
        print(f"  {i + 1}. {t.title}")

    return {"roadmap": tasks, "current_task_index": 0}


# ============================================================
# ROADMAP HITL REVIEW
# ============================================================

def roadmap_review_node(state: State):
    return interrupt({
        "type": "roadmap_review",
        "roadmap": [t.title for t in state.roadmap],
        "options": ["add", "delete", "edit", "confirm"],
    })


# ============================================================
# APPLY USER EDIT
# ============================================================

def apply_roadmap_edit_node(state: State) -> dict:

    action = state.user_action["action"]
    roadmap = list(state.roadmap)

    if action == "add":
        roadmap.append(Task(title=state.user_action["task"]))
    elif action == "delete":
        roadmap.pop(state.user_action["index"])
    elif action == "edit":
        roadmap[state.user_action["index"]].title = state.user_action["task"]

    return {"roadmap": roadmap}


# ============================================================
# HELPERS — domain scoring & filtering
# ============================================================

def getYoutubeVideoId(url: str | None) -> str | None:
    if not url: return None
    regExp = r"^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*"
    match = re.match(regExp, url)
    return (match.group(2)) if (match and len(match.group(2)) == 11) else None

def _domain_of(url: str) -> str:
    try:
        from urllib.parse import urlparse
        return urlparse(url).hostname or ""
    except Exception:
        return url.lower()


def _is_blocked(url: str) -> bool:
    host = _domain_of(url)
    return any(blocked in host for blocked in _BLOCKED_DOMAINS)


def _score_resource(url: str, rtype: str) -> float:
    host = _domain_of(url)
    url_lower = url.lower()
    for domain, score in _PREFERRED_DOMAINS.items():
        if domain in host or domain in url_lower:
            return score
    if rtype == "video":
        return 0.75
    return 0.70


# ============================================================
# RESOURCE NODE
# ============================================================

async def _extract_video_segment(title: str, url: str, task_title: str) -> dict:
    DEFAULT = {
        "start_timestamp": "00:00",
        "end_timestamp": "05:00",
        "reason": "Core section covering the topic.",
        "transcript_snippet": "",
    }

    try:
        transcript_data = await youtube_transcript(url)
        has_transcript = bool(transcript_data and transcript_data.get("transcript"))
    except Exception as e:
        print(f"[youtube_segment] Transcript fetch error for {url}: {e}")
        has_transcript = False

    if has_transcript:
        transcript_text = transcript_data["transcript"]
        print(f"[youtube_segment] Transcript fetched ({len(transcript_text)} chars): {title}")
        source_block = f"TRANSCRIPT:\n{transcript_text[:4000]}"
        instruction = (
            "Estimate realistic MM:SS timestamps based on where the relevant "
            "content appears (~130 words per minute of speech)."
        )
    else:
        print(f"[youtube_segment] No transcript — using LLM estimation for: {title}")
        source_block = f'Video title: "{title}"\nURL: {url}'
        instruction = "Estimate timestamps for the most relevant 2-to-6 minute segment."

    prompt = f"""
    You are an expert educator. A student needs to learn: "{task_title}"

    {source_block}

    {instruction}

    Respond ONLY with a valid JSON object — no markdown:
    {{
        "start_timestamp": "MM:SS",
        "end_timestamp": "MM:SS",
        "reason": "One sentence explaining why this segment is useful.",
        "transcript_snippet": "1-2 sentence excerpt (empty string if no transcript)."
    }}
    """
    try:
        raw = llm.invoke(prompt).content.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        print(f"[youtube_segment] Timestamps: "
              f"{data.get('start_timestamp')} → {data.get('end_timestamp')} | {title}")
        return {
            "start_timestamp": data.get("start_timestamp", DEFAULT["start_timestamp"]),
            "end_timestamp":   data.get("end_timestamp",   DEFAULT["end_timestamp"]),
            "reason":          data.get("reason",          DEFAULT["reason"]),
            "transcript_snippet": data.get("transcript_snippet", ""),
        }
    except Exception as e:
        print(f"[youtube_segment] LLM parse failed for '{title}': {e}")
        return DEFAULT


async def resource_node(state: State) -> dict:

    current_task = state.roadmap[state.current_task_index]
    query = current_task.title

    print(f"\n[resource_node] Current task : {current_task.title}")
    print(f"[resource_node] Task index   : {state.current_task_index + 1}/{len(state.roadmap)}")

    try:
        docs_result, videos_result = await asyncio.gather(
            search_docs(query),
            youtube_search(query),
            return_exceptions=True,
        )
    except Exception as e:
        print(f"[resource_node] Search failed entirely: {e}")
        docs_result, videos_result = [], []

    if isinstance(docs_result, Exception):
        print(f"[resource_node] search_docs failed: {docs_result}")
        docs_result = []
    if isinstance(videos_result, Exception):
        print(f"[resource_node] youtube_search failed: {videos_result}")
        videos_result = []

    raw: list[tuple[str, str, str]] = []
    seen: set[str] = set()

    for d in (docs_result or []):
        url   = (d.get("url") or "").strip()
        title = (d.get("title") or "Untitled").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        raw.append((title, url, "docs"))

    for v in (videos_result or []):
        url   = (v.get("url") or "").strip()
        title = (v.get("title") or "Untitled").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        raw.append((title, url, "video"))

    before_filter = len(raw)
    raw = [(t, u, r) for t, u, r in raw if not _is_blocked(u)]
    print(f"[resource_node] {before_filter - len(raw)} blocked-domain URL(s) removed. "
          f"{len(raw)} remaining.")

    if len(raw) < 3:
        print(f"[resource_node] Only {len(raw)} after filtering — broadening query...")
        for broader in [
            f"{state.topic} {query} tutorial guide",
            f"{state.topic} official documentation",
        ]:
            try:
                extra = await search_docs(broader)
                if isinstance(extra, list):
                    for d in extra:
                        url   = (d.get("url") or "").strip()
                        title = (d.get("title") or "Untitled").strip()
                        if not url or url in seen or _is_blocked(url):
                            continue
                        seen.add(url)
                        raw.append((title, url, "article"))
            except Exception as e:
                print(f"[resource_node] Broader search '{broader}' failed: {e}")
            if len(raw) >= 3:
                break

    scored = sorted(raw, key=lambda r: _score_resource(r[1], r[2]), reverse=True)
    top = scored[:5]

    print(f"[resource_node] Resources selected: {len(top)} "
          f"(from {len(scored)} qualified candidates)")

    resources: list[Resource] = []
    for title, url, rtype in top:
        if rtype == "video":
            seg = await _extract_video_segment(title, url, current_task.title)
            resource = Resource(
                title=title, url=url, type="video",
                score=_score_resource(url, rtype),
                start_timestamp=seg["start_timestamp"],
                end_timestamp=seg["end_timestamp"],
                reason=seg["reason"],
            )
        else:
            resource = Resource(
                title=title, url=url, type=rtype,
                score=_score_resource(url, rtype),
            )
        resources.append(resource)

    # Print resource list for the learner
    print(f"\n{'─' * 55}")
    print(f"📚  Recommended Resources for: {current_task.title}")
    print(f"{'─' * 55}")
    for i, r in enumerate(resources, 1):
        if r.type == "video":
            print(f"  {i}. [VIDEO] {r.title}")
            print(f"         ▶ Watch: {r.start_timestamp} → {r.end_timestamp}")
            print(f"         💡 {r.reason}")
            print(f"         🔗 {r.url}")
        else:
            print(f"  {i}. [{r.type.upper()}] {r.title}")
            print(f"         🔗 {r.url}")
    print(f"{'─' * 55}\n")

    updated = list(state.roadmap)
    updated[state.current_task_index].resources = resources
    return {"roadmap": updated}


# ============================================================
# FETCH RESOURCE CONTENT NODE
# ============================================================

def _bs4_extract(html: str, url: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "header", "footer",
                      "aside", "form", "noscript", "iframe"]):
        tag.decompose()

    article = (
        soup.find("article")
        or soup.find("main")
        or soup.find(id=re.compile(r"content|article|main|post", re.I))
        or soup.find(class_=re.compile(r"content|article|main|post|body", re.I))
        or soup.body
    )

    if article is None:
        return ""

    text = article.get_text(separator="\n")
    lines = [l.strip() for l in text.splitlines()]
    lines = [l for l in lines if l]
    return "\n".join(lines)


def _fetch_with_bs4(url: str) -> str:
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=12, allow_redirects=True)
        resp.raise_for_status()
    except Exception as e:
        print(f"[fetch_resource_content] HTTP error for {url}: {e}")
        return ""

    html = resp.text
    text = ""

    try:
        import trafilatura
        extracted = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
        )
        if extracted and len(extracted.strip()) >= _MIN_CONTENT_CHARS:
            text = extracted.strip()
    except Exception:
        pass

    if not text or len(text) < _MIN_CONTENT_CHARS:
        bs_text = _bs4_extract(html, url)
        if len(bs_text) > len(text):
            text = bs_text

    return text[:8000] if text else ""


async def _exa_highlights_fallback(resource: Resource) -> str:
    try:
        results = await search_docs(resource.title)
        for r in (results or []):
            if r.get("url") == resource.url and r.get("highlights"):
                hl = r["highlights"]
                joined = "\n".join(hl) if isinstance(hl, list) else str(hl)
                if len(joined) >= 200:
                    return joined
    except Exception as e:
        print(f"[fetch_resource_content] Exa fallback failed for {resource.url}: {e}")
    return ""


async def fetch_resource_content_node(state: State) -> dict:

    current_task = state.roadmap[state.current_task_index]
    resources = current_task.resources

    print(f"\n[fetch_resource_content] Current task  : {current_task.title}")
    print(f"[fetch_resource_content] Fetching content for {len(resources)} resource(s)...")

    fetched: list[FetchedContent] = []

    for r in resources:
        content = ""

        try:
            if r.type == "video":
                transcript_data = await youtube_transcript(r.url)
                if transcript_data and transcript_data.get("transcript"):
                    content = transcript_data["transcript"]
                    print(f"[fetch_resource_content] [VIDEO ] {len(content):>6} chars — {r.title}")
                else:
                    print(f"[fetch_resource_content] [VIDEO ] no transcript — {r.url}")
            else:
                content = await asyncio.to_thread(_fetch_with_bs4, r.url)

                if len(content) >= _MIN_CONTENT_CHARS:
                    print(f"[fetch_resource_content] [{r.type.upper():5}] "
                          f"{len(content):>6} chars (HTTP) — {r.title}")
                else:
                    print(f"[fetch_resource_content] [{r.type.upper():5}] "
                          f"HTTP extraction too short ({len(content)} chars) "
                          f"— trying Exa highlights...")
                    hl_content = await _exa_highlights_fallback(r)
                    if len(hl_content) >= 200:
                        content = hl_content
                        print(f"[fetch_resource_content] [{r.type.upper():5}] "
                              f"{len(content):>6} chars (Exa hl) — {r.title}")
                    else:
                        print(f"[fetch_resource_content] [{r.type.upper():5}] "
                              f"DISCARDED (all extractors failed) — {r.url}")
                        content = ""

        except Exception as e:
            print(f"[fetch_resource_content] Unexpected error for {r.url}: {e}")
            content = ""

        if content and len(content) >= _MIN_CONTENT_CHARS:
            fetched.append(FetchedContent(
                title=r.title,
                url=r.url,
                type=r.type,
                content=content,
                start_timestamp=r.start_timestamp,
                end_timestamp=r.end_timestamp,
                reason=r.reason,
            ))

    print(f"[fetch_resource_content] Extracted {len(fetched)} usable source(s) "
          f"(≥{_MIN_CONTENT_CHARS} chars) out of {len(resources)} resources")

    return {"resource_contents": fetched}


# ============================================================
# RESEARCH NODE
# ============================================================

def research_node(state: State) -> dict:

    current_task = state.roadmap[state.current_task_index]
    rc = state.resource_contents

    print(f"\n[research_node] Current task: {current_task.title}")
    print(f"[research_node] Synthesizing knowledge from {len(rc)} document(s)")

    if rc:
        source_blocks = []
        for i, doc in enumerate(rc, 1):
            header = f"SOURCE {i} — {doc.title} [{doc.type.upper()}]\nURL: {doc.url}"
            if doc.type == "video" and doc.start_timestamp:
                header += (f"\nWatch: {doc.start_timestamp} → {doc.end_timestamp}"
                           f"  |  {doc.reason}")
            source_blocks.append(header + f"\n\n{doc.content[:2000]}")

        sources_text = ("\n\n" + "─" * 60 + "\n\n").join(source_blocks)

        prompt = f"""
You are an expert software engineer and educator writing a comprehensive lesson.

SUBJECT : {state.topic}
LESSON  : {current_task.title}
SOURCES : {len(rc)} real documents (provided below)

━━━ SOURCES ━━━
{sources_text}
━━━ END SOURCES ━━━

Using ONLY the information in the sources above, produce a thorough lesson note
in the following exact structure. Do NOT fabricate information not in the sources.

SUMMARY:
Write 2-4 clear paragraphs explaining what "{current_task.title}" is,
why it matters, and how it works.

KEY POINTS:
- List 5-7 precise, actionable bullet points a learner must remember.

CODE SNIPPETS:
Provide 1-3 short, realistic code examples (if the topic is technical).
Use fenced code blocks with the correct language tag, e.g. ```python.

EXAMPLES:
- Give 2-3 concrete real-world examples drawn from the sources.

KEY TAKEAWAYS:
- Summarise the 3-5 most important lessons in one sentence each.
"""

    else:
        print(f"[research_node] ⚠ No fetched content — falling back to LLM knowledge.")
        prompt = f"""
You are an expert software engineer and educator.
A learner is studying: {state.topic}
Current lesson: {current_task.title}

No external sources are available. Use your own knowledge.

SUMMARY:
<2-4 paragraphs>

KEY POINTS:
- <5-7 bullet points>

CODE SNIPPETS:
<1-3 relevant code examples in fenced blocks>

EXAMPLES:
- <2-3 concrete examples>

KEY TAKEAWAYS:
- <3-5 one-sentence takeaways>
"""

    response = llm.invoke(prompt)
    updated = list(state.roadmap)
    updated[state.current_task_index].knowledge = response.content

    print(f"[research_node] Knowledge generated ({len(response.content)} chars)")
    return {"roadmap": updated}


# ============================================================
# EXPLAIN NODE
# ============================================================

def explain_node(state: State) -> dict:

    task = state.roadmap[state.current_task_index]
    print(f"\n[explain_node] Teaching: '{task.title}' "
          f"(task {state.current_task_index + 1}/{len(state.roadmap)})")

    prompt = f"""
You are a clear, engaging tutor teaching: {state.topic}

Current lesson: {task.title}

Research notes:
{task.knowledge}

Deliver a well-structured lesson with:
- Clear headings
- Step-by-step explanations
- Concrete code examples where relevant
- A short "What you learned" summary at the end
"""

    lesson_text = llm.invoke(prompt).content

    return {"lesson": lesson_text}


# ============================================================
# ASK QUIZ PERMISSION NODE
# ============================================================

def ask_quiz_permission_node(state: State):
    return interrupt({
        "type": "quiz_permission",
        "message": (
            f"✅  Lesson complete: '{state.roadmap[state.current_task_index].title}'\n"
            "Would you like to take a quiz to test your understanding? (yes / no)"
        ),
    })


def quiz_permission_router(state: State) -> str:
    if state.quiz_permission is True:
        return "quiz"
    return "progress"


# ============================================================
# QUIZ NODE
# ============================================================

def quiz_node(state: State) -> dict:

    task = state.roadmap[state.current_task_index]
    print(f"\n[quiz_node] Generating quiz for: '{task.title}' "
          f"(task {state.current_task_index + 1}/{len(state.roadmap)})")

    prompt = f"""
You are an expert educator creating a short quiz.

Topic    : {task.title}
Knowledge: {task.knowledge}

Generate exactly 3 quiz questions.
For each provide the question and a concise correct answer (1-3 sentences).

Respond ONLY with a valid JSON array — no markdown, no extra text:
[
    {{"question": "...", "correct_answer": "..."}},
    {{"question": "...", "correct_answer": "..."}},
    {{"question": "...", "correct_answer": "..."}}
]
"""

    raw = llm.invoke(prompt).content.strip().replace("```json", "").replace("```", "").strip()

    try:
        questions = [QuizQuestion(**q) for q in json.loads(raw)]
    except Exception as e:
        print(f"[quiz_node] JSON parse failed ({e}), using fallback question.")
        questions = [QuizQuestion(
            question=f"Explain the key concept of '{task.title}' in your own words.",
            correct_answer="A comprehensive explanation of the topic.",
        )]

    lines = [f"Quiz — {task.title}\n"]
    for i, q in enumerate(questions, 1):
        lines.append(f"Q{i}: {q.question}")
    quiz_text = "\n".join(lines)

    print(f"[quiz_node] Generated {len(questions)} question(s).")

    return {
        "quiz_questions": questions,
        "quiz_text": quiz_text,
        "user_answers": [],
        "evaluation_result": None,
    }


# ============================================================
# QUIZ HITL — collect user answers
# ============================================================

def quiz_hitl_node(state: State):
    return interrupt({
        "type": "quiz_answer",
        "quiz_text": state.quiz_text,
        "questions": [q.question for q in state.quiz_questions],
    })


# ============================================================
# EVALUATE QUIZ NODE
# ============================================================

def evaluate_quiz_node(state: State) -> dict:

    questions = state.quiz_questions
    answers   = state.user_answers

    print(f"\n[evaluate_quiz_node] Evaluating {len(questions)} question(s)...")

    if not answers:
        print("[evaluate_quiz_node] No answers found — skipping.")
        return {"evaluation_result": "No answers were provided for this quiz."}

    qa_pairs = ""
    for i, q in enumerate(questions):
        user_ans = answers[i] if i < len(answers) else "(no answer)"
        qa_pairs += (
            f"\nQ{i + 1}: {q.question}\n"
            f"Correct : {q.correct_answer}\n"
            f"Student : {user_ans}\n"
        )

    prompt = f"""
You are a strict but encouraging tutor evaluating quiz answers.

Topic: {state.roadmap[state.current_task_index].title}
{qa_pairs}

For EACH question:
1. Mark CORRECT or INCORRECT.
2. If INCORRECT — explain the correct answer in 2-3 sentences.
3. If CORRECT — acknowledge warmly in one sentence.

End with:
SCORE: X/{len(questions)}
"""

    evaluation = llm.invoke(prompt).content

    score_lines = [l for l in evaluation.splitlines() if l.strip().startswith("SCORE:")]
    score_str = score_lines[-1].replace("SCORE:", "").strip() if score_lines else "?/?"
    print(f"[evaluate_quiz_node] Quiz score: {score_str}")

    return {"evaluation_result": evaluation}


# ============================================================
# ASK CHALLENGE NODE  (NEW)
# ============================================================
# Fires after every evaluate_quiz.
# Uses interrupt() — consistent with every other HITL node in
# this codebase.  The test harness injects
# {"challenge_accepted": True/False} and resumes from this node
# so challenge_router fires correctly.
# ============================================================

def ask_challenge_node(state: State):
    task = state.roadmap[state.current_task_index]
    return interrupt({
        "type": "challenge_prompt",
        "message": (
            f"\n🏆  Ready for a challenge?\n"
            f"   I have a hands-on project for you based on what you just learned:\n"
            f"   '{task.title}'\n"
            "   Type  yes  to get the project brief, or  no  to move on."
        ),
    })


def challenge_router(state: State) -> str:
    """Route to 'project' if accepted, else jump straight to 'progress'."""
    return "project" if state.challenge_accepted is True else "progress"


# ============================================================
# PROJECT NODE  (NEW)
# ============================================================
# Generates a full project brief grounded in what was taught
# in the current task.  Printed for the learner, stored in
# state.project.
# ============================================================

def project_node(state: State) -> dict:

    task = state.roadmap[state.current_task_index]
    print(f"\n[project_node] Generating project for: '{task.title}'")

    prompt = f"""
You are an expert educator designing a practical learning project.

The student has just finished studying:
  Subject : {state.topic}
  Lesson  : {task.title}

Knowledge covered in this lesson:
{task.knowledge}

━━━ YOUR TASK ━━━
Design ONE well-scoped, hands-on project that:
1. Directly applies the concepts from "{task.title}".
2. Is completable in 1-3 hours by a motivated beginner.
3. Produces something tangible (a script, a small app, a notebook, etc.).
4. Reinforces the KEY POINTS and CODE patterns from the lesson.

Format the project brief EXACTLY as follows — use all six sections:

────────────────────────────────────────
🚀  PROJECT: <catchy one-line project title>
────────────────────────────────────────

🎯  OBJECTIVE
<2-3 sentences explaining what the student will build and what concept it cements>

📋  REQUIREMENTS
List every feature the finished project must have (4-7 bullet points):
- 
- 

🛠️  STEP-BY-STEP GUIDE
Break the build into 4-6 numbered steps, each with a short description and
a starter code snippet where relevant.

1. ...
2. ...

💡  HINTS & TIPS
- <2-3 tips to help the student avoid common mistakes>

🏁  STRETCH GOALS (optional — for fast finishers)
- <2 optional extensions that add depth without changing the core project>

✅  HOW TO KNOW YOU'RE DONE
<1-2 sentences describing what working output looks like>
────────────────────────────────────────
"""

    project_text = llm.invoke(prompt).content

    print(f"[project_node] Project brief generated ({len(project_text)} chars)")

    # Pretty-print the project for the learner right away
    print(f"\n{'═' * 60}")
    print(project_text)
    print(f"{'═' * 60}\n")

    return {"project": project_text}


# ============================================================
# PROGRESS NODE
# ============================================================

def progress_node(state: State) -> dict:

    next_index = state.current_task_index + 1
    total      = len(state.roadmap)

    print(f"\n[progress_node] Completed: '{state.roadmap[state.current_task_index].title}' "
          f"({state.current_task_index + 1}/{total})")

    if next_index < total:
        print(f"[progress_node] Next task: '{state.roadmap[next_index].title}'")
        return {
            "current_task_index": next_index,
            "resource_contents":  [],     # clear for next task
            "quiz_permission":    None,   # reset quiz gate
            "challenge_accepted": None,   # reset challenge gate
            # NOTE: intentionally NOT clearing "project" here.
            # The /challenge backend route reads state.project after
            # resume_until_interrupt() returns.  Because the next task's
            # full pipeline (resource → research → explain) runs inside
            # that same resume call, we must leave the project value in
            # state so it is still readable at the quiz_permission interrupt.
            # The backend captures it immediately and the value is naturally
            # overwritten only if the student earns another project later.
        }

    print("[progress_node] All tasks complete! 🎉")
    return {"finished": True}


# ============================================================
# ROUTERS
# ============================================================

def roadmap_router(state: State) -> str:
    return "resource" if state.user_action["action"] == "confirm" else "apply_edit"


def progress_router(state: State) -> str:
    return "end" if state.finished else "resource"
