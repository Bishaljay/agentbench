"""Trusted deterministic agent runtime subprocess, JSON in/out.
Maintains backward compatibility while delegating to the Python Agent SDK.
"""
import sys
from pathlib import Path

# Ensure backend root is on path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sdk.runner import run_main

if __name__ == "__main__":
    run_main()
