"""
AI Tech & Delivery Review Agent
Main Application Entry Point
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.core.config import settings
from app.api.routes import projects, reviews, reports, checklists, auth
from app.api.routes.organizations import router as organizations_router
from app.api.routes.users import router as users_router
from app.api.routes.autonomous_reviews import router as autonomous_reviews_router
from app.api.routes.agent import router as agent_router
from app.api.routes.routing_rules import router as routing_rules_router
from app.api.routes.llm_configs import router as llm_configs_router
from app.api.routes.settings import router as settings_router
from app.api.routes.integrations import router as integrations_router
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

# Trust proxy headers from Cloud Run / load balancers (fixes https→http redirect downgrade)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

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
app.include_router(llm_configs_router,         prefix="/api/llm-configs",        tags=["LLM Configuration"])
app.include_router(settings_router,            prefix="/api/settings",           tags=["System Settings"])
app.include_router(organizations_router,       prefix="/api/organizations",       tags=["Organizations"])
app.include_router(users_router,               prefix="/api/admin",              tags=["Admin - User Management"])
app.include_router(integrations_router,        prefix="/api/integrations",        tags=["Integrations"])


# Diagnostic route for LLM test (direct to main)
@app.post("/api/llm-test-direct")
async def llm_test_direct(config_in: dict):
    from app.services.autonomous_review.connectors.llm import validate_llm_connectivity
    from app.models import LLMConfig
    temp = LLMConfig(**config_in)
    success, msg = await validate_llm_connectivity(overriding_config=temp)
    return {"success": success, "message": msg}

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

# ── Frontend (Vanilla JS) ─────────────────────────────────────────────────────
_frontend_dir = os.path.join(os.path.dirname(__file__), "frontend_vanilla")
if os.path.isdir(_frontend_dir):
    app.mount("/frontend_vanilla", StaticFiles(directory=_frontend_dir), name="frontend")


@app.get("/ui", include_in_schema=False)
async def serve_ui():
    """Serve the Autonomous Review frontend UI"""
    return FileResponse(os.path.join(_frontend_dir, "index.html"))


@app.get("/history", include_in_schema=False)
@app.get("/history/{job_id}", include_in_schema=False)
async def serve_history(job_id: int = None):
    """Serve the Report History UI (job_id handled client-side via JS)"""
    return FileResponse(os.path.join(_frontend_dir, "history.html"))


@app.get("/projects-ui", include_in_schema=False)
@app.get("/projects-ui/{project_id}", include_in_schema=False)
async def serve_projects_ui(project_id: int = None):
    """Serve the Projects & Checklists Management UI"""
    return FileResponse(os.path.join(_frontend_dir, "project.html"))


@app.get("/globals", include_in_schema=False)
async def serve_globals():
    """Serve the Global Templates Management UI"""
    return FileResponse(os.path.join(_frontend_dir, "globals.html"))


@app.get("/global", include_in_schema=False)
async def redirect_to_globals():
    """Redirect /global to /globals"""
    return RedirectResponse(url="/globals")


@app.get("/documentation", include_in_schema=False)
async def serve_documentation():
    """Serve the How It Works documentation page"""
    return FileResponse(os.path.join(_frontend_dir, "documentation.html"))


@app.get("/system-config", include_in_schema=False)
async def serve_system_config_ui():
    """Serve the System Configuration Management UI"""
    return FileResponse(os.path.join(_frontend_dir, "system_config.html"))


# ── Health / root ─────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def serve_home():
    """Serve the ReviewBot home / dashboard page"""
    return FileResponse(os.path.join(_frontend_dir, "home.html"))


@app.get("/dashboard", include_in_schema=False)
async def serve_dashboard():
    """Alias for / - serves the ReviewBot dashboard page"""
    return FileResponse(os.path.join(_frontend_dir, "home.html"))


@app.get("/api/status")
async def root():
    """JSON status endpoint (previously at /)"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "ui": "/",
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
