"""Authentication and user session routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from models import User, AuditLog
from schemas import Credentials, TokenResponse, UserProfile
from security import (
    hash_password, verify_password, create_session_token,
    revoke_session_token, get_current_user
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: Credentials, db: Session = Depends(get_db)):
    """Register a new user account."""
    existing = db.scalar(select(User).where(User.username == data.username))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )

    # First user is made admin; subsequent users are operators
    user_count = db.scalar(select(User.id).limit(1))
    role = "admin" if user_count is None else "operator"

    user = User(
        username=data.username,
        password=hash_password(data.password),
        role=role,
        is_active=True
    )
    db.add(user)
    db.flush()

    db.add(AuditLog(
        user_id=user.id,
        username=user.username,
        action="user_registered",
        entity_type="user",
        entity_id=str(user.id),
        details='{"role": "' + role + '"}'
    ))
    db.commit()
    return {"message": "Account created successfully", "role": role}

@router.post("/login", response_model=TokenResponse)
def login(data: Credentials, db: Session = Depends(get_db)):
    """Authenticate and obtain session token."""
    user = db.scalar(select(User).where(User.username == data.username))
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    token = create_session_token(db, user)

    db.add(AuditLog(
        user_id=user.id,
        username=user.username,
        action="user_login",
        entity_type="user",
        entity_id=str(user.id)
    ))
    db.commit()

    return TokenResponse(
        token=token,
        username=user.username,
        role=user.role or "operator"
    )

@router.post("/logout")
def logout(
    authorization: Optional[str] = Header(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Invalidate current session token."""
    token_str = authorization[7:].strip() if authorization and authorization.startswith("Bearer ") else ""
    if token_str:
        revoke_session_token(db, token_str)
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserProfile)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return UserProfile(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role or "operator",
        is_active=current_user.is_active,
        created_at=current_user.created_at or ""
    )

