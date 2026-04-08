"""Pydantic schemas for Persona."""

from datetime import datetime

from pydantic import BaseModel, Field


class PersonaCreate(BaseModel):
    session_id: str
    role_title: str = Field(..., min_length=1, max_length=128)
    role_description: str = ""
    accountability_areas: list[str] = []
    decision_domains: list[str] = []
    success_criteria: list[str] = []
    irrelevant_topics: list[str] = []
    prior_open_questions: list[str] = []
    is_async: bool = False
    template: str | None = None  # e.g., "architect" | "security" | "pm" | ...


class PersonaResponse(BaseModel):
    persona_id: str
    session_id: str
    role_title: str
    role_description: str
    accountability_areas: list[str]
    decision_domains: list[str]
    is_async: bool
    template: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class BriefingResponse(BaseModel):
    persona_id: str
    session_id: str
    role_title: str
    generated_at: datetime
    sections: dict  # matches PersonaBriefing JSON schema from design.md
