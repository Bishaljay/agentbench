"""Database setup, constraints, migrations, and CRUD operations verification."""
import pytest
from sqlalchemy import select, text
from database import SessionLocal, engine
from models import (
    Base, User, Role, SessionToken, Agent, AgentVersion, AgentCapability,
    Benchmark, BenchmarkVersion, Task, TaskVersion, Run, TaskRun,
    EvaluationResult, Artifact, Notification, AuditLog, SystemSetting
)

def test_database_tables_exist():
    """Verify all required tables are present in SQLite metadata."""
    inspector_tables = engine.dialect.get_table_names(engine.connect())
    required_tables = [
        "users", "roles", "session_tokens", "agents", "agent_versions",
        "agent_capabilities", "benchmarks", "benchmark_versions", "tasks",
        "task_versions", "benchmark_runs", "task_runs", "evaluation_results",
        "artifacts", "notifications", "audit_logs", "system_settings"
    ]
    for table in required_tables:
        assert table in inspector_tables, f"Table '{table}' missing from database"

def test_existing_users_preserved():
    """Verify that existing user data in benchmark.db was preserved."""
    with SessionLocal() as session:
        users = session.scalars(select(User)).all()
        usernames = [u.username for u in users]
        assert "rm@gmail.com" in usernames or len(users) >= 2, f"Expected existing users, got {usernames}"

def test_foreign_key_constraints():
    """Verify foreign key enforcement in SQLite."""
    with SessionLocal() as session:
        # Check foreign_keys pragma is enabled
        fk_on = session.execute(text("PRAGMA foreign_keys")).scalar()
        assert fk_on == 1

        # Attempting to insert a task for a non-existent benchmark should fail
        invalid_task = Task(
            benchmark_id=999999,
            name="Orphan Task",
            category="Test",
            operation="echo",
            input="{}",
            expected="{}"
        )
        session.add(invalid_task)
        with pytest.raises(Exception):
            session.commit()
        session.rollback()

def test_crud_operations():
    """Verify insert, update, query, and delete operations."""
    with SessionLocal() as session:
        # Insert
        test_agent = Agent(
            name="Test Verification Agent",
            kind="perfect",
            version="1.0.0",
            capabilities="deterministic,testing",
            description="Created for CRUD testing"
        )
        session.add(test_agent)
        session.commit()
        agent_id = test_agent.id
        assert agent_id is not None

        # Query & Update
        loaded = session.get(Agent, agent_id)
        assert loaded is not None
        assert loaded.name == "Test Verification Agent"
        loaded.description = "Updated description"
        session.commit()

        reloaded = session.get(Agent, agent_id)
        assert reloaded.description == "Updated description"

        # Delete
        session.delete(reloaded)
        session.commit()

        deleted = session.get(Agent, agent_id)
        assert deleted is None

