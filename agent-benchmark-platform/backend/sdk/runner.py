"""Subprocess runner adhering to standard JSON input/output protocol."""
import json
import sys
from pathlib import Path

# Add backend directory to sys.path so sdk is importable
backend_dir = Path(__file__).resolve().parents[1]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sdk.base import AgentContext
from sdk.builtin import get_agent

def run_main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input:
            print("No input provided to agent runner", file=sys.stderr)
            sys.exit(1)
        data = json.loads(raw_input)
        kind = data.get("kind", "perfect")
        operation = data.get("operation")
        input_data = data.get("input")
        timeout = float(data.get("timeout", 3.0))

        context = AgentContext(
            operation=operation,
            input_data=input_data,
            timeout=timeout
        )
        agent = get_agent(kind)
        result = agent.execute(context)
        print(json.dumps(result.model_dump()))
        sys.exit(0)
    except Exception as e:
        print(f"Agent Execution Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run_main()

