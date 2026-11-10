@echo off
set SCRIPT_DIR=%~dp0
set ROOT_DIR=%SCRIPT_DIR%..
cd /d "%ROOT_DIR%"

echo =======================================================
echo Starting AI Agent Benchmarking Platform
echo =======================================================

echo [1/3] Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "AgentBench-Backend" cmd /k "cd /d "%ROOT_DIR%\backend" && "%ROOT_DIR%\.venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000"

echo [2/3] Starting Background Worker ...
start "AgentBench-Worker" cmd /k "cd /d "%ROOT_DIR%\backend" && "%ROOT_DIR%\.venv\Scripts\python.exe" worker.py"

echo [3/3] Starting Vite Frontend on http://localhost:5173 ...
start "AgentBench-Frontend" cmd /k "cd /d "%ROOT_DIR%\frontend" && npm run dev"

echo.
echo All services launched!
echo Open http://localhost:5173 in your browser.
echo Swagger documentation is at http://127.0.0.1:8000/docs
echo =======================================================

