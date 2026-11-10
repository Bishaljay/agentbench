"""Pydantic schemas for request and response validation."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=8, max_length=200)

class TokenResponse(BaseModel):
    token: str
    username: str
    role: str = "operator"

class UserProfile(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool
    created_at: str

class UserUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=200)

class AgentIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    kind: str
    version: str = "1.0.0"
    capabilities: str = "deterministic"
    description: str = ""

class AgentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    version: Optional[str] = None
    capabilities: Optional[str] = None
    description: Optional[str] = None

class AgentOut(BaseModel):
    id: int
    name: str
    kind: str
    version: str
    capabilities: str
    description: str
    created_at: str

class BenchmarkIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    category: str = "General"

class BenchmarkUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    category: Optional[str] = None

class BenchmarkOut(BaseModel):
    id: int
    name: str
    description: str
    category: str
    created_at: str

class TaskIn(BaseModel):
    benchmark_id: int
    name: str = Field(min_length=1)
    category: str = "General"
    operation: str
    input: Any
    expected: Any
    timeout: float = Field(default=3.0, gt=0, le=60.0)
    difficulty: str = "medium"
    memory_limit: Optional[int] = None

class TaskUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    operation: Optional[str] = None
    input: Optional[Any] = None
    expected: Optional[Any] = None
    timeout: Optional[float] = Field(default=None, gt=0, le=60.0)
    difficulty: Optional[str] = None
    memory_limit: Optional[int] = None

class TaskOut(BaseModel):
    id: int
    benchmark_id: int
    name: str
    category: str
    operation: str
    input: str
    expected: str
    timeout: float
    difficulty: str
    memory_limit: Optional[int] = None
    created_at: str

class RunIn(BaseModel):
    agent_id: int
    benchmark_id: int

class RunOut(BaseModel):
    id: int
    agent_id: int
    benchmark_id: int
    status: str
    created_at: str
    finished_at: Optional[str] = None
    cancel: int = 0

class TaskRunOut(BaseModel):
    id: int
    run_id: int
    task_id: int
    status: str
    output: str
    error: str
    duration: float
    cpu: float
    memory: int
    score: float
    retries: int

class RunDetailOut(RunOut):
    tasks: List[TaskRunOut] = []

class LeaderboardEntry(BaseModel):
    agent_id: int
    name: str
    kind: str
    tasks: int
    success_rate: float
    score: float
    avg_duration: float
    median: float
    p95: float
    memory: float
    cpu: float
    timeouts: int
    recoveries: int

class AnalyticsSummary(BaseModel):
    agents: int
    benchmarks: int
    runs: int
    completed: int
    failed: int
    avg_duration: float
    avg_memory: float
    leaderboard: List[LeaderboardEntry]

class HealthResponse(BaseModel):
    status: str
    database: str
    worker: str
    version: str = "0.2.0"
    environment: str = "development"
    active_runs: int = 0
    timestamp: str

class NotificationOut(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    type: str
    is_read: bool
    created_at: str

class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int]
    username: str
    action: str
    entity_type: str
    entity_id: Optional[str]
    details: str
    ip_address: Optional[str]
    created_at: str

class SettingIn(BaseModel):
    value: str
    description: Optional[str] = None

class SettingOut(BaseModel):
    key: str
    value: str
    description: str
    updated_at: str

