"""Nexus AI Meeting Recorder — FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from recorder.api.routes import chat, health, personas, projects, sessions
from recorder.api.websockets import chat as ws_chat
from recorder.core.config import settings
from recorder.core.logging import configure_logging
from recorder.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging()
    await init_db()
    yield


app = FastAPI(
    title="Nexus AI — Meeting Recorder Agent",
    description="Multi-Agent Meeting Intelligence System with Project Brain",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST routes
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(personas.router, prefix="/api/personas", tags=["personas"])
app.include_router(chat.router, prefix="/api", tags=["chat"])

# WebSocket
app.include_router(ws_chat.router, prefix="/ws", tags=["websocket"])
