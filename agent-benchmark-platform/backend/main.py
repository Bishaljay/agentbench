"""FastAPI backend application entrypoint.
Registers routers, configures CORS, initializes logging, and provides backward compatibility.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from config import CORS_ORIGINS, LOG_LEVEL, ENVIRONMENT
from database import SessionLocal, engine
from models import Base, User, Role, Agent, Benchmark, Task, Run, TaskRun, utc_now_iso
from security import get_current_user
from seed import seed_database

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("agentbench.api")

# Lifespan event for idempotent startup initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Agent Benchmark Platform backend...")
    # Ensure tables exist and seed default catalog
    seed_database(verbose=False)
    yield
    logger.info("Shutting down backend cleanly...")

app = FastAPI(
    title="Agent Benchmark Platform API",
    description="Enterprise-grade local benchmarking engine for AI and deterministic agents",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS else ["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Validation exception handler for clear error feedback
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_msg = "; ".join(f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": error_msg, "errors": exc.errors()}
    )

# Register modular routers
from routers import (
    auth, users, agents, benchmarks, tasks,
    runs, analytics, leaderboard, reports,
    system, notifications, audit
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(agents.router)
app.include_router(benchmarks.router)
app.include_router(tasks.router)
app.include_router(runs.router)
app.include_router(analytics.router)
app.include_router(leaderboard.router)
app.include_router(reports.router)
app.include_router(system.router)
app.include_router(notifications.router)
app.include_router(audit.router)

# Compatibility aliases for legacy scripts and test harness
Session = SessionLocal
now = utc_now_iso
auth_dep = get_current_user

def serialize(o):
    """Serialize model instance to dictionary."""
    if hasattr(o, "to_dict"):
        return o.to_dict()
    return {c.name: getattr(o, c.name) for c in o.__table__.columns}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
