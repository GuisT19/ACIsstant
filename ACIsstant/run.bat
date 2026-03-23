@echo off
echo --- Starting Antigravity Local AI Assistant ---
echo [1/2] Activating Virtual Environment...
call venv\Scripts\activate.bat

echo [2/2] Launching Backend Server...
python -m backend.main

pause
