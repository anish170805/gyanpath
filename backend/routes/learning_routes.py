"""
backend/routes/learning_routes.py

All HTTP endpoints for the GyanPath learning agent.

Flow overview (matches the LangGraph graph exactly)
─────────────────────────────────────────────────────
POST /start
  → graph starts → hits "roadmap_review" interrupt
  → returns roadmap to frontend for user to confirm/edit

POST /roadmap/edit   (loop: add / delete / edit / confirm)
  → on "confirm" → graph continues → runs resource + research + explain
  → hits "quiz_permission" interrupt
  → returns lesson + resources

POST /quiz/start     (user said "yes" to quiz_permission)
  → inject quiz_permission=True → graph generates quiz questions
  → hits "quiz_answer" interrupt
  → returns questions

POST /quiz/submit
  → inject answers → graph evaluates → hits "challenge_prompt" interrupt
  → returns score + feedback

POST /challenge
  → inject accepted=True/False → graph runs project_node if accepted
  → graph calls progress_node → either loops back (next task) or finishes
  → returns project brief (if accepted) + next_action

POST /next           (user skipped the quiz — quiz_permission=False)
  → inject quiz_permission=False → graph skips quiz → hits challenge_prompt
  → same as above but without quiz score

GET  /resources/{session_id}
  → reads current task resources from session state → returns them

GET  /session/{session_id}
  → returns lightweight status (phase, progress, roadmap)
"""

from __future__ import annotations

import re
import sys
import os
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

