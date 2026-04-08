"""Pydantic schemas for Project and Project Brain."""

from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    goals: list[str] = []
    git_repo_path: str | None = None
    git_url: str | None = None
    docs_folder: str | None = None
    excluded_paths: list[str] = []
    jira_project_key: str | None = None
    github_repo: str | None = None
    confluence_space: str | None = None
    sharepoint_url: str | None = None


class ProfileCardUpdate(BaseModel):
    profile_card: str = Field(..., max_length=3000)


class ProjectResponse(BaseModel):
    project_id: str
    name: str
    description: str
    goals: list[str]
    git_repo_path: str | None
    git_url: str | None
    docs_folder: str | None
    profile_card: str | None
    indexing_status: str
    last_indexed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SyncRequest(BaseModel):
    force_full_reindex: bool = False
