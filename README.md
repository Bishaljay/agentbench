# AgentBench
### Build a Benchmarking Platform for AI Agents, Not Just Models

AgentBench is a local web-based platform for benchmarking and evaluating **AI agent implementations** through repeatable tasks. It provides a central workspace to register agents, organize benchmark suites, execute runs, inspect task-level results, and compare performance.

> **Project status:** Working academic prototype / proof of concept. The included agents are deterministic Python scripts used to demonstrate the benchmark workflow; they are not autonomous LLM-based agents. The project is not production-ready and must not be exposed to untrusted users.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [How It Works](#how-it-works)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [1-clone-the-repository](#1-clone-the-repository)
  - [2-set-up-the-backend](#2-set-up-the-backend)
  - [3-set-up-the-frontend](#3-set-up-the-frontend)
  - [4-run-the-application](#4-run-the-application)
- [Using AgentBench](#using-agentbench)
- [Evaluation Methodology](#evaluation-methodology)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Configuration](#configuration)
- [Limitations and Security Notes](#limitations-and-security-notes)
- [Future Improvements](#future-improvements)
- [Team](#team)
- [License](#license)

---

## Overview

Traditional model evaluation often focuses on model-level metrics. AgentBench takes an **agent-oriented** approach: it evaluates how a configured agent performs across a collection of tasks and records its outcomes and execution characteristics.

The platform demonstrates an end-to-end benchmarking workflow:

1. Register and select an agent implementation.
2. Organize tasks into reusable benchmark suites.
3. Submit a benchmark run.
4. Let a background worker execute the queued tasks.
5. Compare each task's output with its expected result.
6. Review run history, task details, leaderboard information, and reports.

The current prototype uses a local SQLite database and trusted, built-in agent implementations so that the workflow can be demonstrated without external model APIs, API keys, or paid services.

## Key Features

- **Agent registry** — view and register supported built-in agent configurations.
- **Benchmark suites** — organize related tasks into reusable categories.
- **Task catalogue** — define task operations, JSON inputs, expected outputs, and timeouts.
- **Background execution** — process queued benchmark runs using a separate polling worker.
- **Task-level evaluation** — record success, failure, timeout, output, and execution details.
- **Run history and details** — inspect completed and failed benchmark runs.
- **Leaderboard and analytics** — compare registered agents using recorded benchmark results.
- **Report exports** — download run reports in CSV or JSON formats.
- **Local persistence** — store users, agents, suites, tasks, runs, and results in SQLite.

### Demonstration agents

The seed configuration includes five deterministic agent behaviours:

| Agent | Demonstrates |
|---|---|
| Perfect Agent | Correct output under normal execution |
| Partial Success Agent | Incomplete or partially matching output |
| Slow Agent | Execution delay and timeout handling |
| Failing Agent | Controlled execution errors |
| Error Recovery Agent | A simulated transient error followed by a retry |

These are scripted test behaviours, not real LLM agents.

### Example benchmark suites

The sample configuration includes suites such as:

- Data foundations
- Workflow operations
- Reliability checks
- Advanced reasoning & algorithms

The seeded task catalogue demonstrates arithmetic, sorting, JSON transformation, file operations, validation, filtering, aggregation, regular-expression extraction, and related operations.

---

## How It Works

```text
                 ┌────────────────────────┐
                 │       User             │
                 │ Select agent and suite │
                 └───────────┬────────────┘
                             │
                             ▼
                 ┌────────────────────────┐
                 │ React + TypeScript UI  │
                 │ Dashboard and controls│
                 └───────────┬────────────┘
                             │ HTTP / REST
                             ▼
                 ┌────────────────────────┐
                 │ FastAPI Backend        │
                 │ API and application    │
                 │ services               │
                 └───────────┬────────────┘
                             │
                  ┌──────────┴───────────┐
                  ▼                      ▼
        ┌──────────────────┐   ┌────────────────────┐
        │ SQLite Database  │   │ Background Worker  │
        │ Runs and results │◄──│ Executes queued    │
        │ and configuration│   │ tasks in processes │
        └──────────────────┘   └─────────┬──────────┘
                                         │
                                         ▼
                              ┌────────────────────┐
                              │ Evaluator          │
                              │ Compare actual and │
                              │ expected outputs   │
                              └────────────────────┘
```

**Execution lifecycle:** Configure → Queue → Execute → Evaluate → Store → Visualize

---

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React 18, TypeScript, Vite |
| UI and charts | Lucide React, Recharts |
| Backend API | Python, FastAPI, Uvicorn |
| Data validation | Pydantic |
| Database and ORM | SQLite, SQLAlchemy |
| Background execution | Python worker, subprocess |
| Process metrics | psutil |
| Testing | pytest, frontend production build |

---

## Project Structure

```text
agentbench/
├── backend/
│   ├── alembic/              # Migration configuration and scripts
│   ├── evaluation/           # Benchmark result evaluation
│   ├── execution/            # Execution backend and dispatcher
│   ├── models/               # Database models
│   ├── routers/              # API route modules
│   ├── schemas/              # API schemas
│   ├── sdk/                  # Runtime and runner components
│   ├── tests/                # Backend tests
│   ├── agent_runtime.py      # Built-in agent runtime
│   ├── config.py             # Application configuration
│   ├── database.py           # Database setup
│   ├── main.py               # FastAPI application entry point
│   ├── seed.py               # Sample configuration data
│   ├── worker.py             # Background task worker
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── main.tsx          # Frontend application
│   │   └── style.css         # Application styles
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
├── scripts/
│   ├── start.bat
│   ├── start.sh
│   ├── stop.bat
│   └── stop.sh
├── storage/                  # Local SQLite storage (created/used at runtime)
├── .env.example              # Example environment configuration
├── .gitignore
├── DEVELOPMENT_STATUS.md     # Implemented scope and known gaps
├── PROJECT_AUDIT.md          # Project review and audit notes
├── TASK_CHECKLIST.md
└── README.md
```

---

## Getting Started

### Prerequisites

Install the following:

- **Python 3.10 or later**
- **Node.js 20 or later**
- **npm** (included with Node.js)
- **Git**

Check your installed versions:

```bash
python --version
node --version
npm --version
git --version
```

### 1. Clone the repository

```bash
git clone https://github.com/Bishaljay/agentbench.git
cd agentbench
```

Run the remaining commands from the repository root (the directory containing `backend/` and `frontend/`).

### 2. Set up the backend

Create and activate a Python virtual environment.

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:

```bat
.venv\Scripts\activate.bat
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install Python dependencies:

```bash
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

### 3. Set up the frontend

Open a terminal at the repository root and run:

```bash
cd frontend
npm ci
cd ..
```

### 4. Run the application

Start the frontend, backend API, and worker in **three separate terminals**.

#### Terminal 1 — Backend API

From the repository root:

```bash
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

#### Terminal 2 — Background worker

From the repository root, activate the virtual environment if needed, then:

```bash
cd backend
python worker.py
```

#### Terminal 3 — Frontend

From the repository root:

```bash
cd frontend
npm run dev
```

Open the application in your browser:

**http://localhost:5173**

The FastAPI interactive API documentation is available at:

**http://localhost:8000/docs**

> Keep all three processes running while using the application. The worker is responsible for processing queued benchmark runs.

---

## Using AgentBench

1. Open `http://localhost:5173`.
2. Create an account and sign in.
3. Explore the dashboard and registered agents.
4. Open the benchmark library and select a suite.
5. Use the task catalogue to review the tasks in a suite or create a task.
6. Navigate to **Run benchmark**.
7. Select an agent and benchmark suite, then submit the run.
8. Open run history and inspect the run details and individual task results.
9. Review the leaderboard and analytics pages.
10. Export available run reports from the Reports area.

The dashboard and analytics are based on records stored by the application. The seed process does not create artificial benchmark run results.

---

## Evaluation Methodology

The current evaluator uses a simple, deterministic exact-match approach.

- Each task has an expected JSON output.
- The agent's returned output is compared with the expected value.
- A successful task with an exact output match receives a score of **1**.
- A mismatch or unsuccessful execution receives a score of **0**.
- Agent score and success rate are calculated from persisted task results.
- Failed and timed-out task attempts count as zero.
- Run duration is measured using subprocess wall-clock time.
- CPU and memory measurements are sampled from the executing process.

The leaderboard orders agents using score, success rate, and average execution time.

**Metric interpretation:** Process CPU time and peak resident memory are sampled measurements. Very short-lived processes may not be measured accurately. Token usage is not measured by this prototype.

---

## API Documentation

With the backend running, open:

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI schema: `http://localhost:8000/openapi.json`

The API is organized into modules for authentication, users, agents, benchmarks, tasks, runs, analytics, leaderboard, reports, system information, notifications, and audit-related routes. The exact endpoints and request schemas are documented in Swagger UI.

---

## Testing

### Backend tests

From the repository root:

```bash
cd backend
pytest -q
```

### Frontend production build

From the repository root:

```bash
cd frontend
npm run build
```

A successful frontend build runs the TypeScript check and Vite production build.

---

## Configuration

The project includes `.env.example` as a template. Copy it to `.env` in the repository root if you need to customize local settings.

**Windows PowerShell:**

```powershell
Copy-Item .env.example .env
```

**macOS / Linux:**

```bash
cp .env.example .env
```

Common settings include:

| Variable | Purpose | Default |
|---|---|---|
| `BENCHMARK_DB` | SQLite database path | `storage/benchmark.db` |
| `HOST` | Backend bind address | `127.0.0.1` |
| `PORT` | Backend port | `8000` |
| `ENVIRONMENT` | Application environment | `development` |
| `LOG_LEVEL` | Logging level | `info` |
| `CORS_ORIGINS` | Allowed frontend origins | Local Vite origins |
| `WORKER_POLL_INTERVAL` | Worker polling interval | `1.0` seconds |
| `DEFAULT_TASK_TIMEOUT` | Default task timeout | `3.0` seconds |
| `MAX_TASK_TIMEOUT` | Maximum configured task timeout | `60.0` seconds |

Use a unique secret key for any non-local deployment. Never commit `.env`, credentials, API keys, tokens, or private database contents.

---

## Limitations and Security Notes

AgentBench is an academic prototype intended for local demonstration and development.

- The built-in agents are deterministic scripts, not LLM-powered or autonomous agents.
- The runtime uses an allowlist of built-in agent behaviours; it is not a general-purpose secure agent plugin system.
- **Subprocess execution is not a security sandbox.** A child process can access the filesystem and network with the permissions of the current user.
- Do not execute untrusted code or expose the service to the public internet.
- Do not store secrets in task inputs or environment variables used by agent processes.
- Process-tree termination and operating-system resource isolation are not fully implemented.
- Worker crash recovery and stale-running-run reclamation are not implemented; a worker crash may leave a run marked as running.
- Authentication, session lifecycle, authorization roles, and administrative controls are not production-grade.
- Database migrations and several advanced management, versioning, filtering, and reporting capabilities remain incomplete.
- The current evaluation method is strict exact matching and does not provide general semantic evaluation of agent behaviour.

For a detailed scope review, see [`DEVELOPMENT_STATUS.md`](DEVELOPMENT_STATUS.md), [`PROJECT_AUDIT.md`](PROJECT_AUDIT.md), and [`TASK_CHECKLIST.md`](TASK_CHECKLIST.md).

---

## Future Improvements

Potential next steps for the project include:

- A documented, extensible agent SDK and adapter interface.
- Isolated execution using containers or another hardened sandbox.
- Process-tree management, CPU/memory limits, and worker crash recovery.
- More evaluation strategies, including schema validation, numeric tolerance, and task-specific scoring.
- Agent and benchmark versioning.
- Role-based access control and stronger session management.
- More complete analytics, filters, comparison tools, and report customization.
- Frontend end-to-end tests and broader automated test coverage.

---

## Team

| Name | Role |
|---|---|
| **Bishal Jaysawal** | Team Lead |
| Abhishek Gupta | Team Member |
| Suzanne | Team Member |

---

## License

No license has currently been specified. Unless a license is added to this repository, the project remains protected by the default copyright rules and others do not automatically receive permission to reuse, modify, or distribute it.

If you want to make the project open source, choose and add an appropriate license file (for example, MIT) after confirming that the project dependencies and all included assets permit it.
