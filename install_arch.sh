#!/bin/bash

# Antigravity Arch Linux Installer script
# This script installs system dependencies, sets up a virtual environment, and installs Python packages.

echo "--- Iniciando Instalação para Arch Linux ---"

# Step 1: Install system dependencies using pacman
echo "[1/4] Instalando dependências do sistema..."
sudo pacman -S --needed --noconfirm base-devel cmake python python-pip python-virtualenv 

# Step 2: Create a virtual environment if it doesn't exist
echo "[2/4] Criando ambiente virtual (venv)..."
if [ ! -d "venv" ]; then
    python -m venv venv
else
    echo "Ambiente venv já existe. Saltando criação."
fi

# Step 3: Activate venv and install requirements
echo "[3/4] Instalando dependências Python via pip..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Step 4: Make run.sh executable
echo "[4/4] Configurando script de execução..."
chmod +x run.sh

echo "--- Instalação concluída com sucesso! ---"
echo "Agora podes descarregar o modelo com: venv/bin/python download_model.py"
echo "E iniciar o assistente com: ./run.sh"
