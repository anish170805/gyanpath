"""
backend/agent/runner.py

Thin async wrappers around the compiled LangGraph graph.

The graph already lives at the repo root (graph.py / nodes.py / states.py).
We import it directly — no duplication.

Key design decisions
────────────────────
• The graph uses LangGraph's interrupt() for every HITL step.
  When the graph hits an interrupt, astream() yields a special
  "__interrupt__" event.  We catch it, surface the payload to the
  route handler, and pause.  The route handler then injects the
  user's response via graph.aupdate_state() and calls
  resume_until_interrupt() to continue.

• We never "run the whole graph in one shot" for a single HTTP
  request because the graph is designed to pause multiple times
  per task (quiz_permission, quiz_answer, challenge_prompt).
  Routes drive the graph step by step.

• The session's LangGraph thread_id == session_id so the
  InMemorySaver checkpointer keeps all state between requests.

• resume_capturing_nodes() additionally tracks per-node output dicts
  as they stream in.  This lets the /challenge route read the project
  text directly from project_node's output — before progress_node
  can overwrite it in the shared state.
"""

from __future__ import annotations

import sys
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

# ── make sure the repo root is on the path ──────────────────
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from graph import graph          # the compiled LangGraph graph
from states import State         # pydantic State model


@dataclass
class AgentInterrupt:
    """
    Returned by run_until_interrupt / resume_until_interrupt when the
    graph pauses at a HITL node.

    interrupt_type: one of
        "roadmap_review" | "quiz_permission" | "quiz_answer" |
        "challenge_prompt"
    payload: the dict passed to interrupt() inside the node
    """
    interrupt_type: str
    payload: Dict[str, Any]
    state: Dict[str, Any]


@dataclass
class StreamResult:
    """
    Full result of a single graph stream run.

    interrupt    : the interrupt that paused the graph (None = ran to end)
    final_state  : graph state at pause / completion
    node_outputs : node_name → raw output dict emitted by that node.
                   Populated only by resume_capturing_nodes(); empty otherwise.
    """
    interrupt:    Optional[AgentInterrupt]
    final_state:  Dict[str, Any]
    node_outputs: Dict[str, Any] = field(default_factory=dict)


def _langgraph_config(session_id: str) -> dict:
    return {"configurable": {"thread_id": session_id}}


async def _stream(
    input_value,
    session_id: str,
    capture_nodes: bool = False,
) -> StreamResult:
    """
    Drive the graph forward until it either pauses (interrupt) or ends.

    If capture_nodes=True, records every node's raw output in
    StreamResult.node_outputs so callers can read values that later nodes
    overwrite (e.g. project_node sets project, progress_node clears it).
    """
    config = _langgraph_config(session_id)
    node_outputs: Dict[str, Any] = {}

    async for event in graph.astream(input_value, config=config):
        for node_name, output in event.items():

            if node_name == "__interrupt__":
                payload    = output[0].value
                itype      = payload.get("type", "unknown")
                snapshot   = await graph.aget_state(config)
                state_dict = dict(snapshot.values)
                print(f"[runner] ⏸  interrupt: {itype}")
                return StreamResult(
                    interrupt=AgentInterrupt(
                        interrupt_type=itype,
                        payload=payload,
                        state=state_dict,
                    ),
                    final_state=state_dict,
                    node_outputs=node_outputs,
                )

            # Record node output when requested
            if capture_nodes and isinstance(output, dict):
                node_outputs[node_name] = output
                print(f"[runner] ▶ {node_name}: keys={list(output.keys())}")
            else:
                print(f"[runner] ▶ {node_name}")

    # Graph ran to completion
    snapshot   = await graph.aget_state(config)
    state_dict = dict(snapshot.values)
    print("[runner] ✅ graph completed (no interrupt)")
    return StreamResult(
        interrupt=None,
        final_state=state_dict,
        node_outputs=node_outputs,
    )


# ── Public helpers ────────────────────────────────────────────────────────────

async def run_until_interrupt(
    initial_state: State,
    session_id: str,
) -> tuple[Optional[AgentInterrupt], Dict[str, Any]]:
    """Start a brand-new graph run.  Returns (interrupt_or_None, state)."""
    result = await _stream(initial_state, session_id)
    return result.interrupt, result.final_state


async def resume_until_interrupt(
    session_id: str,
) -> tuple[Optional[AgentInterrupt], Dict[str, Any]]:
    """Resume from checkpoint.  Returns (interrupt_or_None, state)."""
    result = await _stream(None, session_id)
    return result.interrupt, result.final_state


async def resume_capturing_nodes(
    session_id: str,
) -> StreamResult:
    """
    Like resume_until_interrupt but returns the full StreamResult,
    including per-node output snapshots captured as each node fires.

    Use this when a later node in the same stream may overwrite a value
    you need (e.g. project_node sets state.project, then progress_node
    clears it — but node_outputs["project"] still has the original dict).
    """
    return await _stream(None, session_id, capture_nodes=True)


async def inject_state(session_id: str, updates: Dict[str, Any], as_node: str) -> None:
    """
    Inject user-supplied values into the graph's checkpoint and mark
    the graph as resuming from `as_node`.
    """
    config = _langgraph_config(session_id)
    await graph.aupdate_state(config, updates, as_node=as_node)