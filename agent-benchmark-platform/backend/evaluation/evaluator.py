"""Evaluation Engine for evaluating agent outputs and computing statistical metrics."""
import math
import statistics
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class EvaluationOutcome(BaseModel):
    """Result of evaluating a single task execution against its expectation."""
    score: float = 0.0
    passed: bool = False
    retries: int = 0
    error_reason: str = ""
    breakdown: List[Dict[str, Any]] = Field(default_factory=list)

def _compute_partial_match(actual: Any, expected: Any) -> float:
    """Calculate partial similarity score for dicts and lists."""
    if actual == expected:
        return 1.0
    if actual is None or expected is None:
        return 0.0
    if isinstance(expected, dict) and isinstance(actual, dict):
        if not expected:
            return 1.0 if not actual else 0.0
        matches = 0
        for k, v in expected.items():
            if k in actual and actual[k] == v:
                matches += 1
        return round(matches / len(expected), 3)
    if isinstance(expected, list) and isinstance(actual, list):
        if not expected:
            return 1.0 if not actual else 0.0
        s_exp = set(str(x) for x in expected)
        s_act = set(str(x) for x in actual)
        intersection = s_exp.intersection(s_act)
        union = s_exp.union(s_act)
        return round(len(intersection) / len(union), 3) if union else 0.0
    return 0.0

def evaluate_task_execution(
    expected_value: Any,
    exec_status: str,
    raw_result: Optional[Dict[str, Any]],
    stderr_data: str
) -> EvaluationOutcome:
    """Evaluate task output against expected value and categorize results."""
    # 1. Non-completion states
    if exec_status == "TIMEOUT":
        return EvaluationOutcome(
            score=0.0,
            passed=False,
            error_reason="Execution exceeded task timeout",
            breakdown=[{"metric": "timeout", "score": 0.0, "passed": False}]
        )
    if exec_status == "CANCELLED":
        return EvaluationOutcome(
            score=0.0,
            passed=False,
            error_reason="Task cancelled before completion",
            breakdown=[{"metric": "cancellation", "score": 0.0, "passed": False}]
        )
    if exec_status != "COMPLETED" or raw_result is None:
        return EvaluationOutcome(
            score=0.0,
            passed=False,
            error_reason=stderr_data or "Agent failed with non-zero exit code",
            breakdown=[{"metric": "execution_success", "score": 0.0, "passed": False}]
        )

    # 2. Extract agent result fields
    agent_status = raw_result.get("status")
    output = raw_result.get("output")
    metadata = raw_result.get("metadata", {})
    retries = int(metadata.get("retries", 0))

    if agent_status != "success":
        return EvaluationOutcome(
            score=0.0,
            passed=False,
            retries=retries,
            error_reason=raw_result.get("error") or "Agent reported error status",
            breakdown=[{"metric": "status_check", "score": 0.0, "passed": False}]
        )

    # 3. Output comparison (exact vs partial)
    if output == expected_value:
        return EvaluationOutcome(
            score=1.0,
            passed=True,
            retries=retries,
            error_reason="",
            breakdown=[
                {"metric": "exact_match", "score": 1.0, "passed": True},
                {"metric": "schema_conformance", "score": 1.0, "passed": True}
            ]
        )

    # Numeric tolerance check
    if isinstance(expected_value, (int, float)) and isinstance(output, (int, float)):
        if abs(expected_value - output) < 1e-6:
            return EvaluationOutcome(
                score=1.0,
                passed=True,
                retries=retries,
                error_reason="",
                breakdown=[{"metric": "numeric_tolerance", "score": 1.0, "passed": True}]
            )

    # Partial credit check for structured types
    partial_score = _compute_partial_match(output, expected_value)
    if partial_score > 0.0:
        return EvaluationOutcome(
            score=partial_score,
            passed=False,
            retries=retries,
            error_reason=f"Partial output match ({int(partial_score * 100)}%)",
            breakdown=[{"metric": "partial_match", "score": partial_score, "passed": False}]
        )

    return EvaluationOutcome(
        score=0.0,
        passed=False,
        retries=retries,
        error_reason=f"Output mismatch: expected {expected_value}, got {output}",
        breakdown=[{"metric": "output_equality", "score": 0.0, "passed": False}]
    )

def calculate_statistical_metrics(task_runs: List[Any]) -> Dict[str, Any]:
    """Compute verified aggregate statistics from genuine persisted TaskRun objects."""
    if not task_runs:
        return {
            "tasks": 0,
            "score": 0.0,
            "success_rate": 0.0,
            "failure_rate": 0.0,
            "timeout_rate": 0.0,
            "recovery_rate": 0.0,
            "avg_duration": 0.0,
            "median": 0.0,
            "p95": 0.0,
            "memory": 0.0,
            "cpu": 0.0,
            "timeouts": 0,
            "recoveries": 0
        }

    total = len(task_runs)
    completed = sum(1 for t in task_runs if t.status == "COMPLETED")
    failed = sum(1 for t in task_runs if t.status == "FAILED")
    timeouts = sum(1 for t in task_runs if t.status == "TIMEOUT")
    recoveries = sum(1 for t in task_runs if getattr(t, "retries", 0) > 0 and t.status == "COMPLETED")

    durations = sorted(t.duration for t in task_runs)
    avg_duration = round(statistics.mean(durations), 3) if durations else 0.0
    median_duration = round(statistics.median(durations), 3) if durations else 0.0
    
    # Nearest rank percentile for P95
    p95_index = math.ceil(0.95 * total) - 1
    p95_duration = round(durations[max(0, min(p95_index, total - 1))], 3)

    avg_memory_mb = round(statistics.mean(t.memory for t in task_runs) / 1048576, 2)
    avg_cpu_seconds = round(statistics.mean(t.cpu for t in task_runs), 3)

    scores = [t.score for t in task_runs]
    avg_score = round(statistics.mean(scores) * 100, 1) if scores else 0.0

    return {
        "tasks": total,
        "score": avg_score,
        "success_rate": round((completed / total) * 100, 1),
        "failure_rate": round((failed / total) * 100, 1),
        "timeout_rate": round((timeouts / total) * 100, 1),
        "recovery_rate": round((recoveries / total) * 100, 1),
        "avg_duration": avg_duration,
        "median": median_duration,
        "p95": p95_duration,
        "memory": avg_memory_mb,
        "cpu": avg_cpu_seconds,
        "timeouts": timeouts,
        "recoveries": recoveries
    }

