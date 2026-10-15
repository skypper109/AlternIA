#!/bin/bash
# ==============================================================================
# AWS EC2 Cloud-Init User Data Script pour Instance t3.xlarge (Ubuntu 22.04 / 24.04 LTS)
# Déploiement 100% Automatique sans intervention ("Zero-Touch Launch")
# Collez ce script dans : Console AWS EC2 > Lancer une instance > Détails avancés > Données utilisateur
# ==============================================================================

set -e
exec > >(tee /var/log/alternia-cloud-init.log|logger -t alternia-init -s 2>/dev/console) 2>&1

echo "=============================================================================="
echo "  🇲🇱  ALTERNIA — DÉPLOIEMENT AUTOMATIQUE SERVEUR AWS EC2 (t3.xlarge)  🇲🇱"
echo "=============================================================================="

export DEBIAN_FRONTEND=noninteractive

# 1. OPTIMISATIONS NOYAU & MÉMOIRE POUR t3.xlarge (16 Go RAM / 4 vCPUs)
echo "⚡ [1/8] Configuration Swap et paramètres noyau..."
if [ ! -f /swapfile ]; then
    fallocate -l 4G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# Ajustement sysctl pour forte concurrence et recherche vectorielle
cat << 'EOF' > /etc/sysctl.d/99-alternia.conf
vm.max_map_count=262144
vm.swappiness=10
net.core.somaxconn=65535
net.ipv4.tcp_max_syn_backlog=8192
net.ipv4.ip_local_port_range=1024 65535
fs.file-max=2097152
EOF
sysctl --system

# 2. MISE À JOUR DU SYSTÈME & DÉPENDANCES
echo "📦 [2/8] Installation des paquets système..."
apt-get update -y
apt-get upgrade -y
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
    nodejs \
    npm

# 3. INSTALLATION DE CLOUDFLARED (TUNNEL OFFICIEL CLOUDFLARE)
echo "🔒 [3/8] Installation de Cloudflare Tunnel..."
if ! which cloudflared > /dev/null 2>&1; then
    curl -L --output /tmp/cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    dpkg -i /tmp/cloudflared.deb
    rm -f /tmp/cloudflared.deb
fi

# 4. INSTALLATION NATIVE DU MOTEUR VECTORIEL QDRANT (PORT 6333)
echo "🧠 [4/8] Installation native de Qdrant Vector DB..."
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
fi

# 5. CONFIGURATION DU RÉPERTOIRE ALTERNIA
echo "📁 [5/8] Préparation du code source et de l'environnement Python..."
APP_DIR="/home/ubuntu/AlternIA"
mkdir -p "$APP_DIR"
chown -R ubuntu:ubuntu "$APP_DIR"

# Création du venv Python
sudo -u ubuntu python3 -m venv "$APP_DIR/.venv"
sudo -u ubuntu "$APP_DIR/.venv/bin/pip" install --upgrade pip

# Si le dépôt n'est pas encore cloné, cloner le dépôt GitHub (remplacer par l'URL de votre repo ou copier les sources)
if [ ! -f "$APP_DIR/requirements.txt" ]; then
    echo "ℹ️ En attente du code dans $APP_DIR. Les services démarreront dès synchronisation."
fi

# 6. DÉPLOIEMENT DES SERVICES SYSTEMD AUTO-START
echo "⚙️ [6/8] Installation et activation des services systemd..."

# Service Qdrant
cat << 'EOF' > /etc/systemd/system/qdrant.service
[Unit]
Description=Qdrant Vector Database Engine
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=qdrant
Group=qdrant
WorkingDirectory=/var/lib/qdrant
ExecStart=/usr/local/bin/qdrant --config-path /etc/qdrant/config.yaml
Restart=always
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

# Service Backend AlternIA (4 Workers pour t3.xlarge)
cat << 'EOF' > /etc/systemd/system/alternia-backend.service
[Unit]
Description=AlternIA Backend API (FastAPI 4-Workers)
After=network.target network-online.target qdrant.service mysql.service mariadb.service
Wants=network-online.target qdrant.service

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/AlternIA
Environment="PATH=/home/ubuntu/AlternIA/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
EnvironmentFile=-/home/ubuntu/AlternIA/.env
Environment="PYTHONUNBUFFERED=1"
Environment="PYTHONPATH=/home/ubuntu/AlternIA:/home/ubuntu/AlternIA/backend/src:/home/ubuntu/AlternIA/ai-engine/src"
Environment="OMP_NUM_THREADS=4"

ExecStart=/home/ubuntu/AlternIA/.venv/bin/uvicorn backend.src.main:app --host 0.0.0.0 --port 8000 --workers 4 --proxy-headers --forwarded-allow-ips=* --timeout-keep-alive 65

Restart=always
RestartSec=5
KillMode=mixed
TimeoutStopSec=30
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

# Service Cloudflare Tunnel
cat << 'EOF' > /etc/systemd/system/alternia-tunnel.service
[Unit]
Description=AlternIA Cloudflare Tunnel Daemon
After=network.target network-online.target alternia-backend.service
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/ubuntu
EnvironmentFile=-/home/ubuntu/AlternIA/.env
ExecStart=/usr/bin/cloudflared tunnel --no-autoupdate run --token ${CLOUDFLARE_TUNNEL_TOKEN}
Restart=always
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

# Service Watchdog Auto-Healing
cat << 'EOF' > /etc/systemd/system/alternia-watchdog.service
[Unit]
Description=AlternIA Auto-Healing Watchdog Service
After=alternia-backend.service

[Service]
Type=oneshot
ExecStart=/bin/bash -c "curl -sf --max-time 5 http://127.0.0.1:8000/docs > /dev/null || systemctl restart alternia-backend.service"
EOF

cat << 'EOF' > /etc/systemd/system/alternia-watchdog.timer
[Unit]
Description=AlternIA Watchdog Timer
After=alternia-backend.service

[Timer]
OnBootSec=1min
OnUnitActiveSec=30s
AccuracySec=5s

[Install]
WantedBy=timers.target
EOF

# 7. ACTIVATION GLOBALE AU BOOT DE L'INSTANCE AWS
echo "🔄 [7/8] Activation au démarrage de la machine..."
systemctl daemon-reload
systemctl enable qdrant.service
systemctl enable alternia-backend.service
systemctl enable alternia-tunnel.service
systemctl enable alternia-watchdog.timer

systemctl restart qdrant.service || true

echo "=============================================================================="
echo "🎉 [8/8] CONFIGURATION TERMINÉE ! TOUT DÉMARRERA AUTOMATIQUEMENT AU BOOT !"
echo "=============================================================================="
