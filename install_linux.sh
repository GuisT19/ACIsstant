#!/bin/bash

# Antigravity Linux (Arch) Installer script
# This script installs system dependencies, sets up a virtual environment, and installs Python packages.

echo "--- Initializing Installation for Linux (Arch) ---"

# Step 1: Install system dependencies using pacman
echo "[1/4] Installing system dependencies..."
if command -v pacman &> /dev/null; then
    sudo pacman -S --needed --noconfirm base-devel cmake python python-pip python-virtualenv 
else
    echo "[WARNING] Pacman not found. Please manually install: base-devel, cmake, python, pip, venv."
fi

# Step 2: Create a virtual environment if it doesn't exist
echo "[2/4] Creating virtual environment (venv)..."
if [ ! -d "venv" ]; then
    python -m venv venv
else
    echo "Virtual environment (venv) already exists. Skipping creation."
fi

# Step 3: Activate venv and install requirements
echo "[3/4] Installing Python dependencies via pip..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Step 4: Make run scripts executable
echo "[4/4] Configuring execution scripts..."
chmod +x run.sh

echo "--- Installation completed successfully! ---"
echo "Now you can download the model with: venv/bin/python download_model.py"
echo "And start the assistant with: ./run.sh"
