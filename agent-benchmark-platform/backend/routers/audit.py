"""Audit log inspection routes."""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import AuditLog, User
from schemas import AuditLogOut
from security import get_current_user, require_admin

router = APIRouter(prefix="/api/audit-logs", tags=["Audit Logs"])

@router.get("", response_model=List[AuditLogOut])
def list_audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    action: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve system and user activity audit trail."""
    stmt = select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    logs = db.scalars(stmt).all()
    return [
        AuditLogOut(
            id=log.id,
            user_id=log.user_id,
            username=log.username or "system",
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            details=log.details or "{}",
            ip_address=log.ip_address,
            created_at=log.created_at or ""
        )
        for log in logs
    ]

