import asyncio
import json
import re
import requests

from langgraph.types import interrupt

from MCP.research.search_docs import search_docs
from MCP.research.youtube_tools import youtube_search, youtube_transcript

from states import State, Roadmap, Task, Resource, FetchedContent, QuizQuestion
from utils.llm import llm


# ============================================================
# ROADMAP NODE
# ============================================================

def roadmap_to_tasks(roadmap: Roadmap):
    return [Task(title=task_title) for task_title in roadmap.tasks]


def roadmap_node(state: State):

    print(f"[roadmap_node] Generating roadmap for topic: '{state.topic}'")

    prompt = f"""
    You are an expert tutor who creates precise, topic-specific learning roadmaps.

    Create a step-by-step roadmap to learn: {state.topic}

    STRICT RULES:
    - Every single task MUST be directly and specifically about "{state.topic}".
    - Do NOT include unrelated subjects, general programming concepts, or adjacent
      topics unless they are a direct prerequisite specifically needed for "{state.topic}".
    - Generate between 6 and 10 tasks.
    - Tasks must progress from beginner to advanced level.
    - Each task must be a short, clear title (5–10 words max).
    - Use "{state.topic}" in task titles where appropriate to keep focus.

    Example — for topic "LangGraph":
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
    roadmap_output = roadmap_llm.invoke(prompt)
    tasks = roadmap_to_tasks(roadmap_output)

    print(f"[roadmap_node] Generated {len(tasks)} tasks:")
    for i, t in enumerate(tasks):
        print(f"  {i + 1}. {t.title}")

    return {
        "roadmap": tasks,
        "current_task_index": 0
    }


# ============================================================
# ROADMAP HITL REVIEW
# ============================================================

def roadmap_review_node(state: State):

    roadmap_titles = [t.title for t in state.roadmap]

    return interrupt(
        {
            "type": "roadmap_review",
            "roadmap": roadmap_titles,
            "options": ["add", "delete", "edit", "confirm"]
        }
    )


# ============================================================
# APPLY USER EDIT
# ============================================================

def apply_roadmap_edit_node(state: State):

    action = state.user_action["action"]
    roadmap = state.roadmap.copy()

    if action == "add":
        new_task = Task(title=state.user_action["task"])
        roadmap.append(new_task)

    elif action == "delete":
        idx = state.user_action["index"]
        roadmap.pop(idx)

    elif action == "edit":
        idx = state.user_action["index"]
        roadmap[idx].title = state.user_action["task"]

    return {"roadmap": roadmap}


# ============================================================
# RESOURCE NODE
# ============================================================
#
# Rules:
#   • Hard cap: 5 resources max, 3 minimum
#   • Preferred types: docs > tutorials/blogs > GitHub > YouTube
#   • Every video resource carries real timestamp metadata from
#     transcript analysis (see _extract_video_segment)
# ============================================================

def _score_resource(url: str, rtype: str) -> float:
    """
    Heuristic quality score so we keep the best resources when trimming to 5.
    Higher is better.
    """
    url_lower = url.lower()

    if any(x in url_lower for x in ["docs.", "documentation", "readthedocs", "official"]):
        return 1.0
    if rtype == "docs":
        return 0.95
    if "github.com" in url_lower:
        return 0.90
    if any(x in url_lower for x in ["tutorial", "guide", "how-to", "howto"]):
        return 0.85
    if any(x in url_lower for x in ["blog", "medium.com", "dev.to", "hashnode"]):
        return 0.80
    if rtype == "video" or "youtube.com" in url_lower or "youtu.be" in url_lower:
        return 0.75
    return 0.70


def _is_youtube_url(url: str) -> bool:
    return "youtube.com" in url or "youtu.be" in url


def _extract_video_id(url: str) -> str | None:
    match = re.search(r"(?:v=|youtu\.be/)([^&?/]+)", url)
    return match.group(1) if match else None


async def _extract_video_segment(
    title: str,
    url: str,
    task_title: str
) -> dict:
    """
    Fetch the YouTube transcript and ask the LLM to identify the single
    most relevant 2-to-6-minute segment for the current learning task.

    Returns a dict with:
        start_timestamp, end_timestamp, reason, transcript_snippet
    """
    DEFAULT = {
        "start_timestamp": "00:00",
        "end_timestamp": "05:00",
        "reason": "Core section covering the topic.",
        "transcript_snippet": ""
    }

    try:
        transcript_data = await youtube_transcript(url)
        if not transcript_data or not transcript_data.get("transcript"):
            print(f"[youtube_segment] No transcript available for: {url}")
            # Fall back to LLM estimation without transcript
            return await _llm_estimate_timestamps(title, url, task_title)

        transcript_text = transcript_data["transcript"]
        print(f"[youtube_segment] Transcript fetched ({len(transcript_text)} chars) for: {title}")

        prompt = f"""
        You are an expert educator. A student needs to learn about: "{task_title}"

        Below is a transcript excerpt from the YouTube video: "{title}"
        URL: {url}

        TRANSCRIPT:
        {transcript_text[:4000]}

        Your job:
        1. Identify the single most relevant 2-to-6 minute segment that best teaches "{task_title}".
        2. Estimate realistic MM:SS timestamps based on where the relevant content appears
           in the transcript (assume ~130 words per minute of speech).
        3. Write one sentence explaining why this segment is the most useful.

        Respond ONLY with a valid JSON object — no markdown, no extra text:
        {{
            "start_timestamp": "MM:SS",
            "end_timestamp": "MM:SS",
            "reason": "One sentence explaining why this segment is useful.",
            "transcript_snippet": "A 1-3 sentence excerpt from that segment of the transcript."
        }}
        """

        raw = llm.invoke(prompt).content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)

        print(f"[youtube_segment] Extracted timestamps: "
              f"{data.get('start_timestamp')} → {data.get('end_timestamp')} | {title}")

        return {
            "start_timestamp": data.get("start_timestamp", "00:00"),
            "end_timestamp": data.get("end_timestamp", "05:00"),
            "reason": data.get("reason", DEFAULT["reason"]),
            "transcript_snippet": data.get("transcript_snippet", "")
        }

    except Exception as e:
        print(f"[youtube_segment] Transcript analysis failed for '{title}': {e}")
        return await _llm_estimate_timestamps(title, url, task_title)


async def _llm_estimate_timestamps(title: str, url: str, task_title: str) -> dict:
    """
    Fallback: ask LLM to estimate timestamps without a real transcript.
    """
    prompt = f"""
    You are an expert educator. A student needs to learn: "{task_title}"

    Video title: "{title}"
    URL: {url}

    Estimate the single most relevant 2-to-6 minute segment of this video.

    Respond ONLY with a valid JSON object — no markdown, no extra text:
    {{
        "start_timestamp": "MM:SS",
        "end_timestamp": "MM:SS",
        "reason": "One sentence explaining why this segment is useful.",
        "transcript_snippet": ""
    }}
    """
    try:
        raw = llm.invoke(prompt).content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        return {
            "start_timestamp": data.get("start_timestamp", "00:00"),
            "end_timestamp": data.get("end_timestamp", "05:00"),
            "reason": data.get("reason", "Core section covering the topic."),
            "transcript_snippet": ""
        }
    except Exception as e:
        print(f"[youtube_segment] LLM timestamp estimation also failed: {e}")
        return {
            "start_timestamp": "00:00",
            "end_timestamp": "05:00",
            "reason": "Core section covering the topic.",
            "transcript_snippet": ""
        }


async def resource_node(state: State):

    current_task = state.roadmap[state.current_task_index]
    query = current_task.title

    print(f"\n[resource_node] Current task : {current_task.title}")
    print(f"[resource_node] Task index   : {state.current_task_index + 1}/{len(state.roadmap)}")

    # ── Fetch docs + videos concurrently ──────────────────────────
    try:
        docs_result, videos_result = await asyncio.gather(
            search_docs(query),
            youtube_search(query),
            return_exceptions=True
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

    raw_resources: list[tuple[str, str, str]] = []   # (title, url, type)
    seen: set[str] = set()

    for d in (docs_result or []):
        url = d.get("url", "")
        title = d.get("title", "Untitled")
        if not url or url in seen:
            continue
        seen.add(url)
        raw_resources.append((title, url, "docs"))

    for v in (videos_result or []):
        url = v.get("url", "")
        title = v.get("title", "Untitled")
        if not url or url in seen:
            continue
        seen.add(url)
        raw_resources.append((title, url, "video"))

    # ── Broaden query if we have fewer than 3 ─────────────────────
    if len(raw_resources) < 3:
        print(f"[resource_node] Only {len(raw_resources)} found — broadening query...")
        broader_query = f"{state.topic} {query} tutorial guide"
        try:
            extra = await search_docs(broader_query)
            if isinstance(extra, list):
                for d in extra:
                    url = d.get("url", "")
                    title = d.get("title", "Untitled")
                    if not url or url in seen:
                        continue
                    seen.add(url)
                    raw_resources.append((title, url, "article"))
        except Exception as e:
            print(f"[resource_node] Broader search failed: {e}")

    # ── Score & rank → keep best 5 ────────────────────────────────
    scored = sorted(
        raw_resources,
        key=lambda r: _score_resource(r[1], r[2]),
        reverse=True
    )
    top = scored[:5]

    print(f"[resource_node] Resources collected: {len(top)} "
          f"(from {len(raw_resources)} candidates)")

    # ── Build Resource objects; extract real timestamps for videos ─
    resources: list[Resource] = []
    for title, url, rtype in top:
        base_score = _score_resource(url, rtype)

        if rtype == "video":
            seg = await _extract_video_segment(title, url, current_task.title)
            resource = Resource(
                title=title,
                url=url,
                type="video",
                score=base_score,
                start_timestamp=seg["start_timestamp"],
                end_timestamp=seg["end_timestamp"],
                reason=seg["reason"]
            )
            print(f"  [video] {title} | "
                  f"{seg['start_timestamp']} → {seg['end_timestamp']} | {url}")
        else:
            resource = Resource(
                title=title,
                url=url,
                type=rtype,
                score=base_score
            )
            print(f"  [{rtype}] {title} | {url}")

        resources.append(resource)

    updated = state.roadmap.copy()
    updated[state.current_task_index].resources = resources

    return {"roadmap": updated}


# ============================================================
# FETCH RESOURCE CONTENT NODE  (NEW — Problem 1)
# ============================================================
#
# Sits between resource_node and research_node.
# Fetches real content from every resource URL:
#   • Articles / docs  → HTTP fetch + trafilatura extraction
#   • YouTube videos   → youtube_transcript (already implemented)
#
# Stores results in state.resource_contents so research_node
# can synthesize from real sources instead of LLM knowledge.
# ============================================================

def _fetch_article_content(url: str) -> str:
    """
    Download a web page and extract clean readable text.
    Tries three extraction libraries in order of preference.
    Returns empty string on failure.
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        html = response.text
    except Exception as e:
        print(f"[fetch_resource_content] HTTP fetch failed for {url}: {e}")
        return ""

    # ── 1. trafilatura (best at boilerplate removal) ──────────────
    try:
        import trafilatura
        text = trafilatura.extract(html, include_comments=False, include_tables=False)
        if text and len(text.strip()) > 200:
            return text.strip()[:6000]
    except Exception:
        pass

    # ── 2. newspaper3k ────────────────────────────────────────────
    try:
        from newspaper import Article
        article = Article(url)
        article.set_html(html)
        article.parse()
        if article.text and len(article.text.strip()) > 200:
            return article.text.strip()[:6000]
    except Exception:
        pass

    # ── 3. readability-lxml ───────────────────────────────────────
    try:
        from readability import Document
        doc = Document(html)
        # readability returns HTML; strip tags for plain text
        import re as _re
        text = _re.sub(r"<[^>]+>", " ", doc.summary())
        text = _re.sub(r"\s+", " ", text).strip()
        if len(text) > 200:
            return text[:6000]
    except Exception:
        pass

    print(f"[fetch_resource_content] All extractors failed for {url}")
    return ""


