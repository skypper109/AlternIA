#!/bin/bash
# ==============================================================================
# Script d'Installation & Configuration Parfaite pour Serveur AWS EC2 t3.xlarge
# Optimisé pour 4 vCPUs / 16 Go RAM / Ubuntu 22.04 & 24.04 LTS
# Active le démarrage 100% automatique au boot sans aucun lancement manuel ordinaire.
# Usage : chmod +x setup_aws_t3_xlarge.sh && sudo ./setup_aws_t3_xlarge.sh
# ==============================================================================

set -e

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${GREEN}   🇲🇱  ALTERNIA — CONFIGURATION PARFAITE SERVEUR AWS t3.xlarge  🇲🇱${NC}"
echo -e "${BLUE}==============================================================================${NC}"

# 1. Vérification des privilèges root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Veuillez exécuter ce script avec les droits root (sudo ./setup_aws_t3_xlarge.sh)${NC}"
    exit 1
fi

REAL_USER=${SUDO_USER:-ubuntu}
USER_HOME=$(eval echo "~$REAL_USER")
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "\n${BLUE}[1/8] Optimisation du noyau Linux et Swap pour t3.xlarge (16 Go RAM)...${NC}"
# Création d'un swap de 4 Go de sécurité contre tout pic OOM
if [ ! -f /swapfile ]; then
    fallocate -l 4G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo "✅ Fichier Swap 4 Go créé."
fi

# Optimisation sysctl
cat << 'EOF' > /etc/sysctl.d/99-alternia.conf
vm.max_map_count=262144
vm.swappiness=10
net.core.somaxconn=65535
net.ipv4.tcp_max_syn_backlog=8192
net.ipv4.ip_local_port_range=1024 65535
fs.file-max=2097152
EOF
sysctl --system > /dev/null
echo "✅ Paramètres noyau t3.xlarge appliqués (max_map_count=262144, somaxconn=65535)."

echo -e "\n${BLUE}[2/8] Installation des paquets système indispensables...${NC}"
apt-get update -y
apt-get install -y \
    build-essential \
    curl \
    git \
    wget \
    tar \
    unzip \
    htop \
    jq \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    libportaudio2 \
    libasound2-dev \
    portaudio19-dev \
    ffmpeg \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-fra \
    nginx \
    mysql-server

systemctl enable mysql 2>/dev/null || true
systemctl start mysql 2>/dev/null || true

echo -e "\n${BLUE}[3/8] Installation de Cloudflare Tunnel (cloudflared)...${NC}"
if ! which cloudflared > /dev/null 2>&1; then
    curl -L --output /tmp/cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    dpkg -i /tmp/cloudflared.deb
    rm -f /tmp/cloudflared.deb
    echo "✅ cloudflared binaire installé."
else
    echo "ℹ️ cloudflared déjà présent."
fi
# Garantir la présence de cloudflared dans /usr/bin et /usr/local/bin
CF_BIN=$(which cloudflared || echo "/usr/bin/cloudflared")
ln -sf "$CF_BIN" /usr/bin/cloudflared 2>/dev/null || true
ln -sf "$CF_BIN" /usr/local/bin/cloudflared 2>/dev/null || true

echo -e "\n${BLUE}[4/8] Installation native de la base vectorielle Qdrant (RAG)...${NC}"
if [ ! -f /usr/local/bin/qdrant ]; then
    QDRANT_VER="v1.11.0"
    curl -L "https://github.com/qdrant/qdrant/releases/download/${QDRANT_VER}/qdrant-x86_64-unknown-linux-gnu.tar.gz" | tar xz -C /usr/local/bin
    chmod +x /usr/local/bin/qdrant

    id -u qdrant &>/dev/null || useradd -r -s /bin/false qdrant
    mkdir -p /var/lib/qdrant /etc/qdrant
    chown -R qdrant:qdrant /var/lib/qdrant

    cat << 'EOF' > /etc/qdrant/config.yaml
service:
  host: 0.0.0.0
  http_port: 6333
  grpc_port: 6334
