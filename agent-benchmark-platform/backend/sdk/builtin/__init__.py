"""Built-in trusted agent implementations."""
import time
from pathlib import Path
from typing import Dict, Type
from sdk.base import BaseAgent, AgentContext, AgentResult

def perform_operation(op: str, data: any) -> any:
    """Core deterministic computational operations for benchmark tasks."""
    if op == "sum":
        return sum(data["numbers"])
    elif op == "sort":
        return sorted(data["items"])
    elif op == "transform":
        return {"full_name": f"{data['first']} {data['last']}"}
    elif op == "file":
        tmp_file = Path("artifact.txt")
        tmp_file.write_text(data["content"], encoding="utf-8")
        out = tmp_file.read_text(encoding="utf-8")
        if tmp_file.exists():
            tmp_file.unlink(missing_ok=True)
        return out
    elif op == "multistep":
        return sum(data["numbers"]) * 2
    elif op == "format":
        return data["value"].strip().lower()
    elif op == "validate":
        return isinstance(data["value"], int) and not isinstance(data["value"], bool)
    elif op in ("recover", "echo"):
        return data["value"]
    elif op == "filter":
        return [x for x in data["items"] if x > 0]
    elif op == "aggregate":
        nums = data["numbers"]
        return {"count": len(nums), "sum": sum(nums), "max": max(nums), "min": min(nums)}
    elif op == "regex":
        import re
        match = re.search(data["pattern"], data["text"])
        return match.group(0) if match else None
    else:
        raise ValueError(f"Unsupported operation: {op}")

class PerfectAgent(BaseAgent):
    """Accurately processes all tasks and returns expected answers."""
    def execute(self, context: AgentContext) -> AgentResult:
        out = perform_operation(context.operation, context.input_data)
        return AgentResult(status="success", output=out, metadata={"retries": 0})

class PartialSuccessAgent(BaseAgent):
    """Returns correct results for some operations, but incomplete/null for others."""
    def execute(self, context: AgentContext) -> AgentResult:
        if context.operation in ("sort", "file", "recover", "multistep", "filter"):
            # Intentionally incomplete
            return AgentResult(status="success", output=None, metadata={"retries": 0, "partial": True})
        out = perform_operation(context.operation, context.input_data)
        return AgentResult(status="success", output=out, metadata={"retries": 0})

class SlowAgent(BaseAgent):
    """Deliberately introduces latency to test timeout handling and resource measurement."""
    def execute(self, context: AgentContext) -> AgentResult:
        time.sleep(1.0)
        out = perform_operation(context.operation, context.input_data)
        return AgentResult(status="success", output=out, metadata={"retries": 0, "delayed": True})

class FailingAgent(BaseAgent):
    """Always raises a controlled failure to test error capture and status transitions."""
    def execute(self, context: AgentContext) -> AgentResult:
        raise RuntimeError("Controlled agent failure: intentional execution error")

class ErrorRecoveryAgent(BaseAgent):
    """Encounters simulated transient errors on recovery tasks, retries, and completes."""
    def execute(self, context: AgentContext) -> AgentResult:
        retries = 0
        if context.operation == "recover":
            # Simulate catching a transient failure and retrying
            try:
                raise RuntimeError("Simulated transient network timeout")
            except RuntimeError:
                retries = 1
        out = perform_operation(context.operation, context.input_data)
        return AgentResult(status="success", output=out, metadata={"retries": retries})

AGENT_REGISTRY: Dict[str, Type[BaseAgent]] = {
    "perfect": PerfectAgent,
    "partial": PartialSuccessAgent,
    "slow": SlowAgent,
    "failing": FailingAgent,
    "recovery": ErrorRecoveryAgent,
}

def get_agent(kind: str) -> BaseAgent:
    agent_cls = AGENT_REGISTRY.get(kind.lower())
    if not agent_cls:
        raise ValueError(f"Agent kind '{kind}' is not in the trusted registry")
    return agent_cls(name=f"{kind.capitalize()} Agent")