async def fetch_resource_content_node(state: State) -> dict:
    """
    For the current task, fetch real content from every resource.
    Results are stored in state.resource_contents and consumed by
    research_node.
    """
    current_task = state.roadmap[state.current_task_index]
    resources = current_task.resources

    print(f"\n[fetch_resource_content] Current task  : {current_task.title}")
    print(f"[fetch_resource_content] Fetching content for {len(resources)} resource(s)...")

    fetched: list[FetchedContent] = []

    for r in resources:
        content = ""
        try:
            if r.type == "video":
                # ── YouTube transcript ─────────────────────────────
                transcript_data = await youtube_transcript(r.url)
                if transcript_data and transcript_data.get("transcript"):
                    content = transcript_data["transcript"]
                    print(f"[fetch_resource_content] [video] Transcript fetched "
                          f"({len(content)} chars): {r.title}")
                else:
                    print(f"[fetch_resource_content] [video] No transcript: {r.url}")

            else:
                # ── Article / docs — HTTP + extraction ────────────
                # Run synchronous HTTP call in a thread so we don't block the loop
                content = await asyncio.to_thread(_fetch_article_content, r.url)
                if content:
                    print(f"[fetch_resource_content] [{r.type}] Extracted "
                          f"{len(content)} chars: {r.title}")
                else:
                    # Fallback: use Exa highlights stored during search
                    # (search_docs returns a 'highlights' field)
                    print(f"[fetch_resource_content] [{r.type}] "
                          f"HTTP extraction empty — trying Exa highlights...")
                    try:
                        exa_results = await search_docs(r.title)
                        for result in exa_results:
                            if result.get("url") == r.url and result.get("highlights"):
                                hl = result["highlights"]
                                if isinstance(hl, list):
                                    content = "\n".join(hl)
                                elif isinstance(hl, str):
                                    content = hl
                                if content:
                                    print(f"[fetch_resource_content] "
                                          f"Used Exa highlights ({len(content)} chars)")
                                break
                    except Exception as e:
                        print(f"[fetch_resource_content] Exa highlight fallback failed: {e}")

        except Exception as e:
            print(f"[fetch_resource_content] Error fetching {r.url}: {e}")

        if content:
            fetched.append(FetchedContent(
                title=r.title,
                url=r.url,
                type=r.type,
                content=content,
                start_timestamp=r.start_timestamp,
                end_timestamp=r.end_timestamp,
                reason=r.reason
            ))

    print(f"[fetch_resource_content] Extracted {len(fetched)} source(s) "
          f"with usable content (out of {len(resources)} resources)")

    return {"resource_contents": fetched}


