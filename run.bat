@echo off
echo ========================================================
echo           ProxyQR Attendance Management System
echo ========================================================
echo.
echo Starting FastAPI Server on http://localhost:8000 ...
echo Press Ctrl+C to stop.
echo.
.\venv\Scripts\python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
pause