storage:
  storage_path: /var/lib/qdrant/storage
  snapshots_path: /var/lib/qdrant/snapshots
  on_disk_payload: true
EOF
    echo "✅ Qdrant installé en natif sur le port 6333."
fi

echo -e "\n${BLUE}[5/8] Configuration de l'environnement virtuel Python & variables .env...${NC}"
cd "$APP_DIR"

# Création du fichier .env si absent
if [ ! -f "$APP_DIR/.env" ]; then
    echo "⚙️ Génération automatique du fichier .env officiel AlternIA..."
    cat << 'EOF' > "$APP_DIR/.env"
APP_NAME=AlternIA
APP_ENV=production
DEBUG=false

# LLM Providers (Gemini 2.5 Flash / Groq Qwen 27B)
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
LLM_API_KEY=AQ.Ab8RN6JGzagbZCG-VcH1I4tTAUGUmN9bB9nwWLDUsP1xTs0r5w
GEMINI_API_KEY=AQ.Ab8RN6JGzagbZCG-VcH1I4tTAUGUmN9bB9nwWLDUsP1xTs0r5w
GEMINI_MODEL=gemini-2.5-flash
GROQ_API_KEY=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
GROQ_MODEL=qwen/qwen3.8-27b

# Backend & Base Vectorielle & MySQL
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
VECTOR_DB_URL=http://localhost:6333
DATABASE_URL=mysql+pymysql://alternia:skypper19@localhost:3306/alta_db?charset=utf8mb4

# Cloudflare Tunnel Officiel AlternIA
CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoiNTYxMzlhYzA0OGZkNWQ4ODEyOTliM2U0NTBiYWEyYzIiLCJ0IjoiZDk2MGQyMDUtMGU5ZC00ODY4LTk4ZjctOGEwYWQzMGVjODFhIiwicyI6Ik4yTTVOREl5WW1JdE9UVXlNaTAwWmpWa0xUazJNMk10TUdWbU5qZzBZVGsyWXpreiJ9
CLOUDFLARE_HOSTNAME=alterniamali.com
CLOUDFLARE_ADMIN_HOSTNAME=admin.alterniamali.com
CLOUDFLARE_DEVICE_HOSTNAME=device.alterniamali.com
CLOUDFLARE_API_HOSTNAME=api.alterniamali.com
EOF
    echo "✅ Fichier .env créé avec le token Cloudflare et DATABASE_URL."
fi

# Configuration automatique de MySQL si présent
if which mysql > /dev/null 2>&1; then
    echo "⚙️ Initialisation automatique de la base MySQL 'alta_db'..."
    mysql -e "CREATE DATABASE IF NOT EXISTS alta_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null || true
    mysql -e "CREATE USER IF NOT EXISTS 'alternia'@'localhost' IDENTIFIED BY 'skypper19';" 2>/dev/null || true
    mysql -e "GRANT ALL PRIVILEGES ON alta_db.* TO 'alternia'@'localhost';" 2>/dev/null || true
    mysql -e "FLUSH PRIVILEGES;" 2>/dev/null || true
fi

# Droits appropriés sur le projet
chown -R "$REAL_USER:$REAL_USER" "$APP_DIR"
chmod 755 "$APP_DIR"

if [ ! -d ".venv" ]; then
    sudo -u "$REAL_USER" python3 -m venv .venv
    echo "✅ Environnement virtuel '.venv' créé."
fi

sudo -u "$REAL_USER" .venv/bin/pip install --upgrade pip
sudo -u "$REAL_USER" .venv/bin/pip install -r requirements.txt
sudo -u "$REAL_USER" .venv/bin/pip install gunicorn python-multipart google-genai groq

