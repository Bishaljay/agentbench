"""Task management and configuration routes."""
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import Task, TaskVersion, Benchmark, AuditLog, User
from schemas import TaskIn, TaskUpdate, TaskOut
from security import get_current_user

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])

VALID_OPERATIONS = [
    "sum", "sort", "transform", "file", "multistep", "format",
    "validate", "recover", "echo", "filter", "aggregate", "regex"
]

@router.get("", response_model=List[TaskOut])
def list_tasks(
    benchmark_id: Optional[int] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all tasks with optional benchmark filter."""
    stmt = select(Task)
    if benchmark_id is not None:
        stmt = stmt.where(Task.benchmark_id == benchmark_id)
    tasks = db.scalars(stmt.order_by(Task.id)).all()
    return [
        TaskOut(
            id=t.id,
            benchmark_id=t.benchmark_id,
            name=t.name,
            category=t.category or "General",
            operation=t.operation,
            input=t.input,
            expected=t.expected,
            timeout=t.timeout,
            difficulty=t.difficulty or "medium",
            memory_limit=t.memory_limit,
            created_at=t.created_at or ""
        )
        for t in tasks
    ]

@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    data: TaskIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new deterministic task definition."""
    if data.operation.lower() not in VALID_OPERATIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported operation. Valid choices: {VALID_OPERATIONS}"
        )

    b = db.get(Benchmark, data.benchmark_id)
    if not b:
        raise HTTPException(status_code=404, detail="Referenced Benchmark suite not found")

    input_str = json.dumps(data.input) if not isinstance(data.input, str) else data.input
    expected_str = json.dumps(data.expected) if not isinstance(data.expected, str) else data.expected

    task = Task(
        benchmark_id=data.benchmark_id,
        name=data.name,
        category=data.category,
        operation=data.operation.lower(),
        input=input_str,
        expected=expected_str,
        timeout=data.timeout,
        difficulty=data.difficulty,
        memory_limit=data.memory_limit
    )
    db.add(task)
    db.flush()

    db.add(TaskVersion(
        task_id=task.id,
        version="1.0.0",
        input=input_str,
        expected=expected_str,
        timeout=data.timeout
    ))

    db.add(AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="task_created",
        entity_type="task",
        entity_id=str(task.id),
        details=json.dumps({"name": task.name, "operation": task.operation})
    ))

    db.commit()
    db.refresh(task)
    return TaskOut(
        id=task.id,
        benchmark_id=task.benchmark_id,
        name=task.name,
        category=task.category or "General",
        operation=task.operation,
        input=task.input,
        expected=task.expected,
        timeout=task.timeout,
        difficulty=task.difficulty or "medium",
        memory_limit=task.memory_limit,
        created_at=task.created_at or ""
    )

@router.get("/{task_id}", response_model=TaskOut)
def get_task_details(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get single task definition."""
    t = db.get(Task, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskOut(
        id=t.id,
        benchmark_id=t.benchmark_id,
        name=t.name,
        category=t.category or "General",
        operation=t.operation,
        input=t.input,
        expected=t.expected,
        timeout=t.timeout,
        difficulty=t.difficulty or "medium",
        memory_limit=t.memory_limit,
        created_at=t.created_at or ""
    )

@router.put("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update task configuration."""
    t = db.get(Task, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")

    if data.name is not None:
        t.name = data.name
    if data.category is not None:
        t.category = data.category
    if data.operation is not None:
        if data.operation.lower() not in VALID_OPERATIONS:
            raise HTTPException(status_code=400, detail="Invalid operation")
        t.operation = data.operation.lower()
    if data.input is not None:
        t.input = json.dumps(data.input) if not isinstance(data.input, str) else data.input
    if data.expected is not None:
        t.expected = json.dumps(data.expected) if not isinstance(data.expected, str) else data.expected
    if data.timeout is not None:
        t.timeout = data.timeout
    if data.difficulty is not None:
        t.difficulty = data.difficulty
    if data.memory_limit is not None:
        t.memory_limit = data.memory_limit

    db.add(AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="task_updated",
        entity_type="task",
        entity_id=str(t.id)
    ))
    db.commit()
    db.refresh(t)
    return TaskOut(
        id=t.id,
        benchmark_id=t.benchmark_id,
        name=t.name,
        category=t.category or "General",
        operation=t.operation,
        input=t.input,
        expected=t.expected,
        timeout=t.timeout,
        difficulty=t.difficulty or "medium",
        memory_limit=t.memory_limit,
        created_at=t.created_at or ""
    )

@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a task."""
    t = db.get(Task, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")

    name = t.name
    db.delete(t)
    db.add(AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="task_deleted",
        entity_type="task",
        entity_id=str(task_id),
        details=json.dumps({"name": name})
    ))
    db.commit()
    return {"message": f"Task '{name}' deleted"}

