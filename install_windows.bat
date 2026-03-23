@echo off
setlocal

echo --- Initializing Installation for Windows ---

:: Step 1: Check for Python
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+ first.
    pause
    exit /b 1
)

:: Step 2: Create Virtual Environment
echo [1/4] Creating virtual environment (venv)...
if not exist venv (
    python -m venv venv
) else (
    echo Virtual environment (venv) already exists. Skipping creation.
)

:: Step 3: Install Dependencies
echo [2/4] Installing Python dependencies via pip...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

:: Step 4: Finalize
echo [3/4] Final configuration completed successfully!
echo.
echo [4/4] Now you can download the model with:
echo       venv\Scripts\python.exe download_model.py
echo.
echo --- Installation complete! ---
echo Run 'run.bat' to start the assistant.
echo.
pause
