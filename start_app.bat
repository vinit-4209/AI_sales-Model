@echo off
title AI Sales Call Assistant Launcher
echo ========================================================
echo        Starting AI Sales Call Assistant (React UI)
echo ========================================================
echo.

echo [1/2] Starting Backend API Server (FastAPI on port 8000)...
start "AI Sales Backend" cmd /k "cd /d "%~dp0" && .venv\Scripts\activate && python run_server.py"

echo [2/2] Starting Frontend App (React on port 5173)...
start "AI Sales Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo ========================================================
echo  Both services are launching in separate windows!
echo  React Frontend: http://localhost:5173
echo  Backend API:    http://127.0.0.1:8000
echo  API Docs:       http://127.0.0.1:8000/docs
echo ========================================================
echo.
pause
