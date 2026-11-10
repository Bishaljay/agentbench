"""User management and administration routes."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import User, AuditLog
from schemas import UserProfile, UserUpdate
from security import get_current_user, require_admin, hash_password

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.get("", response_model=List[UserProfile])
def list_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all registered users (Admin only)."""
    users = db.scalars(select(User).order_by(User.id)).all()
    return [
        UserProfile(
            id=u.id,
            username=u.username,
            role=u.role or "operator",
            is_active=u.is_active,
            created_at=u.created_at or ""
        )
        for u in users
    ]

@router.put("/{user_id}", response_model=UserProfile)
def update_user(
    user_id: int,
    data: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update user role, status, or reset password (Admin only)."""
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    if data.role is not None:
        if data.role not in ("admin", "operator", "viewer"):
            raise HTTPException(status_code=400, detail="Invalid role specified")
        target.role = data.role
    if data.is_active is not None:
        target.is_active = data.is_active
    if data.password is not None:
        target.password = hash_password(data.password)

    db.add(AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="user_updated",
        entity_type="user",
        entity_id=str(target.id)
    ))
    db.commit()
    db.refresh(target)

    return UserProfile(
        id=target.id,
        username=target.username,
        role=target.role or "operator",
        is_active=target.is_active,
        created_at=target.created_at or ""
    )

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a user account (Admin only). Cannot delete own account."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(target)
    db.add(AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="user_deleted",
        entity_type="user",
        entity_id=str(user_id)
    ))
    db.commit()
    return {"message": f"User {target.username} deleted"}

