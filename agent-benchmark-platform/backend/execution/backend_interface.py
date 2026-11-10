"""Execution Backend Interface for agent task dispatch."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable
from pydantic import BaseModel, Field

class ExecutionOutput(BaseModel):
    """Result of low-level backend execution."""
    status: str  # 'COMPLETED', 'FAILED', 'TIMEOUT', 'CANCELLED'
    stdout: str = ""
    stderr: str = ""
    return_code: int = 0
    duration: float = 0.0
    cpu_seconds: float = 0.0
    peak_memory_bytes: int = 0
    raw_result: Optional[Dict[str, Any]] = None

class ExecutionBackend(ABC):
    """Abstract execution backend for future container/sandbox integration."""

    @abstractmethod
    def execute(
        self,
        kind: str,
        operation: str,
        input_data: Any,
        timeout: float,
        cancel_check: Optional[Callable[[], bool]] = None,
        memory_limit: Optional[int] = None
    ) -> ExecutionOutput:
        """Execute a task and return low-level execution metrics and output."""
        pass

