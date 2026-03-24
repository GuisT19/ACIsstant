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

# Step 3: Free port 8000 if already in use
if fuser 8000/tcp &>/dev/null; then
    echo "[AVISO] Porta 8000 em uso. A terminar processo anterior..."
    fuser -k 8000/tcp
    sleep 1
fi

# Step 4: Run the backend server
echo "[2/2] Iniciando o Servidor Backend..."
python -m backend.main

echo "Assistente encerrado."
