#!/bin/bash
# ==============================================================================
# AlternIA - Démarrage Mode CPU (Multi-Cœurs & RAM Système)
# Exécute Qwen 2.5 embarqué sur CPU et libère 100% de la VRAM GPU pour la vidéo
# ==============================================================================
cd "$(dirname "$0")"

# Vérifier l'environnement virtuel (.venv ou système)
PYTHON_BIN="python3"
if [ -f ".venv/bin/python3" ]; then
    PYTHON_BIN=".venv/bin/python3"
fi

echo -e "\033[1;33m⚙️ Démarrage d'AlternIA sur CPU (vCPUs) - VRAM 100% libre pour la vidéo (Zéro API)\033[0m"
$PYTHON_BIN cloud/colab_server.py --local --device cpu "$@"