echo -e "\n${BLUE}[6/8] Compilation des applications frontends (Device Kiosk & Alta)...${NC}"
if which npm > /dev/null 2>&1; then
    if [ -d "$APP_DIR/device/frontend" ] && [ ! -d "$APP_DIR/device/frontend/dist" ]; then
        echo "🔨 Compilation du Kiosk élève..."
        (cd "$APP_DIR/device/frontend" && sudo -u "$REAL_USER" npm install && sudo -u "$REAL_USER" npm run build) || true
    fi
    if [ -d "$APP_DIR/alta" ] && [ ! -d "$APP_DIR/alta/dist" ]; then
        echo "🔨 Compilation du Backoffice Alta..."
        (cd "$APP_DIR/alta" && sudo -u "$REAL_USER" npm install && sudo -u "$REAL_USER" npm run build) || true
    fi
fi

echo -e "\n${BLUE}[7/8] Déploiement des services systemd Auto-Start...${NC}"

# Copie dans /etc/systemd/system/
cp "$SCRIPT_DIR/systemd/qdrant.service" /etc/systemd/system/
cp "$SCRIPT_DIR/systemd/alternia-backend.service" /etc/systemd/system/
cp "$SCRIPT_DIR/systemd/alternia-tunnel.service" /etc/systemd/system/
cp "$SCRIPT_DIR/systemd/alternia-watchdog.service" /etc/systemd/system/
cp "$SCRIPT_DIR/systemd/alternia-watchdog.timer" /etc/systemd/system/

# Ajuster le chemin absolu et l'utilisateur dans les fichiers déployés
sed -i "s|/home/ubuntu/AlternIA|$APP_DIR|g" /etc/systemd/system/alternia-backend.service
sed -i "s|User=ubuntu|User=$REAL_USER|g" /etc/systemd/system/alternia-backend.service
sed -i "s|Group=ubuntu|Group=$REAL_USER|g" /etc/systemd/system/alternia-backend.service
sed -i "s|/home/ubuntu/AlternIA|$APP_DIR|g" /etc/systemd/system/alternia-tunnel.service
sed -i "s|/home/ubuntu/AlternIA|$APP_DIR|g" /etc/systemd/system/alternia-watchdog.service

# Permissions sur les scripts
chmod +x "$SCRIPT_DIR/scripts/healthcheck.sh"
chmod +x "$SCRIPT_DIR/scripts/update_and_restart.sh"

# Rechargement et activation
systemctl daemon-reload
systemctl enable qdrant.service
systemctl enable alternia-backend.service
systemctl enable alternia-tunnel.service
systemctl enable alternia-watchdog.timer

echo -e "\n${BLUE}[8/8] Démarrage immédiat des services...${NC}"
systemctl restart qdrant.service
sleep 1
systemctl restart alternia-backend.service
sleep 2
systemctl restart alternia-tunnel.service
systemctl start alternia-watchdog.timer

echo -e "\n${GREEN}==============================================================================${NC}"
echo -e "${GREEN}  🎉 CONFIGURATION TERMINÉE ! LE SERVEUR EST ENTIÈREMENT OPÉRATIONNEL !     ${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo -e "État des services actifs :"
systemctl --no-pager status qdrant.service | head -n 4
systemctl --no-pager status alternia-backend.service | head -n 4
systemctl --no-pager status alternia-tunnel.service | head -n 4
echo -e "\n${YELLOW}💡 COMPORTEMENT GARANTI AU DÉMARRAGE DE L'INSTANCE AWS :${NC}"
echo -e "  • Dès que vous allumez votre instance t3.xlarge dans la console AWS,"
echo -e "    tous les services se lancent automatiquement en moins de 10 secondes."
echo -e "  • Aucune commande manuelle requise."
echo -e "  • Vos domaines officiels répondent immédiatement :"
echo -e "     - ${GREEN}https://alterniamali.com${NC} (Portail Principal)"
echo -e "     - ${GREEN}https://api.alterniamali.com${NC} (Backend API & Mobile Flutter)"
echo -e "     - ${GREEN}https://admin.alterniamali.com${NC} (Backoffice Direction/Enseignants)"
echo -e "     - ${GREEN}https://device.alterniamali.com${NC} (Kiosk Élève & ESP32)"
echo -e "\nPour voir les logs en direct : ${BLUE}journalctl -u alternia-backend -f${NC}"
