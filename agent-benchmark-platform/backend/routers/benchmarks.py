"""Benchmark Suite management routes."""
import json
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import Benchmark, BenchmarkVersion, Task, AuditLog, User
from schemas import BenchmarkIn, BenchmarkUpdate, BenchmarkOut
from security import get_current_user

router = APIRouter(prefix="/api/benchmarks", tags=["Benchmarks"])

@router.get("", response_model=List[BenchmarkOut])
def list_benchmarks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all benchmark suites."""
    benchmarks = db.scalars(select(Benchmark).order_by(Benchmark.id)).all()
    return [
        BenchmarkOut(
            id=b.id,
            name=b.name,
            description=b.description or "",
            category=b.category or "General",
            created_at=b.created_at or ""
        )
        for b in benchmarks
    ]

@router.post("", response_model=BenchmarkOut, status_code=status.HTTP_201_CREATED)
def create_benchmark(
    data: BenchmarkIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new benchmark suite."""
    existing = db.scalar(select(Benchmark).where(Benchmark.name == data.name))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Benchmark with name '{data.name}' already exists"
        )

    b = Benchmark(
        name=data.name,
        description=data.description,
        category=data.category
    )
    db.add(b)
    db.flush()

    db.add(BenchmarkVersion(
        benchmark_id=b.id,
        version="1.0.0",
        notes="Initial creation"
    ))

    db.add(AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="benchmark_created",
        entity_type="benchmark",
        entity_id=str(b.id),
        details=json.dumps({"name": b.name, "category": b.category})
    ))

    db.commit()
    db.refresh(b)
    return BenchmarkOut(
        id=b.id,
        name=b.name,
        description=b.description or "",
        category=b.category or "General",
        created_at=b.created_at or ""
    )

@router.get("/{benchmark_id}")
def get_benchmark_details(
    benchmark_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve full details of a benchmark suite and its tasks."""
    b = db.get(Benchmark, benchmark_id)
    if not b:
        raise HTTPException(status_code=404, detail="Benchmark not found")

    tasks = db.scalars(select(Task).where(Task.benchmark_id == benchmark_id).order_by(Task.id)).all()
    return {
        "id": b.id,
        "name": b.name,
        "description": b.description or "",
        "category": b.category or "General",
        "created_at": b.created_at or "",
        "tasks": [
            {
                "id": t.id,
                "name": t.name,
                "category": t.category,
                "operation": t.operation,
                "input": t.input,
                "expected": t.expected,
                "timeout": t.timeout,
                "difficulty": t.difficulty,
                "memory_limit": t.memory_limit
            }
            for t in tasks
        ]
    }

@router.put("/{benchmark_id}", response_model=BenchmarkOut)
def update_benchmark(
    benchmark_id: int,
    data: BenchmarkUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a benchmark suite."""
    b = db.get(Benchmark, benchmark_id)
    if not b:
        raise HTTPException(status_code=404, detail="Benchmark not found")

    if data.name and data.name != b.name:
        existing = db.scalar(select(Benchmark).where(Benchmark.name == data.name))
        if existing:
            raise HTTPException(status_code=409, detail="Benchmark name already in use")
        b.name = data.name

    if data.description is not None:
        b.description = data.description
    if data.category is not None:
        b.category = data.category

    db.add(AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="benchmark_updated",
        entity_type="benchmark",
        entity_id=str(b.id)
    ))
    db.commit()
    db.refresh(b)
    return BenchmarkOut(
        id=b.id,
        name=b.name,
        description=b.description or "",
        category=b.category or "General",
        created_at=b.created_at or ""
    )

@router.delete("/{benchmark_id}")
def delete_benchmark(
    benchmark_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a benchmark suite and all attached tasks."""
    b = db.get(Benchmark, benchmark_id)
    if not b:
        raise HTTPException(status_code=404, detail="Benchmark not found")

    name = b.name
    db.delete(b)
    db.add(AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="benchmark_deleted",
        entity_type="benchmark",
        entity_id=str(benchmark_id),
        details=json.dumps({"name": name})
    ))
    db.commit()
    return {"message": f"Benchmark suite '{name}' deleted"}

