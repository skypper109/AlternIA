#!/bin/bash
# ==============================================================================
# Script d'Installation & Configuration Optimisée pour Serveur AWS EC2 g4dn.2xlarge
# Spécifications : NVIDIA T4 (16 Go VRAM) | 8 vCPUs | 32 Go RAM | Ubuntu 22.04 LTS
# Rôle : Remplace le serveur RunPod Ada pour l'inférence locale Qwen + LivePortrait
# ==============================================================================

set -e

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${GREEN}   🚀  ALTERNIA — INSTALLATION SERVEUR AWS GPU g4dn.2xlarge (NVIDIA T4)  🚀${NC}"
echo -e "${YELLOW}   📌  Script Version 2.2 — Patch PyTorch CUDA 12 & Python 3.10/3.11 Certifié${NC}"
echo -e "${BLUE}==============================================================================${NC}"

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Veuillez exécuter ce script avec les droits root (sudo ./setup_aws_g4dn_gpu.sh)${NC}"
    exit 1
fi

REAL_USER=${SUDO_USER:-ubuntu}
USER_HOME=$(eval echo "~$REAL_USER")
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Purge préventive immédiate si un .venv sous Python 3.14 réside dans le projet
if [ -d "$APP_DIR/.venv/lib/python3.14" ] || [ -d "$APP_DIR/.venv/lib/python3.13" ]; then
    echo -e "${YELLOW}🗑️ Détection et suppression immédiate du vieux .venv (Python 3.14 incompatible avec PyTorch)...${NC}"
    rm -rf "$APP_DIR/.venv"
fi

echo -e "\n${BLUE}[1/7] Optimisation du noyau Linux et configuration Swap (4 Go)...${NC}"
if [ ! -f /swapfile ]; then
    fallocate -l 4G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo "✅ Swap 4 Go configuré pour sécuriser les 32 Go de RAM."
fi

cat << 'EOF' > /etc/sysctl.d/99-alternia-gpu.conf
vm.max_map_count=262144
vm.swappiness=10
net.core.somaxconn=65535
fs.file-max=2097152
EOF
sysctl --system > /dev/null
echo "✅ Paramètres noyau appliqués."

echo -e "\n${BLUE}[2/7] Installation des dépendances système & Python compatible PyTorch...${NC}"
apt-get update -y
apt-get install -y \
    build-essential \
    cmake \
    curl \
    git \
    wget \
    tar \
    unzip \
    htop \
    jq \
    software-properties-common \
    libportaudio2 \
    libasound2-dev \
    portaudio19-dev \
    ffmpeg \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-fra

# PyTorch et l'écosystème CUDA ne supportent pas Python 3.13/3.14+.
# Installation garantie de Python 3.10 ou Python 3.11 (Standard IA)
echo "🔍 Vérification de la compatibilité de la version Python pour PyTorch CUDA..."
if ! which python3.10 > /dev/null 2>&1 && ! which python3.11 > /dev/null 2>&1; then
    echo "⚡ Installation de Python 3.10/3.11 via deadsnakes PPA..."
    add-apt-repository -y ppa:deadsnakes/ppa || true
    apt-get update -y
    apt-get install -y python3.10 python3.10-venv python3.10-dev || apt-get install -y python3.11 python3.11-venv python3.11-dev || true
fi

# Sélection du meilleur interpréteur Python (3.10 > 3.11 > 3.12 > système si <= 3.12)
TARGET_PYTHON=""
for cand in python3.10 python3.11 python3.12; do
    if which "$cand" > /dev/null 2>&1; then
        TARGET_PYTHON=$(which "$cand")
        break
    fi
done

if [ -z "$TARGET_PYTHON" ]; then
    SYS_MAJ_MIN=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "3.10")
    if python3 -c "import sys; sys.exit(0 if sys.version_info < (3, 13) else 1)" 2>/dev/null; then
        TARGET_PYTHON=$(which python3)
    else
        echo -e "${RED}❌ Aucune version de Python compatible avec PyTorch (<= 3.12) trouvée. Installation forcée de python3.10...${NC}"
        apt-get install -y python3.10 python3.10-venv python3.10-dev
        TARGET_PYTHON=$(which python3.10)
    fi
fi
echo -e "✅ Interpréteur Python sélectionné pour l'IA : \033[1;32m$TARGET_PYTHON\033[0m ($($TARGET_PYTHON --version))"

echo -e "\n${BLUE}[3/7] Détection et configuration des pilotes NVIDIA CUDA (T4)...${NC}"
if ! which nvidia-smi > /dev/null 2>&1; then
    echo -e "${YELLOW}⚡ Pilote NVIDIA non détecté. Installation automatique du pilote propriétaire recommandé...${NC}"
    apt-get install -y linux-headers-$(uname -r)
    apt-get install -y nvidia-driver-535 nvidia-utils-535
    echo -e "${YELLOW}⚠️ Pilote NVIDIA installé. Si nvidia-smi ne répond pas immédiatement, un redémarrage ('sudo reboot') peut être requis.${NC}"
