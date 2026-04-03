from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from states import State
from nodes import (
    ask_quiz_permission_node,
    quiz_router,
    quiz_router,
    roadmap_node,
    roadmap_review_node,
    apply_roadmap_edit_node,
    resource_node,
    fetch_resource_content_node,    # NEW — real content fetching
    research_node,
    explain_node,
    quiz_node,
    quiz_hitl_node,
    evaluate_quiz_node,
    progress_node,
    roadmap_router,
    progress_router,
)

builder = StateGraph(State)

# ── Nodes ────────────────────────────────────────────────────────────────────
builder.add_node("roadmap",               roadmap_node)
builder.add_node("review",                roadmap_review_node)
builder.add_node("apply_edit",            apply_roadmap_edit_node)

builder.add_node("resource",              resource_node)
builder.add_node("fetch_resource_content", fetch_resource_content_node)  # NEW
builder.add_node("research",              research_node)
builder.add_node("explain",               explain_node)

builder.add_node("ask_quiz_permission", ask_quiz_permission_node)
builder.add_node("quiz",                  quiz_node)
builder.add_node("quiz_hitl",             quiz_hitl_node)
builder.add_node("evaluate_quiz",         evaluate_quiz_node)

builder.add_node("progress",              progress_node)

# ── Edges: start ─────────────────────────────────────────────────────────────
builder.add_edge(START, "roadmap")

# ── Edges: roadmap HITL loop ─────────────────────────────────────────────────
builder.add_edge("roadmap",    "review")
builder.add_edge("apply_edit", "review")

builder.add_conditional_edges(
    "review",
    roadmap_router,
    {
        "resource":   "resource",
        "apply_edit": "apply_edit",
    }
)

# ── Edges: learning pipeline ─────────────────────────────────────────────────
#
#   resource → fetch_resource_content → research → explain
#
builder.add_edge("resource",               "fetch_resource_content")   # NEW
builder.add_edge("fetch_resource_content", "research")                 # NEW
builder.add_edge("research",               "explain")
builder.add_edge("explain",                "ask_quiz_permission")

# Quiz: generate → HITL collect → evaluate → progress
builder.add_conditional_edges(
    "ask_quiz_permission",
    quiz_router,
    {
        "quiz": "quiz",
        "progress": "progress"
    }
)
builder.add_edge("quiz",          "quiz_hitl")
builder.add_edge("quiz_hitl",     "evaluate_quiz")
builder.add_edge("evaluate_quiz", "progress")

# ── Edges: progress loop or end ──────────────────────────────────────────────
builder.add_conditional_edges(
    "progress",
    progress_router,
    {
        "resource": "resource",
        "end":      END,
    }
)

memory = InMemorySaver()
graph = builder.compile(checkpointer=memory)
