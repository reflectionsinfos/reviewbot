"""
AI Tech & Delivery Review Agent
Main Application Entry Point
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import settings
from app.api.routes import projects, reviews, reports, checklists, auth
from app.api.routes.autonomous_reviews import router as autonomous_reviews_router
from app.api.routes.agent import router as agent_router
from app.api.routes.routing_rules import router as routing_rules_router
from app.db.session import init_db
from app.services.autonomous_review.progress import progress_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    await init_db()
    print(f"✅ {settings.APP_NAME} v{settings.APP_VERSION} started")
    yield
    print("👋 Application shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Conversational AI agent for technical and delivery project reviews",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── REST API Routes ───────────────────────────────────────────────────────────
app.include_router(auth.router,                 prefix="/api/auth",              tags=["Authentication"])
app.include_router(projects.router,             prefix="/api/projects",           tags=["Projects"])
app.include_router(checklists.router,           prefix="/api/checklists",         tags=["Checklists"])
app.include_router(reviews.router,              prefix="/api/reviews",            tags=["Reviews"])
app.include_router(reports.router,              prefix="/api/reports",            tags=["Reports"])
app.include_router(autonomous_reviews_router,   prefix="/api/autonomous-reviews", tags=["Autonomous Review"])
app.include_router(agent_router,               prefix="/api/v1/agent/scan",      tags=["Agent Bridge"])
app.include_router(routing_rules_router,       prefix="/api/routing-rules",      tags=["Routing Rules"])

# ── WebSocket — Autonomous Review live progress ───────────────────────────────
@app.websocket("/ws/autonomous-reviews/{job_id}")
async def ws_autonomous_review(websocket: WebSocket, job_id: int):
    """
    Real-time progress stream for an autonomous review job.
    Connect after calling POST /api/autonomous-reviews/ to receive live updates.

    Message types:
      scanning | scan_complete | started | item_start | item_complete | completed | error
    """
    await progress_manager.connect(job_id, websocket)
    try:
        while True:
            await websocket.receive_text()   # keep-alive (client sends "ping")
    except WebSocketDisconnect:
        progress_manager.disconnect(job_id, websocket)

# ── Static frontend ────────────────────────────────────────────────────────────
_static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")


@app.get("/ui", include_in_schema=False)
async def serve_ui():
    """Serve the Autonomous Review frontend UI"""
    return FileResponse(os.path.join(_static_dir, "index.html"))


@app.get("/history", include_in_schema=False)
@app.get("/history/{job_id}", include_in_schema=False)
async def serve_history(job_id: int = None):
    """Serve the Report History UI (job_id handled client-side via JS)"""
    return FileResponse(os.path.join(_static_dir, "history.html"))


@app.get("/projects-ui", include_in_schema=False)
@app.get("/projects-ui/{project_id}", include_in_schema=False)
async def serve_projects_ui(project_id: int = None):
    """Serve the Projects & Checklists Management UI"""
    return FileResponse(os.path.join(_static_dir, "project.html"))


# ── Health / root ─────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "ui": "/ui",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "voice_enabled": settings.VOICE_ENABLED,
        "human_approval_required": settings.REQUIRE_HUMAN_APPROVAL,
    }
