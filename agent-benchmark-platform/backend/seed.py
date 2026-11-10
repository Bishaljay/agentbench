"""Idempotent seed script for platform initialization and trusted demo configuration.
Seeds agents, benchmark suites, tasks, and system settings. Does not create fake runs.
"""
import json
import sys
from pathlib import Path

# Add backend directory to path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select
from database import SessionLocal
from models import Agent, Benchmark, Task, SystemSetting, User, Role
from security import hash_password

def seed_database(verbose: bool = True):
    """Seed base configuration idempotently."""
    with SessionLocal() as db:
        # 1. Base Roles
        roles_data = [
            ("admin", "Full administrative control and user management"),
            ("operator", "Execute benchmarks and export analytical reports"),
            ("viewer", "Read-only access to dashboard and leaderboard")
        ]
        for name, desc in roles_data:
            if not db.scalar(select(Role.id).where(Role.name == name)):
                db.add(Role(name=name, description=desc))
        db.commit()

        # 2. Trusted Sample Agents
        agents_data = [
            ("Perfect Agent", "perfect", "1.0.0", "deterministic,exact-match", "Always computes expected output correctly and within standard timeout limits."),
            ("Partial Success Agent", "partial", "1.0.0", "deterministic,partial-match", "Demonstrates partial output matching and incomplete state representation."),
            ("Slow Agent", "slow", "1.0.0", "deterministic,latency", "Introduces execution delay to test timeout limits and duration metrics."),
            ("Failing Agent", "failing", "1.0.0", "deterministic,fault-injection", "Throws controlled execution errors to test failure capture and status handling."),
            ("Error Recovery Agent", "recovery", "1.0.0", "deterministic,self-healing", "Catches simulated transient network errors, retries, and completes successfully.")
        ]
        for name, kind, ver, caps, desc in agents_data:
            existing = db.scalar(select(Agent).where(Agent.name == name))
            if not existing:
                db.add(Agent(name=name, kind=kind, version=ver, capabilities=caps, description=desc))
        db.commit()

        # 3. Benchmark Suites
        suites_data = [
            ("Data foundations", "JSON transformation, arithmetic, and structured processing", "Data"),
            ("Workflow operations", "File I/O, multi-step workflows, and string formatting", "Workflow"),
            ("Reliability checks", "Input validation, timeout resistance, and error recovery behavior", "Reliability"),
            ("Advanced reasoning & algorithms", "Filtering, aggregations, and pattern extraction", "Reasoning")
        ]
        suite_map = {}
        for name, desc, cat in suites_data:
            b = db.scalar(select(Benchmark).where(Benchmark.name == name))
            if not b:
                b = Benchmark(name=name, description=desc, category=cat)
                db.add(b)
                db.flush()
            suite_map[name] = b.id
        db.commit()

        # 4. Comprehensive Task Catalog
        tasks_data = [
            # Suite 1: Data foundations
            (suite_map["Data foundations"], "Sum numbers", "Data", "sum", {"numbers": [2, 4, 6]}, 12, 3.0, "easy"),
            (suite_map["Data foundations"], "Sort records", "Data", "sort", {"items": ["pear", "apple", "orange"]}, ["apple", "orange", "pear"], 3.0, "easy"),
            (suite_map["Data foundations"], "Transform JSON", "Data", "transform", {"first": "Ada", "last": "Lovelace"}, {"full_name": "Ada Lovelace"}, 3.0, "medium"),

            # Suite 2: Workflow operations
            (suite_map["Workflow operations"], "Create and read file", "Workflow", "file", {"content": "benchmark artifact"}, "benchmark artifact", 3.0, "medium"),
            (suite_map["Workflow operations"], "Multi-step calculation", "Workflow", "multistep", {"numbers": [1, 2, 3]}, 12, 3.0, "medium"),
            (suite_map["Workflow operations"], "Format output", "Workflow", "format", {"value": "  Hello World  "}, "hello world", 3.0, "easy"),

            # Suite 3: Reliability checks
            (suite_map["Reliability checks"], "Validate input", "Reliability", "validate", {"value": 42}, True, 3.0, "easy"),
            (suite_map["Reliability checks"], "Recover from error", "Reliability", "recover", {"value": "ready"}, "ready", 3.0, "hard"),
            (suite_map["Reliability checks"], "Timeout check", "Reliability", "echo", {"value": "on time"}, "on time", 0.5, "hard"),

            # Suite 4: Advanced reasoning & algorithms
            (suite_map["Advanced reasoning & algorithms"], "Positive filter", "Reasoning", "filter", {"items": [-5, 10, -2, 8, 0, 15]}, [10, 8, 15], 3.0, "medium"),
            (suite_map["Advanced reasoning & algorithms"], "Statistical aggregate", "Reasoning", "aggregate", {"numbers": [10, 20, 30, 40]}, {"count": 4, "sum": 100, "max": 40, "min": 10}, 3.0, "medium"),
            (suite_map["Advanced reasoning & algorithms"], "Regex extraction", "Reasoning", "regex", {"pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b", "text": "Contact us at support@example.com for help"}, "support@example.com", 3.0, "medium")
        ]

        for b_id, name, cat, op, inp, exp, timeout, diff in tasks_data:
            existing = db.scalar(
                select(Task).where(Task.benchmark_id == b_id, Task.name == name)
            )
            if not existing:
                db.add(Task(
                    benchmark_id=b_id,
                    name=name,
                    category=cat,
                    operation=op,
                    input=json.dumps(inp),
                    expected=json.dumps(exp),
                    timeout=timeout,
                    difficulty=diff
                ))
        db.commit()

        # 5. System Settings
        settings_data = [
            ("platform_name", "AI Agent Benchmarking Platform", "System display name"),
            ("default_timeout", "3.0", "Default task execution timeout in seconds"),
            ("max_timeout", "60.0", "Maximum permissible task timeout"),
            ("worker_mode", "local_subprocess", "Worker execution backend model"),
            ("log_level", "INFO", "Application logging verbosity")
        ]
        for key, val, desc in settings_data:
            if not db.scalar(select(SystemSetting).where(SystemSetting.key == key)):
                db.add(SystemSetting(key=key, value=val, description=desc))
        db.commit()

        if verbose:
            print("Database initialization and seed complete.")

if __name__ == "__main__":
    seed_database(verbose=True)

