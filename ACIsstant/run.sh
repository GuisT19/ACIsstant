#!/bin/bash

# Antigravity Arch Linux Launch Script
# This script activates the virtual environment and starts the backend service.

echo "--- Iniciando o Assistente Local Antigravity (Arch Linux) ---"

# Step 1: Check if venv exists
if [ ! -d "venv" ]; then
    echo "[ERRO] Ambiente virtual 'venv' não encontrado. Por favor, executa ./install_arch.sh primeiro."
    exit 1
fi

# Step 2: Activate venv
echo "[1/2] Ativando Ambiente Virtual..."
source venv/bin/activate

# Step 3: Run the backend server
echo "[2/2] Iniciando o Servidor Backend..."
python -m backend.main

echo "Assistente encerrado."
