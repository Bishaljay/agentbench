# Project Audit: AI Agent Benchmarking Platform

**Date:** 2026-11-09  
**Platform:** Windows 11 / Local SQLite Environment  
**Tools Detected:** Python 3.14.2, Node.js v25.4.0, npm 10.8.1, Git 2.45.1  
**Project Path:** `c:\Users\bjbis\Downloads\agent\agent-benchmark-platform`

---

## 1. Executive Summary

The existing project is a lightweight proof-of-concept prototype ("AgentBench") designed to demonstrate basic benchmark execution of 5 deterministic Python scripts against 3 predefined benchmark suites with SQLite persistence and a React/TypeScript web UI.

While the fundamental end-to-end loop (register, run, worker poll, evaluate exact match, report download) functions in a minimal test, the codebase is currently structured as an early-stage prototype:
1. **Monolithic Architecture**: The backend resides almost entirely in a single file (`backend/main.py`), with runtime in `backend/agent_runtime.py` and worker in `backend/worker.py`. The frontend is condensed entirely into a single file (`frontend/src/main.tsx`).
2. **Missing Database Architecture**: No Alembic migrations exist. Tables are initialized via SQLAlchemy `create_all()`. Many critical enterprise and operational models are absent (e.g. Roles, Agent Versions, Task Versions, Audit Logs, Notifications, System Settings, Artifacts).
3. **Incomplete Pages & UI Gaps**: Out of the 21 required pages, several are missing (Agent Details, Benchmark Details, Task Editor, Live Execution, Notifications, Administration, System Health), and three pages (`Comparison`, `Leaderboard`, `Analytics`) share identical code. Data tables lack pagination, search, and sorting.
4. **Missing Python SDK**: There is no standalone agent SDK package; agent execution relies on hardcoded string branches in `agent_runtime.py`.
5. **Execution & Evaluation Gaps**: The execution lifecycle is missing the `PENDING` state; timeout kills only the direct PID without process tree isolation; evaluation is limited to strict binary equality without schema or partial credit evaluation.
6. **No Frontend Tests**: Vitest is in `package.json`, but no frontend test files exist.

---

## 2. 20-Point Project Inspection

### 1. Frontend Framework & Dependencies
- **Framework**: React 18.3.0, TypeScript 5.7.0, Vite 6.1.0.
- **UI Libraries**: `lucide-react` 0.468.0, `recharts` 2.15.0.
- **Testing**: `vitest` 2.1.0 in `devDependencies` (no test specs written).
- **Status**: Code exists in `frontend/src/main.tsx` (31 lines, minified/crammed style). Dependencies in `package.json` are not yet installed (`node_modules` missing).

### 2. Backend Framework & Dependencies
- **Framework**: FastAPI (>=0.115,<1) with Uvicorn (>=0.30,<1).
- **ORM & Validation**: SQLAlchemy 2.0 (`sqlalchemy>=2,<3`), Pydantic v2 (`pydantic>=2,<3`).
- **Utilities**: `psutil>=6,<8`, `httpx>=0.27,<1`, `pytest>=8,<10`.
- **Status**: Virtual environment `.venv` is not yet configured. `alembic` is missing from `requirements.txt`.

### 3. Database Configuration
- **Database**: SQLite (`storage/benchmark.db`), controlled via `BENCHMARK_DB` environment variable.
- **Connection**: SQLite connection with `check_same_thread=False` and `PRAGMA foreign_keys=ON` listener.
- **Status**: Database file exists with 2 pre-existing user records (`rm@gmail.com`, `abc@gmail.com`), 5 agents, 3 benchmarks, 9 tasks.

### 4. Database Models
- **Existing Models** (`main.py`):
  - `User`: id, username, password, token.
  - `Agent`: id, name, kind, version, capabilities.
  - `Benchmark`: id, name, description, category.
  - `Task`: id, benchmark_id, name, category, operation, input, expected, timeout.
  - `Run`: id, agent_id, benchmark_id, status, created_at, finished_at, cancel.
  - `TaskRun`: id, run_id, task_id, status, output, error, duration, cpu, memory, score, retries.
- **Missing Models Required**:
  - `Role` / User RBAC roles (admin, operator, viewer).
  - `AgentVersion` (version tracking, changelog, code hash).
  - `AgentCapability` (tagging and capability matrix).
  - `BenchmarkVersion` (suite revisioning).
  - `TaskVersion` (task input/expected schema revisioning).
  - `EvaluationResult` (fine-grained metric breakdown per task run).
  - `Artifact` (execution logs, output files, debug dumps).
  - `Notification` (run completion, failure alerts, system alerts).
  - `AuditLog` (administrative and security audit trail).
  - `SystemSetting` (environment parameters, timeouts, worker configuration).

