"""
backend/agent/session_store.py

In-memory session registry.

Stores two things per session_id:
  • "state"  : last known graph-state dict (refreshed after every agent step)
  • "phase"  : which part of the flow we're currently waiting on
               "lesson" | "quiz" | "challenge" | "done"

Thread-safety: FastAPI runs in a single async event loop by default
(uvicorn with one worker), so a plain dict is safe.  For multi-worker
deployments swap this for Redis.
"""

from __future__ import annotations

from typing import Any, Dict, Literal, Optional

Phase = Literal["lesson", "quiz", "challenge", "done"]

# session_id → {"state": dict, "phase": Phase}
_store: Dict[str, Dict[str, Any]] = {}


def create_session(session_id: str, state: Dict[str, Any]) -> None:
    _store[session_id] = {"state": state, "phase": "lesson"}


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    return _store.get(session_id)


def update_state(session_id: str, state: Dict[str, Any]) -> None:
    if session_id in _store:
        _store[session_id]["state"] = state


def set_phase(session_id: str, phase: Phase) -> None:
    if session_id in _store:
        _store[session_id]["phase"] = phase


def get_phase(session_id: str) -> Optional[Phase]:
    entry = _store.get(session_id)
    return entry["phase"] if entry else None


def delete_session(session_id: str) -> None:
    _store.pop(session_id, None)


def session_exists(session_id: str) -> bool:
    return session_id in _store
