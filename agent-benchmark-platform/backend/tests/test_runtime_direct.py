import subprocess
import sys
import json
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[1]
runtime = str(backend_dir / "agent_runtime.py")

payload = json.dumps({"kind": "perfect", "operation": "sum", "input": {"numbers": [1, 2, 3]}})
p = subprocess.Popen([sys.executable, runtime], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
out, err = p.communicate(payload)
print("Returncode:", p.returncode)
print("Stdout:", out)
print("Stderr:", err)
assert p.returncode == 0
assert "6" in out
print("Direct runtime test SUCCESS")
