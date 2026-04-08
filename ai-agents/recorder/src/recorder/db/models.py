"""SQLAlchemy ORM models for the Meeting Recorder Agent."""

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from recorder.db.session import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Project(Base):
    __tablename__ = "projects"

    project_id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    goals: Mapped[dict] = mapped_column(JSON, default=list)

    # Sources
    git_repo_path: Mapped[str | None] = mapped_column(String(1024))
    git_url: Mapped[str | None] = mapped_column(String(1024))
    docs_folder: Mapped[str | None] = mapped_column(String(1024))
    excluded_paths: Mapped[dict] = mapped_column(JSON, default=list)

    # External integrations
    jira_project_key: Mapped[str | None] = mapped_column(String(64))
    github_repo: Mapped[str | None] = mapped_column(String(256))
    confluence_space: Mapped[str | None] = mapped_column(String(256))
    sharepoint_url: Mapped[str | None] = mapped_column(String(1024))

    # Project Brain
    profile_card: Mapped[str | None] = mapped_column(Text)  # < 500 tokens, always in prompt
    last_indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_git_commit: Mapped[str | None] = mapped_column(String(40))
    indexing_status: Mapped[str] = mapped_column(
        String(32), default="idle"
    )  # idle | running | complete | error

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    sessions: Mapped[list["Session"]] = relationship(back_populates="project")
    code_index: Mapped[list["ProjectCodeIndex"]] = relationship(back_populates="project")


class Session(Base):
    __tablename__ = "sessions"

    session_id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.project_id"), nullable=False)
    title: Mapped[str] = mapped_column(String(512), default="")
    status: Mapped[str] = mapped_column(
        String(32), default="pre_meeting"
    )  # pre_meeting | in_progress | post_meeting | archived
    meeting_focus: Mapped[str | None] = mapped_column(Text)
    preloaded_context: Mapped[str | None] = mapped_column(Text)  # pre-retrieved for this topic
    global_rolling_summary: Mapped[str | None] = mapped_column(Text)
    meeting_brief: Mapped[dict | None] = mapped_column(JSON)

    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="sessions")
    personas: Mapped[list["Persona"]] = relationship(back_populates="session")
    transcript_chunks: Mapped[list["TranscriptChunk"]] = relationship(back_populates="session")
    conflicts: Mapped[list["Conflict"]] = relationship(back_populates="session")
    understanding_documents: Mapped[list["UnderstandingDocument"]] = relationship(
        back_populates="session"
    )


class Persona(Base):
    __tablename__ = "personas"

    persona_id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.session_id"), nullable=False)
    role_title: Mapped[str] = mapped_column(String(128), nullable=False)
    role_description: Mapped[str] = mapped_column(Text, default="")
    accountability_areas: Mapped[dict] = mapped_column(JSON, default=list)
    decision_domains: Mapped[dict] = mapped_column(JSON, default=list)
    success_criteria: Mapped[dict] = mapped_column(JSON, default=list)
    irrelevant_topics: Mapped[dict] = mapped_column(JSON, default=list)
    prior_open_questions: Mapped[dict] = mapped_column(JSON, default=list)
    rolling_summary: Mapped[str | None] = mapped_column(Text)
    is_async: Mapped[bool] = mapped_column(Boolean, default=False)
    template: Mapped[str | None] = mapped_column(String(64))  # built-in template name
    briefing: Mapped[dict | None] = mapped_column(JSON)  # populated post-meeting
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["Session"] = relationship(back_populates="personas")


class TranscriptChunk(Base):
    __tablename__ = "transcript_chunks"

    chunk_id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.session_id"), nullable=False)
    segment_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    speakers: Mapped[dict] = mapped_column(JSON, default=list)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    relevance_scores: Mapped[dict] = mapped_column(JSON, default=dict)  # {agent_id: score}

    session: Mapped["Session"] = relationship(back_populates="transcript_chunks")


class ProjectCodeIndex(Base):
    __tablename__ = "project_code_index"

    entry_id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.project_id"), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    component_name: Mapped[str] = mapped_column(String(256), nullable=False)
    level: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # module | class | endpoint | schema | config
    summary: Mapped[str] = mapped_column(Text, nullable=False)  # LLM-generated, embedded in Chroma
    git_commit: Mapped[str | None] = mapped_column(String(40))
    last_modified: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="code_index")


class Conflict(Base):
    __tablename__ = "conflicts"

    conflict_id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.session_id"), nullable=False)
    timestamp_in_meeting: Mapped[float | None] = mapped_column(Float)
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    agents_involved: Mapped[dict] = mapped_column(JSON, default=list)
    agent_positions: Mapped[dict] = mapped_column(JSON, default=dict)
    conflict_type: Mapped[str] = mapped_column(
        String(64), default="contradiction"
    )  # contradiction | unacknowledged_dependency | risk_gap
    resolution_status: Mapped[str] = mapped_column(
        String(32), default="unresolved"
    )  # unresolved | resolved | deferred
    resolution_notes: Mapped[str | None] = mapped_column(Text)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["Session"] = relationship(back_populates="conflicts")


class UnderstandingDocument(Base):
    __tablename__ = "understanding_documents"

    doc_id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.session_id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    content: Mapped[dict] = mapped_column(JSON, default=dict)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    session: Mapped["Session"] = relationship(back_populates="understanding_documents")
