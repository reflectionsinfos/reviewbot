"""Project CRUD + Project Brain management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from recorder.db.session import get_db
from recorder.schemas.project import ProfileCardUpdate, ProjectCreate, ProjectResponse, SyncRequest

router = APIRouter()


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Create a new project. Triggers Project Setup Wizard (Phase 2)."""
    from recorder.db.models import Project
    project = Project(
        name=body.name,
        description=body.description,
        goals=body.goals,
        git_repo_path=body.git_repo_path,
        git_url=body.git_url,
        docs_folder=body.docs_folder,
        excluded_paths=body.excluded_paths,
        jira_project_key=body.jira_project_key,
        github_repo=body.github_repo,
        confluence_space=body.confluence_space,
        sharepoint_url=body.sharepoint_url,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return ProjectResponse.model_validate(project)


@router.get("/", response_model=list[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db)) -> list[ProjectResponse]:
    from sqlalchemy import select
    from recorder.db.models import Project
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    return [ProjectResponse.model_validate(p) for p in result.scalars().all()]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)) -> ProjectResponse:
    from sqlalchemy import select
    from recorder.db.models import Project
    result = await db.execute(select(Project).where(Project.project_id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse.model_validate(project)


@router.get("/{project_id}/profile-card")
async def get_profile_card(project_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    from sqlalchemy import select
    from recorder.db.models import Project
    result = await db.execute(select(Project).where(Project.project_id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"project_id": project_id, "profile_card": project.profile_card}


@router.put("/{project_id}/profile-card")
async def update_profile_card(
    project_id: str,
    body: ProfileCardUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    from sqlalchemy import select
    from recorder.db.models import Project
    result = await db.execute(select(Project).where(Project.project_id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.profile_card = body.profile_card
    await db.commit()
    return {"project_id": project_id, "profile_card": project.profile_card}


@router.post("/{project_id}/sync")
async def sync_project(
    project_id: str,
    body: SyncRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Trigger incremental sync of the Project Brain. Phase 2."""
    return {"project_id": project_id, "status": "sync_queued", "note": "Phase 2"}