# ============================================================
# RESEARCH NODE  (Problem 3)
# ============================================================
#
# NOW uses state.resource_contents (real fetched text) for synthesis.
# Falls back to LLM knowledge only when resource_contents is empty.
# ============================================================

def research_node(state: State):

    current_task = state.roadmap[state.current_task_index]
    resource_contents = state.resource_contents

    print(f"\n[research_node] Current task: {current_task.title}")
    print(f"[research_node] Synthesizing knowledge from "
          f"{len(resource_contents)} document(s)")

    if resource_contents:
        # ── Real RAG: synthesize from fetched content ──────────────
        source_blocks = []
        for i, rc in enumerate(resource_contents, 1):
            block = f"SOURCE {i} — {rc.title} [{rc.type}]\nURL: {rc.url}\n"
            if rc.type == "video" and rc.start_timestamp:
                block += (f"Watch segment: {rc.start_timestamp} → {rc.end_timestamp}\n"
                          f"Why: {rc.reason}\n")
            block += f"\n{rc.content[:2000]}"   # cap per source to stay within context
            source_blocks.append(block)

        combined_sources = "\n\n" + "─" * 60 + "\n\n".join(source_blocks)

        prompt = f"""
        You are an expert educator. Synthesize the key knowledge for a learner.

        Overall subject  : {state.topic}
        Current lesson   : {current_task.title}

        You have been given {len(resource_contents)} real source document(s) below.
        Use ONLY these sources to create your synthesis. Do NOT add information
        that is not present in the sources.

        SOURCES:
        {combined_sources}

        Produce a structured research summary in this exact format:

        SUMMARY:
        <2-3 paragraph overview synthesized from the sources>

        KEY POINTS:
        - <point 1>
        - <point 2>
        - <point 3>
        - <point 4>
        - <point 5 (optional)>
        - <point 6 (optional)>

        EXAMPLES:
        - <concrete example 1 from the sources>
        - <concrete example 2 from the sources>

        SOURCES USED:
        - <title> (<url>)
        """

    else:
        # ── Fallback: LLM intrinsic knowledge ─────────────────────
        print(f"[research_node] No fetched content available — "
              f"falling back to LLM knowledge for '{current_task.title}'")

        prompt = f"""
        You are an expert educator. A learner is studying: {state.topic}
        The current lesson topic is: {current_task.title}

        No external resources are available. Use your knowledge to produce a
        structured research summary.

        SUMMARY:
        <clear overview of this topic>

        KEY POINTS:
        - <4–6 important concepts or facts>

        EXAMPLES:
        - <1–2 concrete, practical examples>
        """

    response = llm.invoke(prompt)

    updated = state.roadmap.copy()
    updated[state.current_task_index].knowledge = response.content

    print(f"[research_node] Knowledge generated ({len(response.content)} chars)")

    return {"roadmap": updated}


