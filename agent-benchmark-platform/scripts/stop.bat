@echo off
echo Stopping all AgentBench services...
taskkill /F /FI "WINDOWTITLE eq AgentBench-Backend*" /T >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq AgentBench-Worker*" /T >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq AgentBench-Frontend*" /T >nul 2>&1
echo Done.

