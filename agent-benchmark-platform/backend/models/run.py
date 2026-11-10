"""Benchmark run and task run models."""
from typing import List, Optional
from sqlalchemy import String, Integer, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base, utc_now_iso

class Run(Base):
    __tablename__ = "benchmark_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"), index=True)
    benchmark_id: Mapped[int] = mapped_column(ForeignKey("benchmarks.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(50), default="QUEUED", index=True)
    created_at: Mapped[str] = mapped_column(String(64), default=utc_now_iso)
    finished_at: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    cancel: Mapped[int] = mapped_column(Integer, default=0)

    agent: Mapped["Agent"] = relationship("Agent", back_populates="runs")
    benchmark: Mapped["Benchmark"] = relationship("Benchmark", back_populates="runs")
    task_runs: Mapped[List["TaskRun"]] = relationship("TaskRun", back_populates="run", cascade="all, delete-orphan")
    artifacts: Mapped[List["Artifact"]] = relationship("Artifact", back_populates="run", cascade="all, delete-orphan")

class TaskRun(Base):
    __tablename__ = "task_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("benchmark_runs.id", ondelete="CASCADE"), index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(50), index=True)
    output: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str] = mapped_column(Text, default="")
    duration: Mapped[float] = mapped_column(Float, default=0.0)
    cpu: Mapped[float] = mapped_column(Float, default=0.0)
    memory: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    retries: Mapped[int] = mapped_column(Integer, default=0)

    run: Mapped["Run"] = relationship("Run", back_populates="task_runs")
    task: Mapped["Task"] = relationship("Task", back_populates="task_runs")
    evaluation_results: Mapped[List["EvaluationResult"]] = relationship("EvaluationResult", back_populates="task_run", cascade="all, delete-orphan")
    artifacts: Mapped[List["Artifact"]] = relationship("Artifact", back_populates="task_run", cascade="all, delete-orphan")