### 5. Database Migrations
- **Status**: **Missing**. Currently uses `Base.metadata.create_all(engine)` inside `init()`.
- **Requirement**: Full Alembic setup (`alembic.ini`, migration versions) with non-destructive initial migration preserving existing SQLite data.

### 6. Authentication Implementation
- **Existing**:
  - `POST /api/auth/register`: Hashes password using PBKDF2 HMAC-SHA256 (200,000 iterations, 16-byte random salt).
  - `POST /api/auth/login`: Validates password hash via `hmac.compare_digest` and sets `user.token` (secrets.token_urlsafe).
  - Dependency `auth()` checks `Authorization: Bearer <token>`.
- **Missing / Vulnerabilities**:
  - No `POST /api/auth/logout` endpoint to invalidate session tokens.
  - Tokens have no expiration (never expire).
  - Stored in a single column `token` on `User`, allowing only 1 active session.
  - No RBAC or role checking on sensitive endpoints.
  - No user profile endpoint (`GET /api/auth/me`).
  - No documented local administrator bootstrap mechanism.

### 7. Agent Registry
- **Existing**: `GET /api/agents`, `POST /api/agents` (restricting `kind` to 5 hardcoded strings).
- **Missing**:
  - `GET /api/agents/{id}` (Agent details).
  - `PUT /api/agents/{id}` (Update agent).
  - `DELETE /api/agents/{id}` (Delete agent).
  - Version management and capability tagging.
  - Agent validation API.

### 8. Agent SDK
- **Status**: **Missing**.
- **Existing**: Hardcoded script `backend/agent_runtime.py` checking if `op == 'sum'`, `'sort'`, etc.
- **Requirement**: A proper Python SDK module (`agent_sdk`) providing an abstract `BaseAgent`, standardized `TaskContext`, `AgentResult`, schema validation, and CLI/runner interface.

### 9. Benchmark Management
- **Existing**: `GET /api/benchmarks`, `POST /api/benchmarks`.
- **Missing**:
  - `GET /api/benchmarks/{id}` (Detailed view with tasks).
  - `PUT /api/benchmarks/{id}` (Update).
  - `DELETE /api/benchmarks/{id}` (Delete with cascading checks).
  - Suite versioning and categorization.

### 10. Task Management
- **Existing**: `GET /api/tasks`, `POST /api/tasks` (accepts 9 operation types).
- **Missing**:
  - `GET /api/tasks/{id}`, `PUT /api/tasks/{id}`, `DELETE /api/tasks/{id}`.
  - Input/output schema validation beyond basic JSON parse.
  - Support for resource limit definitions (memory limit, max CPU).
  - Expanded task operations catalog across diverse cognitive/workflow categories.

### 11. Execution Engine
- **Existing**: `backend/worker.py` polling SQLite every second for `status == 'QUEUED'`.
- **Gaps**:
  - Missing required lifecycle states: `PENDING` -> `QUEUED` -> `RUNNING` -> `COMPLETED`/`FAILED`/`TIMEOUT`/`CANCELLED`.
  - Subprocess cancellation kills only direct child (`p.kill()`), which on Windows does not terminate orphaned child processes in a tree.
  - No heartbeat mechanism; if worker crashes while running, runs remain permanently in `RUNNING`.
  - No modular backend interface (e.g. `ExecutionBackend` protocol).

### 12. Evaluation Engine
- **Existing**: Binary exact equality check (`output == json.loads(t['expected'])`).
- **Gaps**:
  - No partial scoring support (e.g., set overlap, fuzzy text similarity, schema conformance).
  - No evaluation criteria options (numeric tolerance, regex match, key/value subset).
  - No structured error classification (SyntaxError, Timeout, RuntimeException, SchemaMismatch).

### 13. Metrics and Analytics
- **Existing**: `/api/analytics` computes aggregates in Python memory.
- **Gaps**:
  - Lacks granular time-series metrics.
  - Calculates all stats in Python rather than utilizing SQL aggregate queries.
  - Empty database states need robust default structures.

### 14. Leaderboard
- **Existing**: `/api/leaderboard` returns sorted agent stats.
- **Gaps**:
  - Lacks filtering by benchmark suite, difficulty, or date range.
  - Lacks ranking pagination and breakdown by category.

### 15. Report Generation
- **Existing**: `/api/reports/{id}/json` and `/api/reports/{id}/csv` for a single run.
- **Gaps**:
  - Single agent historical report export missing.
  - Multi-agent comparison report export missing.
  - Suite-level aggregated export missing.

### 16. API Routes Architecture
- **Existing**: All endpoints declared flatly in `main.py`.
- **Recommendation**: Decompose into modular FastAPI routers (`api/routers/auth.py`, `agents.py`, `benchmarks.py`, `tasks.py`, `runs.py`, `analytics.py`, `reports.py`, `system.py`, `admin.py`).

