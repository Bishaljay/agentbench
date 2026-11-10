"""Application configuration loaded from environment and defaults."""
import os
from pathlib import Path
from typing import List

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

# Read .env if present
env_file = PROJECT_ROOT / ".env"
if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

# Database configuration
_raw_db = os.environ.get("BENCHMARK_DB", "storage/benchmark.db")
if not os.path.isabs(_raw_db):
    DB_PATH = (PROJECT_ROOT / _raw_db).resolve()
else:
    DB_PATH = Path(_raw_db).resolve()

DB_PATH.parent.mkdir(parents=True, exist_ok=True)
# SQLite URI with forward slashes for Windows compatibility
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

# Server configuration
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8000"))
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "info")

# Security configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "local-dev-secret-key-change-in-production-only-32chars")
TOKEN_EXPIRE_HOURS = int(os.environ.get("TOKEN_EXPIRE_HOURS", "24"))

# CORS
_cors_raw = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
CORS_ORIGINS: List[str] = [origin.strip() for origin in _cors_raw.split(",") if origin.strip()]

# Execution & Worker
WORKER_POLL_INTERVAL = float(os.environ.get("WORKER_POLL_INTERVAL", "1.0"))
DEFAULT_TASK_TIMEOUT = float(os.environ.get("DEFAULT_TASK_TIMEOUT", "3.0"))
MAX_TASK_TIMEOUT = float(os.environ.get("MAX_TASK_TIMEOUT", "60.0"))
