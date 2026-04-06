"""
Pydantic request / response schemas for the GyanPath API.

All models are strict — extra fields are forbidden so the frontend
cannot accidentally pass unknown keys that silently get ignored.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────────
# Shared sub-models
# ──────────────────────────────────────────────────────────────

class ResourceSchema(BaseModel):
    """One learning resource as returned to the frontend."""
    title: str
    url: str
    type: str                               # "docs" | "video" | "article"
    start_timestamp: Optional[str] = None
    end_timestamp: Optional[str] = None
    reason: Optional[str] = None


class QuizQuestionSchema(BaseModel):
    """A single quiz question (correct_answer is never sent to the frontend)."""
    question: str


class RoadmapTaskSchema(BaseModel):
    """Lightweight task summary shown in the sidebar / roadmap view."""
    title: str
    index: int


# ──────────────────────────────────────────────────────────────
# POST /start
# ──────────────────────────────────────────────────────────────

class StartRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200,
                       description="The subject the learner wants to study.")


class StartResponse(BaseModel):
    session_id: str
    topic: str
    roadmap: List[str]                      # ordered list of task titles
    current_task: str
    current_task_index: int
    total_tasks: int
    lesson: Optional[str] = None
    resources: Optional[List[ResourceSchema]] = None
    progress_pct: int                       # 0-100


# ──────────────────────────────────────────────────────────────
# POST /roadmap/edit
# ──────────────────────────────────────────────────────────────

class RoadmapEditRequest(BaseModel):
    session_id: str
    action: Literal["add", "delete", "edit", "confirm"]
    task: Optional[str] = None             # required for "add" / "edit"
    index: Optional[int] = None            # required for "delete" / "edit"


class RoadmapEditResponse(BaseModel):
    session_id: str
    roadmap: List[str]
    confirmed: bool                        # True when action == "confirm"
    current_task: Optional[str] = None
    current_task_index: Optional[int] = None
    total_tasks: Optional[int] = None
    lesson: Optional[str] = None
    resources: Optional[List[ResourceSchema]] = None
    progress_pct: Optional[int] = None


# ──────────────────────────────────────────────────────────────
# POST /next
# ──────────────────────────────────────────────────────────────

class NextRequest(BaseModel):
    session_id: str


class NextResponse(BaseModel):
    session_id: str
    current_task: str
    current_task_index: int
    total_tasks: int
    lesson: str
    resources: List[ResourceSchema]
    progress_pct: int
    finished: bool


# ──────────────────────────────────────────────────────────────
# POST /quiz/start
# ──────────────────────────────────────────────────────────────

class QuizStartRequest(BaseModel):
    session_id: str


class QuizStartResponse(BaseModel):
    session_id: str
    task_title: str
    questions: List[QuizQuestionSchema]     # correct_answer intentionally omitted
    quiz_text: str


# ──────────────────────────────────────────────────────────────
# POST /quiz/submit
# ──────────────────────────────────────────────────────────────

class QuizSubmitRequest(BaseModel):
    session_id: str
    answers: List[str] = Field(..., min_length=1,
                               description="One answer string per question, in order.")


class QuizSubmitResponse(BaseModel):
    session_id: str
    score: int                              # number of correct answers
    total: int
    feedback: str                           # per-question evaluation text from LLM
    next_action: Literal["challenge", "next_lesson", "finished"]


# ──────────────────────────────────────────────────────────────
# POST /challenge
# ──────────────────────────────────────────────────────────────

class ChallengeRequest(BaseModel):
    session_id: str
    accepted: bool


class ChallengeResponse(BaseModel):
    session_id: str
    accepted: bool
    project: Optional[str] = None          # full project brief (if accepted)
    # Next lesson data — the graph has already run the next task pipeline
    # inside the /challenge call, so we return it here to avoid a redundant
    # /next call from the frontend.
    finished: bool = False
    current_task: Optional[str] = None
    current_task_index: Optional[int] = None
    total_tasks: Optional[int] = None
    lesson: Optional[str] = None
    resources: Optional[List[ResourceSchema]] = None
    progress_pct: Optional[int] = None


# ──────────────────────────────────────────────────────────────
# GET /resources
# ──────────────────────────────────────────────────────────────

class ResourcesResponse(BaseModel):
    session_id: str
    task_title: str
    resources: List[ResourceSchema]


# ──────────────────────────────────────────────────────────────
# GET /session/{session_id}
# ──────────────────────────────────────────────────────────────

class SessionStatusResponse(BaseModel):
    session_id: str
    topic: str
    current_task_index: int
    total_tasks: int
    roadmap: List[str]
    progress_pct: int
    finished: bool
    phase: str                             # "lesson" | "quiz" | "challenge" | "done"
