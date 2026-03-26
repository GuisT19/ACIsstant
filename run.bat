@echo off
setlocal enabledelayedexpansion

cls
echo.
echo  ===========================================================
echo       ACIsstant  ^|  Local AI Assistant
echo       Powered by Qwen2.5 3B  ^|  CPU-Only Mode
echo  ===========================================================
echo.

:: -- Check venv ------------------------------------------------
if not exist venv\ (
    echo  [ERROR] Virtual environment not found.
    echo          Please run install_windows.bat first.
    echo.
    pause
    exit /b 1
)

:: -- Activate venv ---------------------------------------------
echo  [ .. ] Activating virtual environment...
call venv\Scripts\activate.bat
echo  [ OK ] Virtual environment active.
echo.

:: -- Free port 8000 if already in use -------------------------
set PORT_BUSY=0
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    set PORT_BUSY=1
    echo  [ !! ] Port 8000 in use ^(PID %%a^). Releasing...
    taskkill /PID %%a /F >nul 2>&1
    timeout /t 1 /nobreak >nul
)
if %PORT_BUSY%==0 (
    echo  [ OK ] Port 8000 is free.
)
echo.

:: -- Start backend --------------------------------------------
title ACIsstant ^| Running at http://localhost:8000
echo  [ .. ] Starting backend server...
echo.
echo  ===========================================================
echo    Open in browser:   http://localhost:8000
echo    Press Ctrl+C to stop the assistant at any time.
echo  ===========================================================
echo.

python -m backend.main

:: -- Shutdown -------------------------------------------------
echo.
echo  ===========================================================
echo    ACIsstant stopped.
echo  ===========================================================
echo.
echo  ===========================================================
echo    Session ended. Goodbye.
echo  ===========================================================
echo.
title ACIsstant ^| Offline
pause