### 17. Frontend Pages
- **Required Pages (21 total)**:
  1. Dashboard / Overview (Partial)
  2. Agent Registry (Partial)
  3. Agent Registration (Missing separate modal/page)
  4. Agent Details (Missing)
  5. Benchmarks (Partial)
  6. Benchmark Details (Missing)
  7. Tasks (Partial)
  8. Task Editor (Missing)
  9. Run Benchmark (Partial)
  10. Live Execution (Missing)
  11. Execution History (Partial)
  12. Execution Details (Partial - inline only)
  13. Agent Comparison (Identical to Leaderboard)
  14. Leaderboard (Identical to Comparison)
  15. Analytics (Identical to Leaderboard)
  16. Reports (Partial)
  17. Notifications (Missing)
  18. SDK Documentation (Static text only)
  19. Settings (Partial)
  20. Administration (Missing)
  21. System Health (Missing)

### 18. API Integration
- **Existing**: Generic `fetch` with no interceptors, no token refresh, 4-second polling timer.
- **Gaps**:
  - Needs structured API client with error handling, loading states, and pagination parameters.

### 19. Existing Tests
- **Backend**: `backend/tests/test_workflow.py` contains 1 integration test.
- **Frontend**: 0 tests.
- **Requirement**: Comprehensive unit and integration test suite covering backend routers, execution lifecycle, evaluation engine, and frontend page rendering.

### 20. Code Quality & Formatting
- The current files (`main.py`, `worker.py`, `agent_runtime.py`, `main.tsx`) were written in an ultra-compact single-line/compressed format, reducing readability and maintainability.
- Code should be restructured into clean, PEP 8 / TypeScript standard modular files with comprehensive documentation.

---

## 3. Discovered Errors & Vulnerabilities

| Category | Issue | Impact |
|---|---|---|
| **Security** | Missing token expiry & logout | Sessions persist indefinitely; revoked credentials cannot be invalidated |
| **Security** | Windows Subprocess Termination | `p.kill()` kills direct PID only; child processes can leak |
| **Database** | No Alembic Migrations | Future schema changes require manual SQL or data loss |
| **Data Integrity** | `worker.py` Hardcoded Pathing | Relative module resolution can fail depending on execution cwd |
| **Architecture** | Missing State in Run Lifecycle | Runs skip `PENDING` directly to `QUEUED` |
| **Frontend** | Duplicated Views | Leaderboard, Comparison, and Analytics display the identical table |
| **Frontend** | Dead Controls | Global Search bar does not filter; theme is lost on browser refresh |
| **Reliability** | Worker Crash Recovery | Crashed runs stay stuck in `RUNNING` forever with no recovery |

---

## 4. Remediation Plan

1. **Phase 2**: Configure Python 3.14 virtual environment `.venv`, install all backend dependencies (adding `alembic`), install frontend npm dependencies, create `.env.example` and update `.gitignore`.
2. **Phase 3 & 4**: Reorganize backend into modular routers/services, implement full SQLAlchemy models (Users, Roles, Agents, Versions, Capabilities, Benchmarks, Tasks, Runs, Evaluations, Artifacts, Notifications, Audit, Settings), initialize Alembic migrations preserving existing database data.
3. **Phase 5**: Complete authentication with token expiration, logout, user profile (`/api/auth/me`), RBAC, and local admin initialization.
4. **Phase 6 & 8**: Build standard Python SDK (`agent_sdk`), implement complete Execution Engine with `PENDING -> QUEUED -> RUNNING -> COMPLETED/FAILED/TIMEOUT/CANCELLED` lifecycle, Windows process tree cleanup, worker heartbeat, and trusted agent runners.
5. **Phase 7 & 9**: Complete Benchmark & Task CRUD with validation; implement multi-criteria Evaluation Engine (exact, partial, schema, tolerance).
6. **Phase 10 & 12**: Expand frontend into dedicated modular pages covering all 21 views with search, filter, pagination, real API connections, and responsive premium design.
7. **Phase 11**: Build idempotent seed script providing the 5 required test agents and comprehensive benchmark suites.
8. **Phase 13**: Implement multi-format report generation (JSON/CSV) for runs, agents, and comparisons.
9. **Phase 14**: Write and execute full automated test suite (Backend Pytest + Frontend Vitest + E2E integration).
10. **Phase 15 & 16**: Audit performance, verify security, provide local startup scripts (`scripts/setup.ps1`, `scripts/start.ps1`, `scripts/setup.sh`, `scripts/start.sh`, `scripts/stop.sh`).
11. **Phase 17**: Produce `FINAL_VERIFICATION_REPORT.md`.