else
    echo "✅ GPU NVIDIA détecté avec succès :"
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader || true
fi

# Configuration des variables d'environnement CUDA et installation de nvcc si nécessaire
if ! which nvcc > /dev/null 2>&1; then
    echo "📦 Installation du compilateur CUDA Toolkit (nvcc)..."
    apt-get install -y nvidia-cuda-toolkit || true
fi

NVCC_BIN=$(which nvcc || find /usr -name nvcc 2>/dev/null | head -n 1 || echo "")
CUDA_PATH="/usr/local/cuda"
if [ -n "$NVCC_BIN" ]; then
    CUDA_PATH=$(dirname $(dirname "$NVCC_BIN"))
elif [ ! -d "$CUDA_PATH" ]; then
    for d in /usr/local/cuda-*; do
        if [ -d "$d" ]; then
            CUDA_PATH="$d"
            break
        fi
    done
fi
export CUDAToolkit_ROOT="$CUDA_PATH"
export CUDA_HOME="$CUDA_PATH"
export PATH="${CUDA_PATH}/bin:$PATH"
export LD_LIBRARY_PATH="${CUDA_PATH}/lib64:${CUDA_PATH}/lib:$LD_LIBRARY_PATH"

cat << EOF > /etc/profile.d/cuda.sh
export PATH=${CUDA_PATH}/bin:\$PATH
export LD_LIBRARY_PATH=${CUDA_PATH}/lib64:${CUDA_PATH}/lib:\$LD_LIBRARY_PATH
export CUDA_HOME=${CUDA_PATH}
export CUDAToolkit_ROOT=${CUDA_PATH}
EOF

echo -e "\n${BLUE}[4/7] Installation de Cloudflare Tunnel (cloudflared)...${NC}"
if ! which cloudflared > /dev/null 2>&1; then
    curl -L --output /tmp/cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    dpkg -i /tmp/cloudflared.deb
    rm -f /tmp/cloudflared.deb
    echo "✅ cloudflared binaire installé."
else
    echo "ℹ️ cloudflared déjà présent."
fi

echo -e "\n${BLUE}[5/7] Configuration de l'environnement Python & compilation llama-cpp CUDA...${NC}"
cd "$APP_DIR"
chown -R "$REAL_USER:$REAL_USER" "$APP_DIR"

# Vérification et purge de l'ancien .venv s'il a été créé avec Python 3.13/3.14 incompatible
if [ -d ".venv" ]; then
    VENV_IS_COMPATIBLE=true
    if [ -f ".venv/bin/python3" ]; then
        if ! .venv/bin/python3 -c "import sys; sys.exit(0 if (3, 8) <= sys.version_info < (3, 13) else 1)" 2>/dev/null; then
            VENV_IS_COMPATIBLE=false
        fi
    else
        VENV_IS_COMPATIBLE=false
    fi

    if [ "$VENV_IS_COMPATIBLE" = false ]; then
        echo -e "${YELLOW}🔄 Ancien .venv détecté avec une version incompatible (ex: Python 3.14). Purge et recréation propre...${NC}"
        rm -rf .venv
    fi
fi

if [ ! -d ".venv" ]; then
    sudo -u "$REAL_USER" "$TARGET_PYTHON" -m venv .venv
    echo -e "✅ Environnement virtuel '.venv' créé avec \033[1;32m$($TARGET_PYTHON --version)\033[0m."
fi

echo "📦 Installation de PyTorch avec support CUDA 12..."
sudo -u "$REAL_USER" .venv/bin/pip install --upgrade pip
sudo -u "$REAL_USER" .venv/bin/pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

echo "⚡ Installation de llama-cpp-python avec accélération matérielle NVIDIA CUDA..."
LLAMA_INSTALLED=false

# 1. Tentative d'installation directe via wheel précompilé CUDA (rapide, fiable, sans besoin de compiler)
for cu_ver in cu121 cu122 cu124 cu120; do
    if sudo -u "$REAL_USER" .venv/bin/pip install llama-cpp-python \
        --extra-index-url "https://abetlen.github.io/llama-cpp-python/whl/${cu_ver}" \
        --no-cache-dir; then
        echo "✅ llama-cpp-python installé avec succès via wheel précompilé ($cu_ver) !"
        LLAMA_INSTALLED=true
        break
    fi
done

