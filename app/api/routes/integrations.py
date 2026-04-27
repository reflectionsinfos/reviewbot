"""
Integration management API.

Admin-only CRUD for IntegrationConfig, plus:
  POST /integrations/{id}/test            — verify connectivity
  POST /integrations/{id}/dispatch/{job_id} — manual dispatch
  GET  /integrations/dispatches/{job_id}  — dispatch history for a job
"""
import copy
import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.routes.auth import get_current_user
from app.db.session import get_db
from app.models import IntegrationConfig, IntegrationDispatch, User
from app.services.integrations.base import mask_secret

logger = logging.getLogger(__name__)
router = APIRouter()

_SUPPORTED_TYPES = {"jira", "smtp", "resend", "linear", "github_issues", "webhook"}
_TRIGGER_OPTIONS = {"always", "red_only", "manual"}

# Keys that contain secrets and must be masked in responses
_SECRET_KEYS = {"api_token", "password", "api_key", "token"}


def _mask_config(cfg: dict) -> dict:
    if not cfg:
        return {}
    masked = copy.deepcopy(cfg)
    for key in _SECRET_KEYS:
        if key in masked and masked[key]:
            masked[key] = mask_secret(masked[key])
    return masked


def _require_admin(user: User) -> None:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class IntegrationCreate(BaseModel):
    name: str
    type: str
    is_enabled: bool = False
    trigger_on: str = "red_only"
    include_advisories: bool = False
    config_json: dict[str, Any] = {}


class IntegrationUpdate(BaseModel):
    name: Optional[str] = None
    is_enabled: Optional[bool] = None
    trigger_on: Optional[str] = None
    include_advisories: Optional[bool] = None
    config_json: Optional[dict[str, Any]] = None


class IntegrationRead(BaseModel):
    id: int
    name: str
    type: str
    is_enabled: bool
    trigger_on: str
    include_advisories: bool
    config_json: dict[str, Any]

    class Config:
        from_attributes = True


class DispatchRead(BaseModel):
    id: int
    integration_id: int
    job_id: int
    triggered_by: str
    status: str
    items_dispatched: int
    items_failed: int
    results_json: Optional[list] = None
    error_message: Optional[str] = None
    dispatched_at: Any

    class Config:
        from_attributes = True


# ── CRUD ──────────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[IntegrationRead])
async def list_integrations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all integration configs (admin only). Secrets are masked."""
    _require_admin(current_user)
    result = await db.execute(select(IntegrationConfig))
    rows = result.scalars().all()
    return [
        IntegrationRead(
            id=r.id, name=r.name, type=r.type,
            is_enabled=r.is_enabled, trigger_on=r.trigger_on,
            include_advisories=r.include_advisories,
            config_json=_mask_config(r.config_json),
        )
        for r in rows
    ]


@router.post("/", response_model=IntegrationRead, status_code=201)
async def create_integration(
    payload: IntegrationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new integration config (admin only)."""
    _require_admin(current_user)
    if payload.type not in _SUPPORTED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported type '{payload.type}'. Supported: {sorted(_SUPPORTED_TYPES)}",
        )
    if payload.trigger_on not in _TRIGGER_OPTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid trigger_on '{payload.trigger_on}'. Options: {sorted(_TRIGGER_OPTIONS)}",
        )
    row = IntegrationConfig(**payload.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return IntegrationRead(
        id=row.id, name=row.name, type=row.type,
        is_enabled=row.is_enabled, trigger_on=row.trigger_on,
        include_advisories=row.include_advisories,
        config_json=_mask_config(row.config_json),
    )


@router.get("/{integration_id}", response_model=IntegrationRead)
async def get_integration(
    integration_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get one integration config (admin only). Secrets masked."""
    _require_admin(current_user)
    row = await db.get(IntegrationConfig, integration_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found")
    return IntegrationRead(
        id=row.id, name=row.name, type=row.type,
        is_enabled=row.is_enabled, trigger_on=row.trigger_on,
        include_advisories=row.include_advisories,
        config_json=_mask_config(row.config_json),
    )


@router.patch("/{integration_id}", response_model=IntegrationRead)
async def update_integration(
    integration_id: int,
    payload: IntegrationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an integration config (admin only)."""
    _require_admin(current_user)
    row = await db.get(IntegrationConfig, integration_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found")

    if payload.trigger_on is not None and payload.trigger_on not in _TRIGGER_OPTIONS:
        raise HTTPException(status_code=400, detail=f"Invalid trigger_on '{payload.trigger_on}'")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(row, field, value)

    await db.commit()
    await db.refresh(row)
    return IntegrationRead(
        id=row.id, name=row.name, type=row.type,
        is_enabled=row.is_enabled, trigger_on=row.trigger_on,
        include_advisories=row.include_advisories,
        config_json=_mask_config(row.config_json),
    )


@router.delete("/{integration_id}", status_code=204)
async def delete_integration(
    integration_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an integration config (admin only)."""
    _require_admin(current_user)
    row = await db.get(IntegrationConfig, integration_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found")
    await db.delete(row)
    await db.commit()


# ── Test connection ───────────────────────────────────────────────────────────

@router.post("/{integration_id}/test")
async def test_integration(
    integration_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Test connectivity for an integration (admin only)."""
    _require_admin(current_user)
    row = await db.get(IntegrationConfig, integration_id)
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found")

    cfg = row.config_json or {}
    ok, message = False, "Unknown integration type"

    if row.type == "jira":
        from app.services.integrations.jira import test_connection
        ok, message = await test_connection(cfg)
    elif row.type == "smtp":
        from app.services.integrations.email_smtp import test_connection
        ok, message = await test_connection(cfg)
    elif row.type == "resend":
        from app.services.integrations.email_resend import test_connection
        ok, message = await test_connection(cfg)
    else:
        message = f"Connection test not yet implemented for type '{row.type}'."

    return {"ok": ok, "message": message, "integration": row.name}


# ── Manual dispatch ───────────────────────────────────────────────────────────

@router.post("/{integration_id}/dispatch/{job_id}")
async def manual_dispatch(
    integration_id: int,
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Manually trigger one integration for a specific review job.
    Available to admins and managers.
    """
    if current_user.role not in ("admin", "manager"):
        raise HTTPException(status_code=403, detail="Admin or manager access required")

    from app.services.integrations.dispatcher import run_manual_dispatch
    result = await run_manual_dispatch(job_id, integration_id)

    return {
        "success": result.success,
        "dispatched": result.dispatched,
        "failed": result.failed,
        "items": result.to_json(),
        "error": result.error_message,
    }


# ── Dispatch history ──────────────────────────────────────────────────────────

@router.get("/dispatches/{job_id}", response_model=list[DispatchRead])
async def get_dispatch_history(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all dispatch logs for a given review job."""
    result = await db.execute(
        select(IntegrationDispatch)
        .where(IntegrationDispatch.job_id == job_id)
        .options(selectinload(IntegrationDispatch.integration))
        .order_by(IntegrationDispatch.dispatched_at.desc())
    )
    return result.scalars().all()
