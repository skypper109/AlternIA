#!/usr/bin/env bash
# ==============================================================================
# AlternIA Cloud GPU Server — Setup LivePortrait In-Memory (Zero-Disk)
# ==============================================================================
set -e

echo "🚀 Préparation de l'environnement GPU AlternIA (Zero-Disk I/O)..."

# 1. Dépendances système
apt-get update -qq && apt-get install -y -qq ffmpeg

# 2. Dépendances Python et accélération CUDA GPU pour le LLM Qwen 14B
pip install -q --no-cache-dir "numpy<2.0.0" -r requirements.txt
CMAKE_ARGS="-DGGML_CUDA=on -DGGML_AVX512=off" pip install -q --no-binary llama-cpp-python --no-cache-dir --force-reinstall llama-cpp-python
pip install -q --no-cache-dir faster-whisper ctranslate2 soundfile

# 3. Installation optimisée de LivePortrait pour inférence en mémoire
cd /dev/shm
if [ ! -d "LivePortrait" ]; then
    echo "📦 Clonage de LivePortrait dans la RAM (/dev/shm)..."
    git clone --depth 1 https://github.com/KwaiVGI/LivePortrait.git
fi

cd LivePortrait
pip install -q --no-cache-dir -r requirements.txt

# Restauration immédiate des versions requises par AlternIA (évite les conflits LivePortrait)
pip install -q --no-cache-dir "numpy<2.0.0" "transformers>=4.46.0,<4.49.0" "sentence-transformers>=3.3.0" "huggingface-hub>=0.24.0,<0.28.0" "markupsafe~=2.0" "websockets<13.0"

echo "📥 Téléchargement des checkpoints pré-entraînés LivePortrait..."
python3 -c "
from huggingface_hub import snapshot_download
snapshot_download(repo_id='KwaiVGI/LivePortrait', local_dir='pretrained_weights', allow_patterns=['*.safetensors', '*.pth', '*.json', '*.yaml'])
" || true

# 4. Purge des résidus d'installation pour préserver l'espace disque
pip cache purge >/dev/null 2>&1 || true

echo "✅ Environnement LivePortrait In-Memory (Zero-Disk) prêt avec succès !"