# ============================================================
# EXPLAIN NODE
# ============================================================

def explain_node(state: State):

    task = state.roadmap[state.current_task_index]
    print(f"\n[explain_node] Teaching: '{task.title}' "
          f"(task {state.current_task_index + 1}/{len(state.roadmap)})")

    # Surface video segment guidance to the student
    video_resources = [
        r for r in task.resources
        if r.type == "video" and r.start_timestamp
    ]
    video_guidance = ""
    if video_resources:
        lines = ["\n📺  Recommended video segments:"]
        for r in video_resources:
            lines.append(
                f"  • {r.title}\n"
                f"    Watch: {r.start_timestamp} → {r.end_timestamp}\n"
                f"    Why: {r.reason}\n"
                f"    URL: {r.url}"
            )
        video_guidance = "\n".join(lines)

    prompt = f"""
    You are a clear, engaging tutor teaching a learner who is studying: {state.topic}

    Current lesson topic:
    {task.title}

    Research knowledge:
    {task.knowledge}

    Teach this topic step by step. Be concrete and use examples.
    Structure your explanation with clear headings.
    """

    explanation = llm.invoke(prompt)
    lesson_text = explanation.content

    # Append video guidance after the lesson
    if video_guidance:
        lesson_text = lesson_text + "\n\n" + video_guidance

    return {"lesson": lesson_text}