# ── path setup ──────────────────────────────────────────────
_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_ROOT    = os.path.abspath(os.path.join(_BACKEND, ".."))
for p in (_BACKEND, _ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from models.schemas import (
    StartRequest, StartResponse,
    RoadmapEditRequest, RoadmapEditResponse,
    NextRequest, NextResponse,
    QuizStartRequest, QuizStartResponse,
    QuizSubmitRequest, QuizSubmitResponse,
    ChallengeRequest, ChallengeResponse,
    ResourcesResponse,
    SessionStatusResponse,
    ResourceSchema, QuizQuestionSchema,
)
from agent.runner import run_until_interrupt, resume_until_interrupt, resume_capturing_nodes, inject_state, AgentInterrupt
from agent.session_store import (
    create_session, get_session, update_state,
    set_phase, get_phase, session_exists, delete_session,
)
from states import State

router = APIRouter()


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def _require_session(session_id: str) -> Dict[str, Any]:
    entry = get_session(session_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return entry


def _resources_from_state(state: Dict[str, Any]) -> List[ResourceSchema]:
    """Extract resource list for the current task from the state dict."""
    roadmap = state.get("roadmap", [])
    idx     = state.get("current_task_index", 0)
    if not roadmap or idx >= len(roadmap):
        print(f"[debug] _resources_from_state: Roadmap empty or index {idx} out of range")
        return []
    
    task = roadmap[idx]
    # task may be a dict (from LangGraph serialisation) or a Task object
    try:
        resources = task.get("resources", []) if isinstance(task, dict) else getattr(task, "resources", [])
    except Exception as e:
        print(f"[debug] _resources_from_state error: {e}")
        resources = []

    print(f"[debug] _resources_from_state: Extracted {len(resources)} resources for task index {idx}")
    
    result = []
    for r in resources:
        try:
            d = r if isinstance(r, dict) else r.dict()
            result.append(ResourceSchema(**{k: d.get(k) for k in ResourceSchema.model_fields}))
        except Exception as e:
            print(f"[debug] _resources_from_state: failed to parse resource {r}: {e}")
    return result


def _current_task_title(state: Dict[str, Any]) -> str:
    roadmap = state.get("roadmap", [])
    idx     = state.get("current_task_index", 0)
    if not roadmap or idx >= len(roadmap):
        return ""
    task = roadmap[idx]
    return task.get("title", "") if isinstance(task, dict) else task.title


def _roadmap_titles(state: Dict[str, Any]) -> List[str]:
    roadmap = state.get("roadmap", [])
    return [
        (t.get("title", "") if isinstance(t, dict) else t.title)
        for t in roadmap
    ]


def _progress_pct(state: Dict[str, Any]) -> int:
    if state.get("finished"):
        return 100
    total = len(state.get("roadmap", []))
    if total == 0:
        return 0
    idx = state.get("current_task_index", 0)
    return min(100, round(idx / total * 100))


def _extract_score(evaluation: str) -> int:
    """Parse 'SCORE: 2/3' → 2.  Returns 0 on failure."""
    m = re.search(r"SCORE:\s*(\d+)/\d+", evaluation or "")
    return int(m.group(1)) if m else 0


def _next_action_from_state(state: Dict[str, Any]) -> str:
    if state.get("finished"):
        return "finished"
    return "challenge"


# ══════════════════════════════════════════════════════════════
# POST /start
# ══════════════════════════════════════════════════════════════

@router.post("/start", response_model=StartResponse, summary="Start a new learning session")
async def start_session(body: StartRequest) -> StartResponse:
    """
    Kick off a new session for the given topic.

    The graph runs until it hits the first interrupt (roadmap_review).
    We then continue past it automatically by confirming the roadmap so
    the frontend receives the first full lesson right away.

    Full interaction sequence driven by this single endpoint:
      roadmap_node → roadmap_review interrupt
        → auto-confirm → resource → fetch → research → explain
        → quiz_permission interrupt  (we stop here and return)
    """
    session_id = str(uuid.uuid4())
    initial    = State(topic=body.topic)

    # ── Phase 1: run until roadmap_review interrupt ───────────
    interrupt, state = await run_until_interrupt(initial, session_id)

    if not interrupt or interrupt.interrupt_type != "roadmap_review":
        raise HTTPException(500, "Expected roadmap_review interrupt; got something else.")

    # ── Phase 2: Wait for user confirmation (HITL) ────────────
    # The frontend is expected to show the roadmap and optionally call /roadmap/edit
    
    lesson    = ""
    resources = []
    roadmap   = _roadmap_titles(state)
    task      = _current_task_title(state)
    idx       = state.get("current_task_index", 0)

    create_session(session_id, state)
    set_phase(session_id, "roadmap")

    return StartResponse(
        session_id=session_id,
        topic=body.topic,
        roadmap=roadmap,
        current_task=task,
        current_task_index=idx,
        total_tasks=len(roadmap),
        lesson=lesson,
        resources=resources,
        progress_pct=_progress_pct(state),
    )


# ══════════════════════════════════════════════════════════════
# POST /roadmap/edit
# ══════════════════════════════════════════════════════════════

@router.post("/roadmap/edit", response_model=RoadmapEditResponse,
             summary="Add / delete / edit / confirm roadmap tasks")
async def edit_roadmap(body: RoadmapEditRequest) -> RoadmapEditResponse:
    """
    Lets the user tweak the AI-generated roadmap before learning begins.
    Call with action='confirm' to lock in the roadmap and proceed.
    """
    _require_session(body.session_id)

    user_action: Dict[str, Any] = {"action": body.action}
    if body.action in ("add", "edit"):
        if not body.task:
            raise HTTPException(422, "'task' is required for add/edit.")
        user_action["task"] = body.task
    if body.action in ("delete", "edit"):
        if body.index is None:
            raise HTTPException(422, "'index' is required for delete/edit.")
        user_action["index"] = body.index

    await inject_state(body.session_id, {"user_action": user_action}, as_node="review")
    interrupt, state = await resume_until_interrupt(body.session_id)
    update_state(body.session_id, state)

    if body.action == "confirm":
        set_phase(body.session_id, "lesson")
        return RoadmapEditResponse(
            session_id=body.session_id,
            roadmap=_roadmap_titles(state),
            confirmed=True,
            current_task=_current_task_title(state),
            current_task_index=state.get("current_task_index", 0),
            total_tasks=len(_roadmap_titles(state)),
            lesson=state.get("lesson", ""),
            resources=_resources_from_state(state),
            progress_pct=_progress_pct(state),
        )

    return RoadmapEditResponse(
        session_id=body.session_id,
        roadmap=_roadmap_titles(state),
        confirmed=False,
    )


# ══════════════════════════════════════════════════════════════
# POST /next   — skip quiz, move to next lesson
# ══════════════════════════════════════════════════════════════

@router.post("/next", response_model=NextResponse, summary="Skip quiz and advance to next lesson")
async def next_lesson(body: NextRequest) -> NextResponse:
    """
    Called when the user declines the quiz (or after challenge is resolved
    and the frontend wants to explicitly load the next task).

    Injects quiz_permission=False so the graph skips quiz → challenge →
    progress → resource → … → explain → quiz_permission interrupt (next task).
    """
    _require_session(body.session_id)

    # Decline quiz
    await inject_state(body.session_id,
                       {"quiz_permission": False},
                       as_node="ask_quiz_permission")

    # Graph will hit challenge_prompt interrupt
    interrupt, state = await resume_until_interrupt(body.session_id)
    update_state(body.session_id, state)

    if interrupt and interrupt.interrupt_type == "challenge_prompt":
        # Auto-decline challenge so we proceed to progress → next lesson
        await inject_state(body.session_id,
                           {"challenge_accepted": False},
                           as_node="ask_challenge")
        interrupt, state = await resume_until_interrupt(body.session_id)
        update_state(body.session_id, state)

    finished = state.get("finished", False)
    set_phase(body.session_id, "done" if finished else "lesson")

    return NextResponse(
        session_id=body.session_id,
        current_task=_current_task_title(state),
        current_task_index=state.get("current_task_index", 0),
        total_tasks=len(_roadmap_titles(state)),
        lesson=state.get("lesson", ""),
        resources=_resources_from_state(state),
        progress_pct=_progress_pct(state),
        finished=finished,
    )


# ══════════════════════════════════════════════════════════════
# POST /quiz/start
# ══════════════════════════════════════════════════════════════

@router.post("/quiz/start", response_model=QuizStartResponse, summary="Start quiz for current lesson")
async def start_quiz(body: QuizStartRequest) -> QuizStartResponse:
    """
    Called when the user accepts the quiz prompt.

    Injects quiz_permission=True → graph runs quiz_node → hits quiz_answer interrupt.
    Returns the questions (without correct answers).
    """
    _require_session(body.session_id)

    await inject_state(body.session_id,
                       {"quiz_permission": True},
                       as_node="ask_quiz_permission")

    interrupt, state = await resume_until_interrupt(body.session_id)
    update_state(body.session_id, state)

    if not interrupt or interrupt.interrupt_type != "quiz_answer":
        raise HTTPException(500, "Expected quiz_answer interrupt after starting quiz.")

    set_phase(body.session_id, "quiz")

    raw_questions = state.get("quiz_questions", [])
    questions = [
        QuizQuestionSchema(
            question=q.get("question", "") if isinstance(q, dict) else q.question
        )
        for q in raw_questions
    ]

    return QuizStartResponse(
        session_id=body.session_id,
        task_title=_current_task_title(state),
        questions=questions,
        quiz_text=state.get("quiz_text", ""),
    )


# ══════════════════════════════════════════════════════════════
# POST /quiz/submit
# ══════════════════════════════════════════════════════════════

@router.post("/quiz/submit", response_model=QuizSubmitResponse, summary="Submit quiz answers")
async def submit_quiz(body: QuizSubmitRequest) -> QuizSubmitResponse:
    """
    Accepts the user's answers, runs evaluate_quiz_node, then pauses
    at the challenge_prompt interrupt.

    Returns score + per-question feedback.
    next_action tells the frontend what to show next:
      "challenge"    → show "Ready for a challenge?" UI
      "next_lesson"  → no challenge available, just continue
      "finished"     → entire roadmap is done
    """
    entry = _require_session(body.session_id)

    await inject_state(body.session_id,
                       {"user_answers": body.answers},
                       as_node="quiz_hitl")

    interrupt, state = await resume_until_interrupt(body.session_id)
    update_state(body.session_id, state)

    evaluation = state.get("evaluation_result", "")
    score      = _extract_score(evaluation)
    total      = len(state.get("quiz_questions", []))

    if interrupt and interrupt.interrupt_type == "challenge_prompt":
        set_phase(body.session_id, "challenge")
        next_action = "challenge"
    elif state.get("finished"):
        set_phase(body.session_id, "done")
        next_action = "finished"
    else:
        next_action = "next_lesson"

    return QuizSubmitResponse(
        session_id=body.session_id,
        score=score,
        total=total,
        feedback=evaluation,
        next_action=next_action,
    )


# ══════════════════════════════════════════════════════════════
# POST /challenge
# ══════════════════════════════════════════════════════════════

@router.post("/challenge", response_model=ChallengeResponse, summary="Accept or decline project challenge")
async def handle_challenge(body: ChallengeRequest) -> ChallengeResponse:
    """
    Called after /quiz/submit returns next_action='challenge'.

    If accepted=True:  graph runs project_node → progress_node.
    If accepted=False: graph runs progress_node directly.

    After progress_node:
      • if more tasks remain  → graph loops back → resource → … → explain
        → quiz_permission interrupt  (frontend polls /session for new state)
      • if finished           → graph ends
    """
    _require_session(body.session_id)

    await inject_state(body.session_id,
                       {"challenge_accepted": body.accepted},
                       as_node="ask_challenge")

    # Use resume_capturing_nodes so we can read project_node's output
    # directly from node_outputs — before progress_node overwrites it.
    stream = await resume_capturing_nodes(body.session_id)
    state  = stream.final_state
    update_state(body.session_id, state)

    # Pull project text from project_node's own output dict (guaranteed
    # to exist even after progress_node clears state.project).
    project_text: Optional[str] = None
    if body.accepted:
        project_node_out = stream.node_outputs.get("project")
        if project_node_out:
            project_text = project_node_out.get("project")
            print(f"[challenge] project captured from node_outputs: {bool(project_text)} "
                  f"({len(project_text) if project_text else 0} chars)")
        else:
            # Fallback: try final state (works if progress_node didn't run yet)
            project_text = state.get("project")
            print(f"[challenge] project from final state: {bool(project_text)}")

    finished = state.get("finished", False)

    set_phase(body.session_id, "done" if finished else "lesson")

    return ChallengeResponse(
        session_id=body.session_id,
        accepted=body.accepted,
        project=project_text,
        finished=finished,
        current_task=_current_task_title(state),
        current_task_index=state.get("current_task_index", 0),
        total_tasks=len(_roadmap_titles(state)),
        lesson=state.get("lesson", "") if not finished else None,
        resources=_resources_from_state(state) if not finished else None,
        progress_pct=_progress_pct(state),
    )


# ══════════════════════════════════════════════════════════════
# GET /resources/{session_id}
# ══════════════════════════════════════════════════════════════

@router.get("/resources/{session_id}", response_model=ResourcesResponse,
            summary="Return resources for the current lesson")
async def get_resources(session_id: str) -> ResourcesResponse:
    entry = _require_session(session_id)
    state = entry["state"]
    return ResourcesResponse(
        session_id=session_id,
        task_title=_current_task_title(state),
        resources=_resources_from_state(state),
    )


# ══════════════════════════════════════════════════════════════
# GET /session/{session_id}
# ══════════════════════════════════════════════════════════════

@router.get("/session/{session_id}", response_model=SessionStatusResponse,
            summary="Get current session status")
async def get_session_status(session_id: str) -> SessionStatusResponse:
    entry = _require_session(session_id)
    state = entry["state"]
    phase = entry.get("phase", "lesson")
    roadmap = _roadmap_titles(state)
    return SessionStatusResponse(
        session_id=session_id,
        topic=state.get("topic", ""),
        current_task_index=state.get("current_task_index", 0),
        total_tasks=len(roadmap),
        roadmap=roadmap,
        progress_pct=_progress_pct(state),
        finished=state.get("finished", False),
        phase=phase,
    )
