"""Pydantic schemas for Session."""

from datetime import datetime

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    project_id: str
    title: str = ""
    meeting_focus: str | None = None


class SessionResponse(BaseModel):
    session_id: str
    project_id: str
    title: str
    status: str
    meeting_focus: str | None
    start_time: datetime | None
    end_time: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class QueryRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    target_persona_id: str | None = None  # None = orchestrator routes automatically


class QueryResponse(BaseModel):
    session_id: str
    question: str
    answer: str
    responding_agent: str
    citations: list[str] = []
    conflicts_detected: list[str] = []  # conflict_ids if any
