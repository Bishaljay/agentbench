"""Local Subprocess Execution Backend with process-tree cleanup and resource monitoring."""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Optional
import psutil

from execution.backend_interface import ExecutionBackend, ExecutionOutput

BACKEND_DIR = Path(__file__).resolve().parents[1]
RUNTIME_SCRIPT = str(BACKEND_DIR / "agent_runtime.py")

class LocalSubprocessBackend(ExecutionBackend):
    """Executes trusted built-in agents in isolated child processes with resource tracking."""

    def __init__(self, python_executable: Optional[str] = None):
        self.python_executable = python_executable or sys.executable

    def _terminate_tree(self, pid: int):
        """Recursively terminate a process and all its spawned children on Windows/Unix."""
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            for child in children:
                try:
                    child.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            parent.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    def execute(
        self,
        kind: str,
        operation: str,
        input_data: Any,
        timeout: float,
        cancel_check: Optional[Callable[[], bool]] = None,
        memory_limit: Optional[int] = None
    ) -> ExecutionOutput:
        start_time = time.monotonic()
        peak_memory = 0
        cpu_time = 0.0
        cancelled = False
        timed_out = False

        # Sanitized minimal environment (excluding platform secrets)
        safe_env = {
            "PATH": os.environ.get("PATH", os.defpath),
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"),
            "PYTHONIOENCODING": "utf-8",
            "PYTHONPATH": str(BACKEND_DIR),
        }

        with tempfile.TemporaryDirectory(prefix="agent-bench-task-") as tmpdir:
            payload = json.dumps({
                "kind": kind,
                "operation": operation,
                "input": input_data,
                "timeout": timeout
            })

            proc = subprocess.Popen(
                [self.python_executable, RUNTIME_SCRIPT],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=tmpdir,
                env=safe_env,
                text=True
            )

            # Send payload and close stdin
            try:
                proc.stdin.write(payload)
                proc.stdin.close()
                proc.stdin = None
            except (BrokenPipeError, OSError):
                pass

            # Monitor process resources and timeout
            try:
                p_mon = psutil.Process(proc.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                p_mon = None

            while proc.poll() is None:
                if p_mon:
                    try:
                        mem_info = p_mon.memory_info()
                        peak_memory = max(peak_memory, mem_info.rss)
                        cpu_times = p_mon.cpu_times()
                        cpu_time = max(cpu_time, cpu_times.user + cpu_times.system)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                # Check external cancellation
                if cancel_check and cancel_check():
                    cancelled = True
                    self._terminate_tree(proc.pid)
                    break

                # Check timeout enforcement
                elapsed = time.monotonic() - start_time
                if elapsed > timeout:
                    timed_out = True
                    self._terminate_tree(proc.pid)
                    break

                time.sleep(0.02)

            stdout_data, stderr_data = proc.communicate()
            duration = time.monotonic() - start_time

        # Determine execution status
        if cancelled:
            status = "CANCELLED"
            stderr_data = stderr_data or "Task was cancelled by user request"
        elif timed_out:
            status = "TIMEOUT"
            stderr_data = stderr_data or f"Execution exceeded task timeout of {timeout}s"
        elif proc.returncode != 0:
            status = "FAILED"
        else:
            status = "COMPLETED"

        raw_result = None
        if status == "COMPLETED" and stdout_data:
            try:
                raw_result = json.loads(stdout_data.strip())
            except Exception:
                status = "FAILED"
                stderr_data = (stderr_data or "") + "\nInvalid JSON output from agent"

        return ExecutionOutput(
            status=status,
            stdout=stdout_data or "",
            stderr=stderr_data or "",
            return_code=proc.returncode if proc.returncode is not None else -1,
            duration=round(duration, 4),
            cpu_seconds=round(cpu_time, 4),
            peak_memory_bytes=peak_memory,
            raw_result=raw_result
        )

