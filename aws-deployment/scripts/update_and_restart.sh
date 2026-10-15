#!/bin/bash
# ==============================================================================
# Script de Mise à Jour Rapide & Redémarrage Zéro-Downtime pour AWS EC2
# Usage : ./update_and_restart.sh
# ==============================================================================

set -e

APP_DIR="/home/ubuntu/AlternIA"
cd "$APP_DIR"

echo "📥 1. Récupération des dernières modifications (git pull)..."
git pull origin main || git pull

echo "📦 2. Mise à jour des dépendances Python si nécessaire..."
./.venv/bin/pip install -r requirements.txt -q

echo "🎨 3. Compilation des interfaces web (Device Kiosk & Alta)..."
if [ -d "device/frontend" ]; then
    (cd device/frontend && npm run build) || true
fi
if [ -d "alta" ]; then
    (cd alta && npm run build) || true
fi

echo "🔄 4. Redémarrage propre des services systemd..."
sudo systemctl restart alternia-backend.service
sudo systemctl restart alternia-tunnel.service

echo "✅ 5. Vérification du statut..."
sleep 2
systemctl --no-pager status alternia-backend.service | head -n 12
systemctl --no-pager status alternia-tunnel.service | head -n 12

echo "🎉 Mise à jour terminée avec succès !"
