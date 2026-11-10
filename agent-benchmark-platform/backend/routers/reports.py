"""Report generation and export routes (CSV and JSON)."""
import csv
import io
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import Run, TaskRun, Agent, Benchmark, Task, User
from security import get_current_user
from evaluation.evaluator import calculate_statistical_metrics

router = APIRouter(prefix="/api/reports", tags=["Reports"])

@router.get("/{run_id}/{format}")
def export_run_report(
    run_id: int,
    format: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export a single benchmark run in JSON or CSV format."""
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    agent = db.get(Agent, run.agent_id)
    benchmark = db.get(Benchmark, run.benchmark_id)
    task_runs = db.scalars(
        select(TaskRun).where(TaskRun.run_id == run_id).order_by(TaskRun.id)
    ).all()

    data = {
        "id": run.id,
        "agent_id": run.agent_id,
        "agent_name": agent.name if agent else f"Agent {run.agent_id}",
        "benchmark_id": run.benchmark_id,
        "benchmark_name": benchmark.name if benchmark else f"Suite {run.benchmark_id}",
        "status": run.status,
        "created_at": run.created_at,
        "finished_at": run.finished_at,
        "tasks": [
            {
                "id": t.id,
                "task_id": t.task_id,
                "status": t.status,
                "output": t.output,
                "error": t.error,
                "duration": t.duration,
                "cpu": t.cpu,
                "memory": t.memory,
                "score": t.score,
                "retries": t.retries
            }
            for t in task_runs
        ]
    }

    if format.lower() == "json":
        json_bytes = json.dumps(data, indent=2).encode("utf-8")
        return StreamingResponse(
            io.BytesIO(json_bytes),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="run-{run_id}.json"'}
        )

    if format.lower() == "csv":
        output = io.StringIO()
        fieldnames = [
            "run_id", "agent_name", "benchmark_name", "task_id",
            "status", "output", "error", "duration", "cpu", "memory", "score", "retries"
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for t in data["tasks"]:
            writer.writerow({
                "run_id": run_id,
                "agent_name": data["agent_name"],
                "benchmark_name": data["benchmark_name"],
                "task_id": t["task_id"],
                "status": t["status"],
                "output": t["output"],
                "error": t["error"],
                "duration": t["duration"],
                "cpu": t["cpu"],
                "memory": t["memory"],
                "score": t["score"],
                "retries": t["retries"]
            })
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="run-{run_id}.csv"'}
        )

    raise HTTPException(status_code=400, detail="Format must be 'json' or 'csv'")

@router.get("/agent/{agent_id}/{format}")
def export_agent_report(
    agent_id: int,
    format: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export aggregated performance report for a single agent across all runs."""
    agent = db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    runs = db.scalars(select(Run).where(Run.agent_id == agent_id)).all()
    run_ids = [r.id for r in runs]
    task_runs = db.scalars(select(TaskRun).where(TaskRun.run_id.in_(run_ids))).all() if run_ids else []

    metrics = calculate_statistical_metrics(task_runs)
    report_data = {
        "agent": {
            "id": agent.id,
            "name": agent.name,
            "kind": agent.kind,
            "version": agent.version
        },
        "total_runs": len(runs),
        "metrics": metrics
    }

    if format.lower() == "json":
        return StreamingResponse(
            io.BytesIO(json.dumps(report_data, indent=2).encode("utf-8")),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="agent-{agent_id}-report.json"'}
        )

    if format.lower() == "csv":
        output = io.StringIO()
        fieldnames = ["metric", "value"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({"metric": "agent_name", "value": agent.name})
        writer.writerow({"metric": "agent_kind", "value": agent.kind})
        writer.writerow({"metric": "total_runs", "value": len(runs)})
        for k, v in metrics.items():
            writer.writerow({"metric": k, "value": v})

        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="agent-{agent_id}-report.csv"'}
        )

    raise HTTPException(status_code=400, detail="Format must be 'json' or 'csv'")

@router.get("/comparison/{format}")
def export_comparison_report(
    format: str,
    agent_ids: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export comparison report across all or selected agents."""
    agents_query = select(Agent)
    if agent_ids:
        ids = [int(i.strip()) for i in agent_ids.split(",") if i.strip().isdigit()]
        if ids:
            agents_query = agents_query.where(Agent.id.in_(ids))
    agents = db.scalars(agents_query).all()

    runs = db.scalars(select(Run)).all()
    task_runs = db.scalars(select(TaskRun)).all()

    comparison_rows = []
    for a in agents:
        a_rids = {r.id for r in runs if r.agent_id == a.id}
        a_trs = [t for t in task_runs if t.run_id in a_rids]
        m = calculate_statistical_metrics(a_trs)
        comparison_rows.append({
            "agent_id": a.id,
            "name": a.name,
            "kind": a.kind,
            "version": a.version,
            **m
        })

    if format.lower() == "json":
        return StreamingResponse(
            io.BytesIO(json.dumps(comparison_rows, indent=2).encode("utf-8")),
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="agent-comparison.json"'}
        )

    if format.lower() == "csv":
        output = io.StringIO()
        fieldnames = [
            "agent_id", "name", "kind", "version", "tasks", "score",
            "success_rate", "failure_rate", "avg_duration", "median",
            "p95", "memory", "cpu", "timeouts", "recoveries"
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for r in comparison_rows:
            writer.writerow({k: r.get(k, "") for k in fieldnames})
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="agent-comparison.csv"'}
        )

    raise HTTPException(status_code=400, detail="Format must be 'json' or 'csv'")

