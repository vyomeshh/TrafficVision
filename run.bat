@echo off
echo ===================================
echo   TrafficVision AI - Server Startup
echo ===================================
echo.

REM Check if venv exists
if not exist "venv" (
    echo [SETUP] Creating Python virtual environment...
    python -m venv venv
)

echo [SETUP] Activating virtual environment...
call venv\Scripts\activate.bat

echo [SETUP] Installing dependencies...
pip install -r requirements.txt

echo.
echo [SERVER] Starting FastAPI server on http://localhost:8000
echo [SERVER] API docs available at http://localhost:8000/docs
echo.
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
