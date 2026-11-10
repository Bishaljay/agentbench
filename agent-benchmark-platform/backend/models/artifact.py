"""Artifact model for capturing files, logs, and dumps."""
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base, utc_now_iso

class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("benchmark_runs.id", ondelete="CASCADE"), index=True)
    task_run_id: Mapped[Optional[int]] = mapped_column(ForeignKey("task_runs.id", ondelete="CASCADE"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(512))
    mime_type: Mapped[str] = mapped_column(String(100), default="application/octet-stream")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[str] = mapped_column(String(64), default=utc_now_iso)

    run: Mapped["Run"] = relationship("Run", back_populates="artifacts")
    task_run: Mapped[Optional["TaskRun"]] = relationship("TaskRun", back_populates="artifacts")

