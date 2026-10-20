#!/bin/bash
# ==============================================================================
# AlternIA - Démarrage Mode GPU (NVIDIA T4 / VRAM Dédiée)
# Exécute Qwen 2.5 embarqué sur GPU avec ZÉRO appel vers Groq / Gemini
# ==============================================================================
cd "$(dirname "$0")"

# Vérifier l'environnement virtuel (.venv ou système)
PYTHON_BIN="python3"
if [ -f ".venv/bin/python3" ]; then
    PYTHON_BIN=".venv/bin/python3"
fi

echo -e "\033[1;32m🚀 Démarrage d'AlternIA sur GPU (VRAM Dédiée) - Qwen Embarqué (Zéro API)\033[0m"
$PYTHON_BIN cloud/colab_server.py --local --device gpu --quick "$@"
