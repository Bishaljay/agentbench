"""Benchmark Execution runs routes."""
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import Run, TaskRun, Agent, Benchmark, Task, AuditLog, User, utc_now_iso
from schemas import RunIn, RunOut, RunDetailOut, TaskRunOut
from security import get_current_user

router = APIRouter(prefix="/api/runs", tags=["Benchmark Runs"])

@router.get("", response_model=List[RunOut])
def list_runs(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    agent_id: Optional[int] = None,
    benchmark_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List execution history with optional filtering."""
    stmt = select(Run).order_by(Run.id.desc())
    if status_filter:
        stmt = stmt.where(Run.status == status_filter.upper())
    if agent_id:
        stmt = stmt.where(Run.agent_id == agent_id)
    if benchmark_id:
        stmt = stmt.where(Run.benchmark_id == benchmark_id)

    runs = db.scalars(stmt).all()
    return [
        RunOut(
            id=r.id,
            agent_id=r.agent_id,
            benchmark_id=r.benchmark_id,
            status=r.status,
            created_at=r.created_at,
            finished_at=r.finished_at,
            cancel=r.cancel
        )
        for r in runs
    ]

@router.post("", response_model=RunOut, status_code=status.HTTP_201_CREATED)
def queue_run(
    data: RunIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Queue a new benchmark run for asynchronous execution."""
    agent = db.get(Agent, data.agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Selected Agent not found")

    benchmark = db.get(Benchmark, data.benchmark_id)
    if not benchmark:
        raise HTTPException(status_code=404, detail="Selected Benchmark suite not found")

    task_count = db.scalar(
        select(Task.id).where(Task.benchmark_id == data.benchmark_id).limit(1)
    )
    if task_count is None:
        raise HTTPException(status_code=400, detail="Cannot run a benchmark suite with no tasks")

    run = Run(
        agent_id=data.agent_id,
        benchmark_id=data.benchmark_id,
        status="QUEUED",
        created_at=utc_now_iso(),
        cancel=0
    )
    db.add(run)
    db.flush()

    db.add(AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="run_queued",
        entity_type="benchmark_run",
        entity_id=str(run.id),
        details=json.dumps({"agent": agent.name, "benchmark": benchmark.name})
    ))

    db.commit()
    db.refresh(run)
    return RunOut(
        id=run.id,
        agent_id=run.agent_id,
        benchmark_id=run.benchmark_id,
        status=run.status,
        created_at=run.created_at,
        finished_at=run.finished_at,
        cancel=run.cancel
    )

@router.get("/{run_id}", response_model=RunDetailOut)
def get_run_details(
    run_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get run status and task-level execution records."""
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    task_runs = db.scalars(
        select(TaskRun).where(TaskRun.run_id == run_id).order_by(TaskRun.id)
    ).all()

    return RunDetailOut(
        id=run.id,
        agent_id=run.agent_id,
        benchmark_id=run.benchmark_id,
        status=run.status,
        created_at=run.created_at,
        finished_at=run.finished_at,
        cancel=run.cancel,
        tasks=[
            TaskRunOut(
                id=tr.id,
                run_id=tr.run_id,
                task_id=tr.task_id,
                status=tr.status,
                output=tr.output,
                error=tr.error,
                duration=tr.duration,
                cpu=tr.cpu,
                memory=tr.memory,
                score=tr.score,
                retries=tr.retries
            )
            for tr in task_runs
        ]
    )

@router.post("/{run_id}/cancel", response_model=RunOut)
def cancel_run(
    run_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Signal cancellation for a queued or currently executing run."""
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run.status not in ("QUEUED", "PENDING", "RUNNING"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Run cannot be cancelled because it is already {run.status}"
        )

    run.cancel = 1
    if run.status in ("QUEUED", "PENDING"):
        run.status = "CANCELLED"
        run.finished_at = utc_now_iso()

    db.add(AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="run_cancelled",
        entity_type="benchmark_run",
        entity_id=str(run.id)
    ))
    db.commit()
    db.refresh(run)

    return RunOut(
        id=run.id,
        agent_id=run.agent_id,
        benchmark_id=run.benchmark_id,
        status=run.status,
        created_at=run.created_at,
        finished_at=run.finished_at,
        cancel=run.cancel
    )

