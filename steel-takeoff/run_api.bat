@echo off
REM Steel Takeoff API Server - Windows Runner
REM This script starts the FastAPI server

REM Set working directory
cd /d "%~dp0"

REM Set PYTHONPATH
set PYTHONPATH=%~dp0

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo.
echo ========================================
echo  Steel Quantity Takeoff API
echo ========================================
echo.
echo Starting server...
echo.
echo API URL: http://localhost:8000
echo Swagger UI: http://localhost:8000/docs
echo ReDoc: http://localhost:8000/redoc
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

REM Run the API server
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