# 2. Si le wheel précompilé n'est pas disponible, compilation locale avec nvcc
if [ "$LLAMA_INSTALLED" = false ]; then
    echo "⚡ Compilation locale de llama-cpp-python avec nvcc (CUDA)..."
    sudo -u "$REAL_USER" bash -c "
    export PATH=${CUDA_PATH}/bin:\$PATH
    export LD_LIBRARY_PATH=${CUDA_PATH}/lib64:${CUDA_PATH}/lib:\$LD_LIBRARY_PATH
    export CUDA_HOME=${CUDA_PATH}
    export CUDAToolkit_ROOT=${CUDA_PATH}
    export CMAKE_ARGS=\"-DGGML_CUDA=on -DGGML_AVX512=off\"
    .venv/bin/pip install --no-cache-dir --force-reinstall --no-binary llama-cpp-python llama-cpp-python
    "
fi

echo "📦 Installation des dépendances du projet AlternIA..."
sudo -u "$REAL_USER" .venv/bin/pip install -q \
    numpy==1.26.4 \
    scipy==1.13.1 \
    scikit-learn \
    opencv-python-headless \
    fastapi \
    uvicorn[standard] \
    pydantic-settings \
    sentence-transformers \
    edge-tts \
    python-multipart \
    faster-whisper \
    simli-ai \
    qdrant-client

echo -e "\n${BLUE}[6/7] Téléchargement du modèle Qwen 2.5 embarqué (GGUF)...${NC}"
MODELS_DIR="$APP_DIR/ai-engine/models/llm"
sudo -u "$REAL_USER" mkdir -p "$MODELS_DIR"

# Modèle recommandé pour g4dn (16 Go VRAM) : Qwen 2.5 7B Instruct (Q4_K_M ~4.5 Go)
MODEL_7B="$MODELS_DIR/qwen2.5-7b-instruct-q4_k_m.gguf"
MODEL_3B="$MODELS_DIR/qwen2.5-3b-instruct-q4_k_m.gguf"

if [ ! -f "$MODEL_7B" ] && [ ! -f "$MODEL_3B" ]; then
    echo -e "${YELLOW}📥 Téléchargement de Qwen 2.5 7B Instruct (Optimisé pour VRAM 16 Go T4)...${NC}"
    sudo -u "$REAL_USER" curl -L -o "$MODEL_7B" \
        "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf"
    echo "✅ Modèle Qwen 2.5 7B téléchargé avec succès."
else
    echo "ℹ️ Modèle local déjà présent dans $MODELS_DIR."
fi

echo -e "\n${BLUE}[7/7] Création des raccourcis de démarrage interactifs...${NC}"
# 1. Raccourci GPU (T4 VRAM)
cat << 'EOF' > "$APP_DIR/start_gpu.sh"
#!/bin/bash
cd "$(dirname "$0")"
echo -e "\033[1;32m🚀 Démarrage d'AlternIA sur GPU NVIDIA T4 (16 Go VRAM) - Qwen Embarqué (Zéro API)\033[0m"
.venv/bin/python3 cloud/colab_server.py --local --device gpu --quick "$@"
EOF
chmod +x "$APP_DIR/start_gpu.sh"
chown "$REAL_USER:$REAL_USER" "$APP_DIR/start_gpu.sh"

# 2. Raccourci CPU (8 vCPUs / 32 Go RAM)
cat << 'EOF' > "$APP_DIR/start_cpu.sh"
#!/bin/bash
cd "$(dirname "$0")"
echo -e "\033[1;33m⚙️ Démarrage d'AlternIA sur CPU (8 vCPUs) - VRAM 100% libre pour LivePortrait\033[0m"
.venv/bin/python3 cloud/colab_server.py --local --device cpu --quick "$@"
EOF
chmod +x "$APP_DIR/start_cpu.sh"
chown "$REAL_USER:$REAL_USER" "$APP_DIR/start_cpu.sh"

echo -e "\n${GREEN}==============================================================================${NC}"
echo -e "${GREEN}  🎉 SERVEUR AWS g4dn.2xlarge CONFIGURÉ AVEC SUCCÈS !                         ${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo -e "Deux commandes prêtes à l'emploi ont été créées dans votre dossier AlternIA :\n"
echo -e "  1. ${PURPLE}./start_gpu.sh${NC}"
echo -e "     -> Exécute Qwen 2.5 à 100% sur la carte GPU NVIDIA T4 (35 à 50 tokens/s)."
echo -e "     -> ZÉRO appel vers Groq ou Gemini. 100% Hors-Ligne / Local."
echo -e "     -> Génère un tunnel Cloudflare temporaire (ne perturbe pas votre serveur t3.xlarge).\n"
echo -e "  2. ${YELLOW}./start_cpu.sh${NC}"
echo -e "     -> Exécute Qwen 2.5 sur vos 8 vCPUs et 32 Go de RAM."
echo -e "     -> Laisse 100% des 16 Go de VRAM libres pour la génération vidéo LivePortrait."
echo -e "\nPour lancer immédiatement : ${BLUE}./start_gpu.sh${NC}"
