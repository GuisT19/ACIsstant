@echo off
echo --- Starting Antigravity Local AI Assistant ---
echo [1/2] Activating Virtual Environment...
if not exist venv (
    echo [ERROR] Virtual environment 'venv' not found. Please run install_windows.bat first.
    pause
    exit /b 1
)
call venv\Scripts\activate.bat

echo [2/2] Launching Backend Server...
python -m backend.main

pause
