"""Benchmark and BenchmarkVersion models."""
from typing import List, Optional
from sqlalchemy import String, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base, utc_now_iso

class Benchmark(Base):
    __tablename__ = "benchmarks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(50), default="General")
    created_at: Mapped[str] = mapped_column(String(64), default=utc_now_iso)

    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="benchmark", cascade="all, delete-orphan")
    versions: Mapped[List["BenchmarkVersion"]] = relationship("BenchmarkVersion", back_populates="benchmark", cascade="all, delete-orphan")
    runs: Mapped[List["Run"]] = relationship("Run", back_populates="benchmark")

class BenchmarkVersion(Base):
    __tablename__ = "benchmark_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    benchmark_id: Mapped[int] = mapped_column(ForeignKey("benchmarks.id", ondelete="CASCADE"))
    version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(String(64), default=utc_now_iso)

    benchmark: Mapped["Benchmark"] = relationship("Benchmark", back_populates="versions")

