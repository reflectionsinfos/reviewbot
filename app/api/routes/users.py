"""
Admin User Management Routes
"""
import secrets
import string
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.db.session import get_db
from app.models import Organization, User
from app.api.routes.auth import get_current_user, get_password_hash

router = APIRouter()


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


def _generate_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$^"
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        # Ensure at least one of each required type
        if (any(c.isupper() for c in pwd)
                and any(c.islower() for c in pwd)
                and any(c.isdigit() for c in pwd)
                and any(c in "!@#$%" for c in pwd)):
            return pwd


class CreateUserRequest(BaseModel):
    email: str
    full_name: str
    role: str = "reviewer"
    organization_id: Optional[int] = None


class UpdateUserRequest(BaseModel):
    is_active: Optional[bool] = None
    role: Optional[str] = None
    # Pass positive int to assign, 0 to unassign, None to leave unchanged
    organization_id: Optional[int] = None


@router.get("/users")
async def list_users(
    admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all users with organization info (admin only)"""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()

    org_ids = {u.organization_id for u in users if u.organization_id}
    org_names: dict = {}
    if org_ids:
        org_result = await db.execute(
            select(Organization).where(Organization.id.in_(org_ids))
        )
        for org in org_result.scalars().all():
            org_names[org.id] = org.name

    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "is_active": u.is_active,
            "organization_id": u.organization_id,
            "organization_name": org_names.get(u.organization_id) if u.organization_id else None,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@router.post("/users", status_code=201)
async def create_user(
    req: CreateUserRequest,
    admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new user with a generated default password (admin only)"""
    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    if req.role not in ("reviewer", "manager", "admin"):
        raise HTTPException(status_code=400, detail="Role must be reviewer, manager, or admin")

    plain_password = _generate_password()
    user = User(
        email=req.email,
        full_name=req.full_name,
        hashed_password=get_password_hash(plain_password),
        role=req.role,
        is_active=True,
        organization_id=req.organization_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "generated_password": plain_password,
    }


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Reset a user's password and return the new generated password (admin only)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    plain_password = _generate_password()
    user.hashed_password = get_password_hash(plain_password)
    await db.commit()

    return {
        "id": user.id,
        "email": user.email,
        "generated_password": plain_password,
    }


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a user (admin only). Cannot delete your own account."""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()


@router.patch("/users/{user_id}")
async def update_user(
    user_id: int,
    req: UpdateUserRequest,
    admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update user role or active status (admin only)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if req.is_active is not None:
        user.is_active = req.is_active
    if req.role is not None:
        if req.role not in ("reviewer", "manager", "admin"):
            raise HTTPException(status_code=400, detail="Role must be reviewer, manager, or admin")
        user.role = req.role
    if req.organization_id is not None:
        # 0 means unassign, positive int means assign to that org
        user.organization_id = req.organization_id if req.organization_id > 0 else None

    await db.commit()
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "organization_id": user.organization_id,
    }
