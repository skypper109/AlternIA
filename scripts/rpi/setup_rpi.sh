#!/bin/bash
# ==============================================================================
# AlternIA Box — Script d'installation automatique pour Raspberry Pi 4 & 5
# OS supporté : Raspberry Pi OS (Debian 12 Bookworm 64-bit)
# ==============================================================================

set -e

echo "===================================================================="
echo "🇲🇱   Installation et Configuration de l'AlternIA Box (Raspberry Pi)  🇲🇱"
echo "===================================================================="

# 1. Mise à jour des paquets système
echo "📦 [1/6] Mise à jour des paquets système..."
sudo apt-get update
sudo apt-get install -y \
    python3-pip python3-venv python3-dev \
    git curl wget mpv ffmpeg alsa-utils \
    libopenblas-dev libgomp1 \
    chromium-browser hostapd dnsmasq

# 2. Création de l'environnement virtuel Python
echo "🐍 [2/6] Configuration de l'environnement virtuel Python..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip setuptools wheel

# 3. Installation de llama-cpp-python avec accélération CPU ARM NEON
echo "⚡ [3/6] Compilation & Installation de llama-cpp-python (ARM NEON)..."
CMAKE_ARGS="-DGGML_NATIVE=ON -DGGML_BLAS=OFF" pip install llama-cpp-python --no-cache-dir

# 4. Installation des dépendances du projet
echo "📚 [4/6] Installation des dépendances AlternIA..."
pip install -r requirements.txt
pip install edge-tts RPi.GPIO

# 5. Indexation des manuels scolaires (si pas encore indexé)
echo "🔍 [5/6] Vérification de l'indexation de la base de connaissances..."
PYTHONPATH=ai-engine/src python -m alternia.scripts.index_knowledge || true

# 6. Installation des services systemd (Démarrage automatique au boot)
echo "⚙️ [6/6] Installation des services systemd..."
sudo cp scripts/rpi/alternia-backend.service /etc/systemd/system/
sudo cp scripts/rpi/alternia-kiosk.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable alternia-backend.service
sudo systemctl enable alternia-kiosk.service

echo ""
echo "===================================================================="
echo "✅ Installation terminée avec succès !"
echo "👉 Redémarrez le Raspberry Pi ('sudo reboot') pour lancer AlternIA."
echo "👉 Interface disponible sur http://localhost:8000/app"
echo "===================================================================="
