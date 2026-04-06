"""
GyanPath — FastAPI entry point.

Start the server:
    cd D:/Langgraph/gyanpath
    uvicorn backend.main:app --reload --port 8000

The backend directory sits alongside the existing agent files
(graph.py, nodes.py, states.py …) so all imports resolve via
the repo-root sys.path insertion in runner.py.
"""

import sys
import os

# Ensure the repo root (gyanpath/) is on sys.path so that
# "from graph import graph" and "from states import State" work
# regardless of how uvicorn is launched.
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.learning_routes import router

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="GyanPath API",
    version="1.0.0",
    description=(
        "REST API that wraps the GyanPath LangGraph learning agent. "
        "Powers the React / Next.js frontend."
    ),
    docs_url="/docs",       # Swagger UI  →  http://localhost:8000/docs
    redoc_url="/redoc",     # ReDoc       →  http://localhost:8000/redoc
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Allows the Next.js dev server (port 3000) to call the API.
# Tighten allow_origins in production.

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",    # Next.js dev
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────

app.include_router(router, prefix="/api", tags=["Learning"])

# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["Meta"])
def health_check():
    """Simple liveness probe — returns 200 when the server is up."""
    return {"status": "ok", "service": "gyanpath-api"}
