"""EvaluationResult model for granular evaluation breakdown."""
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base, utc_now_iso

class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_run_id: Mapped[int] = mapped_column(ForeignKey("task_runs.id", ondelete="CASCADE"), index=True)
    metric_name: Mapped[str] = mapped_column(String(100))
    score: Mapped[float] = mapped_column(Float, default=0.0)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    details: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(String(64), default=utc_now_iso)

    task_run: Mapped["TaskRun"] = relationship("TaskRun", back_populates="evaluation_results")

