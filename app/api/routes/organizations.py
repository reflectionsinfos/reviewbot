"""
Organizations API Routes

Provides CRUD for Organization records. Admins can manage all organizations;
any authenticated user can list active organizations (needed for dropdowns) and
retrieve their own org.
"""
import logging
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.auth import get_current_user
from app.db.session import get_db
from app.models import Organization, User

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class OrgCreate(BaseModel):
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None


class OrgUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _to_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _org_dict(org: Organization) -> dict:
    return {
        "id": org.id,
        "name": org.name,
        "slug": org.slug,
        "description": org.description,
        "is_active": org.is_active,
        "created_at": org.created_at.isoformat() if org.created_at else None,
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/")
async def list_organizations(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List organizations. Any authenticated user may call this (needed for dropdowns)."""
    query = select(Organization)
    if active_only:
        query = query.where(Organization.is_active == True)
    query = query.order_by(Organization.name)
    result = await db.execute(query)
    orgs = result.scalars().all()
    return {"organizations": [_org_dict(o) for o in orgs], "total": len(orgs)}


@router.get("/mine")
async def get_my_organization(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the organization the current user belongs to, or null."""
    if not current_user.organization_id:
        return {"organization": None}
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = result.scalar_one_or_none()
    return {"organization": _org_dict(org) if org else None}


@router.get("/{org_id}")
async def get_organization(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single organization by ID."""
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return _org_dict(org)


@router.post("/", status_code=201)
async def create_organization(
    req: OrgCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new organization. Admin only."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    slug = (req.slug or _to_slug(req.name)).lower().strip("-")
    if not slug:
        raise HTTPException(status_code=400, detail="Organization name produced an empty slug")

    existing = await db.execute(select(Organization).where(Organization.slug == slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Organization with slug '{slug}' already exists")

    org = Organization(name=req.name.strip(), slug=slug, description=req.description)
    db.add(org)
    await db.commit()
    await db.refresh(org)
    logger.info("Organization created: %s (id=%s) by %s", org.name, org.id, current_user.email)
    return _org_dict(org)


@router.put("/{org_id}")
async def update_organization(
    org_id: int,
    req: OrgUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an organization. Admin only."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if req.name is not None:
        org.name = req.name.strip()
    if req.slug is not None:
        new_slug = req.slug.lower().strip("-")
        if new_slug != org.slug:
            clash = await db.execute(select(Organization).where(Organization.slug == new_slug))
            if clash.scalar_one_or_none():
                raise HTTPException(status_code=409, detail=f"Slug '{new_slug}' already in use")
            org.slug = new_slug
    if req.description is not None:
        org.description = req.description
    if req.is_active is not None:
        org.is_active = req.is_active

    await db.commit()
    await db.refresh(org)
    logger.info("Organization updated: %s (id=%s) by %s", org.name, org.id, current_user.email)
    return _org_dict(org)


@router.delete("/{org_id}", status_code=204)
async def delete_organization(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an organization. Admin only. Soft-deletes by setting is_active=False."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    org.is_active = False
    await db.commit()
    logger.info("Organization deactivated: %s (id=%s) by %s", org.name, org.id, current_user.email)
