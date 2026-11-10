"""Security, password hashing, token validation, and RBAC utilities."""
import hmac
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import Header, HTTPException, Depends, status
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from database import get_db
from models import User, SessionToken
from config import TOKEN_EXPIRE_HOURS

def hash_password(password: str, salt: Optional[str] = None) -> str:
    """Hash password using PBKDF2 HMAC SHA-256 with 200,000 iterations."""
    salt = salt or secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200000).hex()
    return f"{salt}${hashed}"

def verify_password(plain_password: str, stored_hash: str) -> bool:
    """Verify password against salt$hash format using constant-time comparison."""
    if not stored_hash or "$" not in stored_hash:
        return False
    salt = stored_hash.split("$")[0]
    expected = hash_password(plain_password, salt=salt)
    return hmac.compare_digest(stored_hash, expected)

def create_session_token(db: Session, user: User) -> str:
    """Generate a cryptographically secure session token with expiration."""
    token_str = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)).isoformat()
    
    # Also record in session_tokens table
    session_token = SessionToken(
        token=token_str,
        user_id=user.id,
        expires_at=expires_at,
        is_revoked=False
    )
    db.add(session_token)
    # Update user.token for legacy compatibility
    user.token = token_str
    db.commit()
    return token_str

def revoke_session_token(db: Session, token_str: str) -> bool:
    """Revoke a session token upon logout."""
    # Revoke in session_tokens table
    stmt = select(SessionToken).where(SessionToken.token == token_str)
    st = db.scalar(stmt)
    if st:
        st.is_revoked = True
    
    # Clear on user if matching
    user_stmt = select(User).where(User.token == token_str)
    user = db.scalar(user_stmt)
    if user:
        user.token = None
    db.commit()
    return True

def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db)
) -> User:
    """FastAPI dependency to extract and validate authenticated user from Bearer token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token_str = authorization[7:].strip()
    if not token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empty authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 1. Check session_tokens table
    st = db.scalar(
        select(SessionToken).where(
            and_(
                SessionToken.token == token_str,
                SessionToken.is_revoked == False
            )
        )
    )
    if st:
        # Check expiration
        exp = datetime.fromisoformat(st.expires_at)
        if exp < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = db.get(User, st.user_id)
        if user and user.is_active:
            return user

    # 2. Fallback check on users.token for legacy/pre-existing sessions
    user = db.scalar(select(User).where(User.token == token_str))
    if user and user.is_active:
        return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or revoked session",
        headers={"WWW-Authenticate": "Bearer"},
    )

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Ensure current user has administrative privileges."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required"
        )
    return current_user

