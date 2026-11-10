"""Worker process for executing queued benchmark runs.
Monitors queue, records metrics, enforces timeouts, captures output, and handles recovery.
"""
import os
import sys
import time
import signal
from pathlib import Path

# Add backend directory to path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from config import WORKER_POLL_INTERVAL
from execution.dispatcher import process_one_queued_run, reclaim_stale_runs, execute_single_run
from database import SessionLocal, Session
from models import Run, Agent, Task, TaskRun, utc_now_iso

# Export work_once for testing compatibility
def work_once() -> bool:
    """Execute one pending task; exported for tests and scripts."""
    return process_one_queued_run()

HEARTBEAT_FILE = BACKEND_DIR / ".worker_heartbeat"

def update_heartbeat():
    """Write current timestamp to heartbeat file for system health monitoring."""
    try:
        HEARTBEAT_FILE.write_text(str(time.time()), encoding="utf-8")
    except Exception:
        pass

def main():
    print("AgentBench Worker started (trusted local agents only)", flush=True)
    print(f"Polling interval: {WORKER_POLL_INTERVAL}s. Press Ctrl+C to terminate.", flush=True)

    running = True

    def handle_signal(sig, frame):
        nonlocal running
        print("\nShutdown signal received. Stopping worker cleanly...", flush=True)
        running = False

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    reclaim_stale_runs()

    while running:
        try:
            update_heartbeat()
            executed = process_one_queued_run()
            if not executed:
                time.sleep(WORKER_POLL_INTERVAL)
        except Exception as e:
            print(f"Worker iteration error: {e}", file=sys.stderr, flush=True)
            time.sleep(1.0)

    # Clean up heartbeat file on exit
    if HEARTBEAT_FILE.exists():
        try:
            HEARTBEAT_FILE.unlink(missing_ok=True)
        except Exception:
            pass
    print("Worker stopped.", flush=True)

if __name__ == "__main__":
    main()
