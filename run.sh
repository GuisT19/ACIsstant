#!/bin/bash

# Antigravity Arch Linux Launch Script
# This script activates the virtual environment and starts the backend service.

echo "--- Starting Antigravity Local AI Assistant (Linux) ---"

# Step 1: Check if venv exists
if [ ! -d "venv" ]; then
    echo "[ERROR] Virtual environment 'venv' not found. Please run ./install_linux.sh first."
    exit 1
fi

# Step 2: Activate venv
echo "[1/2] Activating Virtual Environment..."
source venv/bin/activate

# Step 3: Free port 8000 if already in use
if fuser 8000/tcp &>/dev/null; then
    echo "[WARNING] Port 8000 is in use. Terminating previous process..."
    fuser -k 8000/tcp
    sleep 1
fi

# Step 4: Run the backend server
echo "[2/2] Starting Backend Server..."
python -m backend.main

echo "Assistant closed."
