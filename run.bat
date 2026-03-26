@echo off
setlocal enabledelayedexpansion

:MAIN_MENU
cls
echo  ===========================================================
echo       ACIsstant  ^|  Local AI Assistant
echo       Powered by Qwen2.5 3B  ^|  CPU-Only Mode
echo  ===========================================================
echo.

:: -- Check venv ------------------------------------------------
if not exist venv\ (
    echo  [ERROR] Virtual environment not found. Please run install_windows.bat.
    pause
    exit /b 1
)

:: -- Activate venv ---------------------------------------------
echo  [ .. ] Activating virtual environment...
call venv\Scripts\activate.bat >nul 2>&1
echo  [ OK ] Virtual environment active.
echo.

:: -- Free port 8000 -------------------------------------------
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)
echo  [ OK ] Port 8000 is clean.

echo.
echo  -----------------------------------------------------------
echo    STARTING BACKEND...
echo    Open in browser:   http://localhost:8000
echo    Press Ctrl+C and Ctrl+R to RESTART/RESET.
echo  -----------------------------------------------------------
echo.

python -m backend.main

echo.
echo  ===========================================================
echo    ACIsstant Stopped.
echo    [1] RESTART normally
echo    [2] RESET Knowledge Base (Clear Index ^& Scan Files)
echo    [3] EXIT
echo  ===========================================================
set /p CHOICE="Choose an option (1-3): "

if "%CHOICE%"=="2" (
    echo  [ .. ] Clearing RAG Index...
    if exist data\vectordb rmdir /s /q data\vectordb
    echo  [ OK ] Index cleared. It will rebuild on next start.
    timeout /t 2 >nul
    goto MAIN_MENU
)
if "%CHOICE%"=="1" goto MAIN_MENU
if "%CHOICE%"=="3" exit /b 0

goto MAIN_MENU
