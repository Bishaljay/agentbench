"""Task and TaskVersion models."""
from typing import List, Optional
from sqlalchemy import String, Integer, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base, utc_now_iso

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    benchmark_id: Mapped[int] = mapped_column(ForeignKey("benchmarks.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(150), index=True)
    category: Mapped[str] = mapped_column(String(50), default="General")
    operation: Mapped[str] = mapped_column(String(50))
    input: Mapped[str] = mapped_column(Text)
    expected: Mapped[str] = mapped_column(Text)
    timeout: Mapped[float] = mapped_column(Float, default=3.0)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    memory_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), default=utc_now_iso)

    benchmark: Mapped["Benchmark"] = relationship("Benchmark", back_populates="tasks")
    task_runs: Mapped[List["TaskRun"]] = relationship("TaskRun", back_populates="task")
    versions: Mapped[List["TaskVersion"]] = relationship("TaskVersion", back_populates="task", cascade="all, delete-orphan")

class TaskVersion(Base):
    __tablename__ = "task_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    input: Mapped[str] = mapped_column(Text)
    expected: Mapped[str] = mapped_column(Text)
    timeout: Mapped[float] = mapped_column(Float, default=3.0)
    created_at: Mapped[str] = mapped_column(String(64), default=utc_now_iso)

    task: Mapped["Task"] = relationship("Task", back_populates="versions")

