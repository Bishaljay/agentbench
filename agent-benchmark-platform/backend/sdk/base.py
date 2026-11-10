"""Agent SDK Base Classes and Protocol Definitions."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class AgentContext(BaseModel):
    """Execution context provided to an agent during task execution."""
    operation: str
    input_data: Any
    timeout: float = 3.0
    task_id: Optional[int] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)

class AgentResult(BaseModel):
    """Structured result returned by an agent adhering to the platform protocol."""
    status: str = "success"  # 'success' or 'error'
    output: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BaseAgent(ABC):
    """Abstract base class that all benchmarked agents must implement."""
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version

    @abstractmethod
    def execute(self, context: AgentContext) -> AgentResult:
        """Execute the agent task and return a structured AgentResult."""
        pass