# ============================================================
# QUIZ NODE
# ============================================================

def ask_quiz_permission_node(state):
    print("\nDo you want to take a quiz for this lesson? (yes/no)")
    answer = input("> ").strip().lower()

    if answer in ["yes", "y"]:
        return {"quiz_permission": True}
    else:
        return {"quiz_permission": False}

def quiz_node(state: State):

    task = state.roadmap[state.current_task_index]
    print(f"\n[quiz_node] Generating quiz for: '{task.title}' "
          f"(task {state.current_task_index + 1}/{len(state.roadmap)})")

    prompt = f"""
    You are an expert educator creating a short quiz.

    Topic    : {task.title}
    Knowledge: {task.knowledge}

    Generate exactly 3 quiz questions.
    For each question provide:
    - The question text
    - The correct answer (1–3 concise sentences)

    Respond ONLY with a valid JSON array — no markdown, no extra text:
    [
        {{"question": "...", "correct_answer": "..."}},
        {{"question": "...", "correct_answer": "..."}},
        {{"question": "...", "correct_answer": "..."}}
    ]
    """

    raw = llm.invoke(prompt).content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(raw)
        questions = [
            QuizQuestion(
                question=q["question"],
                correct_answer=q["correct_answer"]
            )
            for q in parsed
        ]
    except Exception as e:
        print(f"[quiz_node] JSON parse failed ({e}), falling back to single question.")
        questions = [
            QuizQuestion(
                question=f"Explain the key concept of {task.title} in your own words.",
                correct_answer="A comprehensive explanation of the topic."
            )
        ]

    lines = [f"Quiz — {task.title}\n"]
    for i, q in enumerate(questions, 1):
        lines.append(f"Q{i}: {q.question}")
    quiz_text = "\n".join(lines)

    print(f"[quiz_node] Generated {len(questions)} question(s).")

    return {
        "quiz_questions": questions,
        "quiz_text": quiz_text,
        "user_answers": [],
        "evaluation_result": None
    }

