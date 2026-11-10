#!/usr/bin/env bash
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -f "$ROOT_DIR/.pids" ]; then
    kill $(cat "$ROOT_DIR/.pids") 2>/dev/null || true
    rm -f "$ROOT_DIR/.pids"
fi
echo "Stopped services."

