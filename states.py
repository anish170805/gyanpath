from pydantic import BaseModel
from typing import List, Optional, Dict


class Resource(BaseModel):
    """
    Represents a single learning resource for a task.

    For video resources, start_timestamp, end_timestamp, and reason
    describe the exact segment most relevant to the current task.
    """

    title: str                              # Human-readable title
    url: str
    type: str                               # "article" | "video" | "docs"
    score: float = 0.8                      # Internal quality score used for ranking

    # Video-only fields (None for articles / docs)
    start_timestamp: Optional[str] = None   # e.g. "03:20"
    end_timestamp: Optional[str] = None     # e.g. "08:45"
    reason: Optional[str] = None            # Why this segment is relevant


class FetchedContent(BaseModel):
    """
    Holds the clean extracted text fetched from a single resource URL.
    Stored in State.resource_contents after fetch_resource_content runs.
    """
    title: str
    url: str
    type: str                               # mirrors Resource.type
    content: str                            # clean extracted text / transcript
    start_timestamp: Optional[str] = None
    end_timestamp: Optional[str] = None
    reason: Optional[str] = None


class Task(BaseModel):
    title: str
    resources: List[Resource] = []
    knowledge: Optional[str] = None


class Roadmap(BaseModel):
    tasks: List[str]


class QuizQuestion(BaseModel):
    """A single quiz question with its correct answer."""
    question: str
    correct_answer: str


class State(BaseModel):
    topic: str
    roadmap: List[Task] = []
    current_task_index: int = 0
    lesson: Optional[str] = None

    # Fetched source content — populated by fetch_resource_content, consumed by research_node
    resource_contents: List[FetchedContent] = []

    # Quiz permission — set by ask_quiz_permission HITL, read by quiz_permission_router
    quiz_permission: Optional[bool] = None

    # Quiz state
    quiz_questions: List[QuizQuestion] = []
    quiz_text: Optional[str] = None
    user_answers: List[str] = []
    evaluation_result: Optional[str] = None

    # Project challenge state
    # True  → user accepted the challenge; project_node will run
    # False → user declined; go straight to progress
    # None  → not yet asked (reset each task)
    challenge_accepted: Optional[bool] = None
    project: Optional[str] = None          # generated project brief

    finished: bool = False
    user_action: dict | None = None
