@echo off
title AI Sales Backend Server
cd /d "%~dp0"
call .venv\Scripts\activate
python run_server.py
pause
