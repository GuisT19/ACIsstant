#!/bin/bash
# ACIsstant Arch Linux Launch Script

# Function to restart/reset
main_loop() {
    clear
    echo "==========================================================="
    echo "     ACIsstant  |  Local AI Assistant (Linux)"
    echo "     Powered by Qwen2.5 3B  |  CPU-Only Mode"
    echo "==========================================================="
    echo ""

    # Check venv
    if [ ! -d "venv" ]; then
        echo "[ERRO] Ambiente virtual 'venv' não encontrado."
        echo "       Por favor, executa ./install_arch.sh primeiro."
        exit 1
    fi

    # Activate venv
    echo "[ .. ] Ativando Ambiente Virtual..."
    source venv/bin/activate
    echo "[ OK ] Ambiente activo."
    echo ""

    # Free port 8000
    if fuser 8000/tcp &>/dev/null; then
        echo "[ !! ] Limpando porta 8000..."
        fuser -k 8000/tcp > /dev/null 2>&1
        sleep 1
    fi
    echo "[ OK ] Porta 8000 limpa."
    echo ""

    echo "-----------------------------------------------------------"
    echo "  INICIANDO BACKEND..."
    echo "  Abrir no browser:  http://localhost:8000"
    echo "  Prime Ctrl+C para REINICIAR ou RESET."
    echo "-----------------------------------------------------------"
    echo ""

    python -m backend.main
    ret_val=$?

    # If Python exited with code 3, it was a Ctrl+R restart request.
    if [ $ret_val -eq 3 ]; then
        echo ""
        echo "  [ !! ] SINAL DE REINICIALIZAÇÃO DETECTADO. A reiniciar..."
        sleep 1
        main_loop
    fi

    echo ""
    echo "==========================================================="
    echo "  ACIsstant Parado."
    echo "  [1] REINICIAR (Normal)"
    echo "  [2] RESET (Limpar Base de Dados e Re-indexar)"
    echo "  [3] SAIR"
    echo "==========================================================="
    echo -n "Escolhe uma opção (1-3): "
    read choice

    case $choice in
        2)
            echo "[ .. ] Limpando o Índice RAG..."
            rm -rf data/vectordb
            echo "[ OK ] Índice limpo. Será reconstruído no próximo arranque."
            sleep 2
            main_loop
            ;;
        1)
            main_loop
            ;;
        3)
            exit 0
            ;;
        *)
            main_loop
            ;;
    esac
}

main_loop
