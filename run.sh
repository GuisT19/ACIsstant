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

# Step 3: Run the backend server
echo "[2/2] Starting the Backend Server..."
python -m backend.main

echo "Assistant closed."
