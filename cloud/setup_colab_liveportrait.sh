#!/usr/bin/env bash
# ==============================================================================
# AlternIA Cloud GPU Server — Setup LivePortrait In-Memory (Zero-Disk)
# ==============================================================================
set -e

echo "🚀 Préparation de l'environnement GPU AlternIA (Zero-Disk I/O)..."

# 1. Dépendances système
apt-get update -qq && apt-get install -y -qq ffmpeg

# 2. Dépendances Python sans mise en cache superflue (gain de 10+ Go d'espace disque)
pip install -q --no-cache-dir -r requirements.txt
pip install -q --no-cache-dir faster-whisper ctranslate2 soundfile

# 3. Installation optimisée de LivePortrait pour inférence en mémoire
cd /content || cd /tmp
if [ ! -d "LivePortrait" ]; then
    echo "📦 Clonage de LivePortrait..."
    git clone --depth 1 https://github.com/KwaiVGI/LivePortrait.git
fi

cd LivePortrait
pip install -q --no-cache-dir -r requirements.txt

echo "📥 Téléchargement des checkpoints pré-entraînés LivePortrait..."
python3 -c "
from huggingface_hub import snapshot_download
snapshot_download(repo_id='KwaiVGI/LivePortrait', local_dir='pretrained_weights', allow_patterns=['*.safetensors', '*.pth', '*.json', '*.yaml'])
" || true

# 4. Purge des résidus d'installation pour préserver l'espace disque
pip cache purge >/dev/null 2>&1 || true

echo "✅ Environnement LivePortrait In-Memory (Zero-Disk) prêt avec succès !"
