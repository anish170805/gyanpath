from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from backend.agent.states import State
from backend.agent.nodes import (
    roadmap_node,
    roadmap_review_node,
    apply_roadmap_edit_node,
    resource_node,
    fetch_resource_content_node,
    research_node,
    explain_node,
    ask_quiz_permission_node,
    quiz_permission_router,
    quiz_node,
    quiz_hitl_node,
    evaluate_quiz_node,
    ask_challenge_node,         # NEW
    challenge_router,           # NEW
    project_node,               # NEW
    progress_node,
    roadmap_router,
    progress_router,
)

builder = StateGraph(State)

# ── Nodes ─────────────────────────────────────────────────────────────────────
builder.add_node("roadmap",                roadmap_node)
builder.add_node("review",                 roadmap_review_node)
builder.add_node("apply_edit",             apply_roadmap_edit_node)

builder.add_node("resource",               resource_node)
builder.add_node("fetch_resource_content", fetch_resource_content_node)
builder.add_node("research",               research_node)
builder.add_node("explain",                explain_node)

builder.add_node("ask_quiz_permission",    ask_quiz_permission_node)
builder.add_node("quiz",                   quiz_node)
builder.add_node("quiz_hitl",              quiz_hitl_node)
builder.add_node("evaluate_quiz",          evaluate_quiz_node)

builder.add_node("ask_challenge",          ask_challenge_node)   # NEW
builder.add_node("project",                project_node)         # NEW

builder.add_node("progress",               progress_node)

# ── Edges: start ──────────────────────────────────────────────────────────────
builder.add_edge(START, "roadmap")

# ── Edges: roadmap HITL loop ──────────────────────────────────────────────────
builder.add_edge("roadmap",    "review")
builder.add_edge("apply_edit", "review")

builder.add_conditional_edges(
    "review",
    roadmap_router,
    {"resource": "resource", "apply_edit": "apply_edit"},
)

# ── Edges: resource pipeline ───────────────────────────────────────────────────
#
#   resource → fetch_resource_content → research → explain
#
builder.add_edge("resource",               "fetch_resource_content")
builder.add_edge("fetch_resource_content", "research")
builder.add_edge("research",               "explain")

# ── Edges: quiz permission gate ────────────────────────────────────────────────
#
#   explain → ask_quiz_permission ─┬─(yes)→ quiz → quiz_hitl → evaluate_quiz
#                                   └─(no) ──────────────────────────────────┐
#                                                                             ↓
#                                                                      ask_challenge
#
builder.add_edge("explain", "ask_quiz_permission")

builder.add_conditional_edges(
    "ask_quiz_permission",
    quiz_permission_router,
    {"quiz": "quiz", "progress": "ask_challenge"},
    #                              ↑
    # When user skips the quiz, go straight to the challenge prompt
    # (still gives them a project opportunity even without the quiz).
)

builder.add_edge("quiz",      "quiz_hitl")
builder.add_edge("quiz_hitl", "evaluate_quiz")

# ── Edges: challenge gate (NEW) ────────────────────────────────────────────────
#
#   evaluate_quiz → ask_challenge ─┬─(yes)→ project → progress
#                                   └─(no) ──────────→ progress
#
builder.add_edge("evaluate_quiz", "ask_challenge")

builder.add_conditional_edges(
    "ask_challenge",
    challenge_router,
    {"project": "project", "progress": "progress"},
)

builder.add_edge("project", "progress")

# ── Edges: progress loop or end ───────────────────────────────────────────────
builder.add_conditional_edges(
    "progress",
    progress_router,
    {"resource": "resource", "end": END},
)

memory = InMemorySaver()
graph = builder.compile(checkpointer=memory)
