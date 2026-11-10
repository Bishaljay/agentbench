"""Analytics, metrics, and agent comparison routes."""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import Agent, Benchmark, Run, TaskRun, User
from schemas import AnalyticsSummary, LeaderboardEntry
from security import get_current_user
from evaluation.evaluator import calculate_statistical_metrics

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("", response_model=AnalyticsSummary)
def get_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate platform-wide statistical aggregates and agent rankings from genuine execution records."""
    agents = db.scalars(select(Agent)).all()
    benchmarks = db.scalars(select(Benchmark)).all()
    runs = db.scalars(select(Run)).all()
    task_runs = db.scalars(select(TaskRun)).all()

    leaderboard: List[LeaderboardEntry] = []
    
    for agent in agents:
        agent_runs = {r.id for r in runs if r.agent_id == agent.id}
        agent_task_runs = [tr for tr in task_runs if tr.run_id in agent_runs]
        if not agent_task_runs:
            continue

        stats = calculate_statistical_metrics(agent_task_runs)
        leaderboard.append(
            LeaderboardEntry(
                agent_id=agent.id,
                name=agent.name,
                kind=agent.kind,
                tasks=stats["tasks"],
                success_rate=stats["success_rate"],
                score=stats["score"],
                avg_duration=stats["avg_duration"],
                median=stats["median"],
                p95=stats["p95"],
                memory=stats["memory"],
                cpu=stats["cpu"],
                timeouts=stats["timeouts"],
                recoveries=stats["recoveries"]
            )
        )

    # Sort leaderboard by score descending, success rate descending, avg duration ascending
    leaderboard.sort(key=lambda x: (-x.score, -x.success_rate, x.avg_duration))

    overall = calculate_statistical_metrics(task_runs)

    return AnalyticsSummary(
        agents=len(agents),
        benchmarks=len(benchmarks),
        runs=len(runs),
        completed=sum(1 for r in runs if r.status == "COMPLETED"),
        failed=sum(1 for r in runs if r.status in ("FAILED", "TIMEOUT")),
        avg_duration=overall["avg_duration"],
        avg_memory=overall["memory"],
        leaderboard=leaderboard
    )

@router.get("/compare")
def compare_agents(
    agent_ids: str = Query(..., description="Comma-separated agent IDs, e.g. 1,2,3"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Compare multiple agents side-by-side using real task-level metrics."""
    id_list = []
    for raw_id in agent_ids.split(","):
        raw_id = raw_id.strip()
        if raw_id.isdigit():
            id_list.append(int(raw_id))

    agents = db.scalars(select(Agent).where(Agent.id.in_(id_list))).all()
    runs = db.scalars(select(Run).where(Run.agent_id.in_(id_list))).all()
    run_ids = {r.id for r in runs}
    task_runs = db.scalars(select(TaskRun).where(TaskRun.run_id.in_(run_ids))).all()

    comparison = []
    for a in agents:
        a_run_ids = {r.id for r in runs if r.agent_id == a.id}
        a_trs = [tr for tr in task_runs if tr.run_id in a_run_ids]
        metrics = calculate_statistical_metrics(a_trs)
        comparison.append({
            "agent_id": a.id,
            "name": a.name,
            "kind": a.kind,
            "version": a.version,
            **metrics
        })

    return {"agents": comparison}

