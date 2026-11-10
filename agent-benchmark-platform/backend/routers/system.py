"""System health, diagnostics, and settings routes."""
import time
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from database import get_db, SessionLocal
from models import Run, SystemSetting, User, utc_now_iso
from schemas import HealthResponse, SettingIn, SettingOut
from security import get_current_user, require_admin

router = APIRouter(prefix="/api/system", tags=["System"])

HEARTBEAT_FILE = Path(__file__).resolve().parents[1] / ".worker_heartbeat"

@router.get("/health", response_model=HealthResponse)
def health_check():
    """Verify backend API, database connectivity, and worker operational status."""
    # 1. Database check
    db_status = "connected"
    active_runs = 0
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
            active_runs = db.scalar(
                select(Run.id).where(Run.status.in_(["RUNNING", "QUEUED"])).count()
            ) or 0
    except Exception as e:
        db_status = f"error: {str(e)}"

    # 2. Worker heartbeat check
    worker_status = "not running (start via 'python worker.py')"
    if HEARTBEAT_FILE.exists():
        try:
            last_beat = float(HEARTBEAT_FILE.read_text(encoding="utf-8").strip())
            age = time.time() - last_beat
            if age < 15.0:
                worker_status = f"active (heartbeat {round(age, 1)}s ago)"
            else:
                worker_status = f"stale (last heartbeat {round(age, 1)}s ago)"
        except Exception:
            worker_status = "unknown"

    overall_status = "ok" if db_status == "connected" else "degraded"

    return HealthResponse(
        status=overall_status,
        database=db_status,
        worker=worker_status,
        version="0.2.0",
        environment="development",
        active_runs=active_runs,
        timestamp=utc_now_iso()
    )

@router.get("/settings", response_model=List[SettingOut])
def list_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve platform configuration settings."""
    settings = db.scalars(select(SystemSetting).order_by(SystemSetting.key)).all()
    return [
        SettingOut(
            key=s.key,
            value=s.value,
            description=s.description or "",
            updated_at=s.updated_at or ""
        )
        for s in settings
    ]

@router.put("/settings/{key}", response_model=SettingOut)
def update_setting(
    key: str,
    data: SettingIn,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update a platform configuration setting (Admin only)."""
    setting = db.scalar(select(SystemSetting).where(SystemSetting.key == key))
    if not setting:
        setting = SystemSetting(key=key, value=data.value, description=data.description or "")
        db.add(setting)
    else:
        setting.value = data.value
        if data.description is not None:
            setting.description = data.description
        setting.updated_at = utc_now_iso()

    db.commit()
    db.refresh(setting)
    return SettingOut(
        key=setting.key,
        value=setting.value,
        description=setting.description,
        updated_at=setting.updated_at or ""
    )

