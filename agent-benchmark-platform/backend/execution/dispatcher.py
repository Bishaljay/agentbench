"""Benchmark Run Dispatcher and Execution Orchestrator."""
import json
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from database import SessionLocal
from models import (
    Run, TaskRun, Agent, Benchmark, Task, EvaluationResult,
    Artifact, Notification, AuditLog, utc_now_iso
)
from execution.local_backend import LocalSubprocessBackend
from evaluation.evaluator import evaluate_task_execution

logger = logging.getLogger("agentbench.dispatcher")

backend_executor = LocalSubprocessBackend()

def execute_single_run(run_id: int) -> bool:
    """Execute a single queued or pending benchmark run."""
    with SessionLocal() as db:
        run = db.get(Run, run_id)
        if not run or run.status not in ("QUEUED", "PENDING"):
            return False

        # Transition to RUNNING
        run.status = "RUNNING"
        db.commit()

        agent = db.get(Agent, run.agent_id)
        benchmark = db.get(Benchmark, run.benchmark_id)
        if not agent or not benchmark:
            run.status = "FAILED"
            run.finished_at = utc_now_iso()
            db.commit()
            return False

        tasks = db.scalars(
            select(Task).where(Task.benchmark_id == run.benchmark_id).order_by(Task.id)
        ).all()
        kind = agent.kind

    task_results = []
    run_cancelled = False

    for task in tasks:
        # Check cancellation before starting task
        with SessionLocal() as db:
            current_run = db.get(Run, run_id)
            if current_run and current_run.cancel:
                run_cancelled = True
                break

        def cancel_check() -> bool:
            with SessionLocal() as s:
                r = s.get(Run, run_id)
                return bool(r and r.cancel)

        try:
            task_input = json.loads(task.input)
        except Exception:
            task_input = task.input

        try:
            expected_val = json.loads(task.expected)
        except Exception:
            expected_val = task.expected

        # Low-level execution
        exec_out = backend_executor.execute(
            kind=kind,
            operation=task.operation,
            input_data=task_input,
            timeout=task.timeout,
            cancel_check=cancel_check,
            memory_limit=task.memory_limit
        )

        if exec_out.status == "CANCELLED":
            run_cancelled = True

        # High-level evaluation
        eval_outcome = evaluate_task_execution(
            expected_value=expected_val,
            exec_status=exec_out.status,
            raw_result=exec_out.raw_result,
            stderr_data=exec_out.stderr
        )

        # Final task run status
        if exec_out.status == "CANCELLED":
            final_status = "CANCELLED"
        elif exec_out.status == "TIMEOUT":
            final_status = "TIMEOUT"
        elif eval_outcome.passed:
            final_status = "COMPLETED"
        else:
            final_status = "FAILED"

        # Persist task execution and evaluation results
        with SessionLocal() as db:
            task_run = TaskRun(
                run_id=run_id,
                task_id=task.id,
                status=final_status,
                output=exec_out.stdout[:100000],
                error=(eval_outcome.error_reason or exec_out.stderr)[:100000],
                duration=exec_out.duration,
                cpu=exec_out.cpu_seconds,
                memory=exec_out.peak_memory_bytes,
                score=eval_outcome.score,
                retries=eval_outcome.retries
            )
            db.add(task_run)
            db.flush()

            # Record granular evaluation results
            for metric in eval_outcome.breakdown:
                db.add(EvaluationResult(
                    task_run_id=task_run.id,
                    metric_name=metric.get("metric", "general"),
                    score=float(metric.get("score", 0.0)),
                    passed=bool(metric.get("passed", False)),
                    details=json.dumps(metric)
                ))

            # Store artifact metadata
            db.add(Artifact(
                run_id=run_id,
                task_run_id=task_run.id,
                name=f"task-{task.id}-output.json",
                file_path=f"runs/{run_id}/tasks/{task.id}.json",
                mime_type="application/json",
                size_bytes=len(exec_out.stdout.encode("utf-8"))
            ))

            db.commit()
            task_results.append(final_status)

        if run_cancelled:
            break

    # Determine final benchmark run status
    with SessionLocal() as db:
        final_run = db.get(Run, run_id)
        if final_run:
            if run_cancelled or final_run.cancel:
                final_run.status = "CANCELLED"
            elif any(s == "TIMEOUT" for s in task_results):
                final_run.status = "FAILED"
            elif task_results and all(s == "COMPLETED" for s in task_results):
                final_run.status = "COMPLETED"
            else:
                final_run.status = "FAILED"

            final_run.finished_at = utc_now_iso()

            # Log audit entry
            db.add(AuditLog(
                username="worker",
                action="benchmark_run_completed",
                entity_type="benchmark_run",
                entity_id=str(run_id),
                details=json.dumps({"status": final_run.status, "tasks": len(task_results)})
            ))
            db.commit()

    return True

def reclaim_stale_runs():
    """Recover from worker crashes: mark long-stuck RUNNING runs as FAILED."""
    with SessionLocal() as db:
        stale_runs = db.scalars(
            select(Run).where(Run.status == "RUNNING")
        ).all()
        for r in stale_runs:
            # Check elapsed time
            try:
                started = datetime.fromisoformat(r.created_at)
                elapsed = (datetime.now(timezone.utc) - started).total_seconds()
                if elapsed > 300:  # 5 minutes stale
                    r.status = "FAILED"
                    r.finished_at = utc_now_iso()
                    logger.warning(f"Reclaimed stale run #{r.id} (status set to FAILED)")
            except Exception:
                pass
        db.commit()

def process_one_queued_run() -> bool:
    """Find and execute the next queued or pending run."""
    with SessionLocal() as db:
        rid = db.scalar(
            select(Run.id)
            .where(Run.status.in_(["PENDING", "QUEUED"]))
            .order_by(Run.id)
            .limit(1)
        )
    if rid is None:
        return False
    return execute_single_run(rid)

