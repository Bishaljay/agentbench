# AgentBench — local benchmarking prototype

A functional **prototype**, not a production-ready platform. It executes five deterministic scripted agent variants without an LLM, keys, Docker, or paid services. The browser talks to a FastAPI API, a separate polling worker executes agents in subprocesses, and SQLite stores the results. The sample agents are scripts, not reasoning models.

## Run locally

Requires Python 3.10+ and Node 20+. From this directory:

```sh
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows instead: .venv\Scripts\activate
pip install -r backend/requirements.txt
cd frontend && npm ci && cd ..
```

Use three terminals (activate the virtual environment in each Python terminal):

```sh
cd backend && uvicorn main:app --host 127.0.0.1 --port 8000
```
```sh
cd backend && python worker.py
```
```sh
cd frontend && npm run dev
```

Open http://localhost:5173, create an account, and sign in. Select **Run benchmark**, pick an agent and suite, and start the run. Execution history refreshes every four seconds; click Details to inspect task results. Download reports from Reports. API documentation is at http://localhost:8000/docs. SQLite is created at `storage/benchmark.db`; it persists across restarts. Back it up while the processes are stopped.

## Verify

```sh
cd backend && pytest -q
cd ../frontend && npm run build
```

## Methodology

Each task produces a JSON result. Exact equality of the returned `output` and expected JSON, plus success status, yields score 1; otherwise score 0. Agent score and success rate are means over persisted task results. Leaderboard sorts by score, success rate, then average time. Duration is wall-clock subprocess time. CPU is sampled process CPU seconds; memory is sampled peak RSS, so fast processes may be undercounted. P95 is the nearest-rank percentile. Recovery counts successful task results with reported retries; the recovery script triggers and catches one controlled transient error. Token usage is N/A. Failed and timed-out attempts count as score zero. Run status is completed only if all tasks succeed; a timed-out task makes the run failed. No synthetic benchmark results are seeded.

## Safety and limitations

Native subprocesses are **not a security sandbox**. The runtime only accepts a built-in allowlist; do not run untrusted code, expose this service to the public, or put secrets in the environment. The subprocess uses a temporary working directory and a minimal environment, but can still access the filesystem and network with the user's privileges. Timeout kills the direct child, not an arbitrary process tree. No OS resource limits are enforced. Use a single worker: multi-worker crash recovery and stale-running reclamation are not implemented. A worker crash can leave a run RUNNING. There is no authentication token expiry, rate limiting, RBAC or secure password reset. Do not use this prototype for sensitive or production deployments.

See DEVELOPMENT_STATUS.md and TASK_CHECKLIST.md for detailed gaps. Database schema is created with SQLAlchemy `create_all`; Alembic migrations are not yet implemented. The prototype does not yet provide the full SDK, all requested task types, extensive filtering, versioning, or administrative controls.