def quiz_router(state):
    if state["quiz_permission"]:
        return "quiz"
    return "progress"


# ============================================================
# QUIZ HITL — collect user answers
# ============================================================

def quiz_hitl_node(state: State):
    """
    Interrupt the graph so the human can answer each quiz question.
    The test harness collects answers and injects them back into
    state as `user_answers: List[str]`.
    """
    questions = [q.question for q in state.quiz_questions]

    return interrupt(
        {
            "type": "quiz_answer",
            "quiz_text": state.quiz_text,
            "questions": questions,
        }
    )


# ============================================================
# EVALUATE QUIZ NODE
# ============================================================

def evaluate_quiz_node(state: State):
    """
    Compare user_answers against correct_answers.
    Acknowledge correct ones; explain incorrect ones.
    """
    questions = state.quiz_questions
    answers = state.user_answers

    print(f"\n[evaluate_quiz_node] Evaluating {len(questions)} question(s)...")

    if not answers:
        print("[evaluate_quiz_node] No user answers found — skipping evaluation.")
        return {"evaluation_result": "No answers were provided for this quiz."}

    qa_pairs = ""
    for i, q in enumerate(questions):
        user_ans = answers[i] if i < len(answers) else "(no answer)"
        qa_pairs += (
            f"\nQ{i + 1}: {q.question}\n"
            f"Correct answer : {q.correct_answer}\n"
            f"Student answer : {user_ans}\n"
        )

    prompt = f"""
    You are a strict but encouraging tutor evaluating a student's quiz answers.

    Topic: {state.roadmap[state.current_task_index].title}

    {qa_pairs}

    For EACH question:
    1. State whether the student's answer is CORRECT or INCORRECT.
    2. If INCORRECT, explain the correct answer clearly in 2–3 sentences.
    3. If CORRECT, acknowledge it warmly in one sentence.

    End your evaluation with:
    SCORE: X/{len(questions)}

    Keep the tone encouraging but honest.
    """

    response = llm.invoke(prompt)
    evaluation = response.content

    score_line = [l for l in evaluation.splitlines() if l.strip().startswith("SCORE:")]
    score_str = score_line[-1].replace("SCORE:", "").strip() if score_line else "?/?"
    print(f"[evaluate_quiz_node] Quiz score: {score_str}")

    return {"evaluation_result": evaluation}


# ============================================================
# PROGRESS NODE
# ============================================================

def progress_node(state: State):

    next_index = state.current_task_index + 1
    total = len(state.roadmap)

    print(f"\n[progress_node] Current task: {state.roadmap[state.current_task_index].title}")
    print(f"[progress_node] Completed task {state.current_task_index + 1}/{total}.")

    if next_index < total:
        print(f"[progress_node] Moving to task {next_index + 1}: "
              f"'{state.roadmap[next_index].title}'")
        return {
            "current_task_index": next_index,
            "resource_contents": []          # clear for next task
        }

    print(f"[progress_node] All {total} tasks complete! 🎉")
    return {"finished": True}


# ============================================================
# ROUTERS
# ============================================================

def roadmap_router(state: State):
    action = state.user_action["action"]
    if action == "confirm":
        return "resource"
    return "apply_edit"


def progress_router(state: State):
    if state.finished:
        return "end"
    return "resource"
