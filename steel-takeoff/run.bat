@echo off
REM Steel Quantity Takeoff - Windows Runner
REM This script sets up the Python path and runs the application

REM Set PYTHONPATH to current directory
set PYTHONPATH=%~dp0

REM Activate virtual environment if it exists
if exist "%~dp0venv\Scripts\activate.bat" (
    call "%~dp0venv\Scripts\activate.bat"
)

REM Run the application with all arguments passed to this script
python "%~dp0main.py" %*
