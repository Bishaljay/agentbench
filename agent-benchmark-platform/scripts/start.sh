#!/usr/bin/env bash
set -e
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Starting AgentBench backend..."
cd "$ROOT_DIR/backend"
"$ROOT_DIR/.venv/bin/uvicorn" main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

echo "Starting worker..."
"$ROOT_DIR/.venv/bin/python" worker.py &
WORKER_PID=$!

echo "Starting frontend..."
cd "$ROOT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo "$BACKEND_PID $WORKER_PID $FRONTEND_PID" > "$ROOT_DIR/.pids"
echo "Services running. Open http://localhost:5173"

