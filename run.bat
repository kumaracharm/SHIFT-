@echo off
title SHIFT - Streaming Hybrid Intelligence for Fraud Tracking
echo ========================================================
echo   SHIFT - Fraud Detection & Threat Tracking Platform
echo ========================================================
echo.
echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "SHIFT Backend (FastAPI)" cmd /k "cd /d D:\project\HACKATHONAI && python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/2] Starting Next.js Frontend on http://localhost:3000 ...
start "SHIFT Frontend (Next.js)" cmd /k "cd /d D:\project\HACKATHONAI\frontend && npm run dev"

echo.
echo ========================================================
echo   Services Launched!
echo   - Web Platform:  http://localhost:3000
echo   - Backend Docs:  http://127.0.0.1:8000/docs
echo ========================================================
echo.
pause

