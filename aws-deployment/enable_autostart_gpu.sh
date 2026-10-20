#!/bin/bash
# ==============================================================================
# Script d'Activation du Service Auto-Start pour AWS g4dn.2xlarge
# Dès que l'instance démarre, AlternIA se lance automatiquement sans commande.
# Usage : chmod +x enable_autostart_gpu.sh && sudo ./enable_autostart_gpu.sh
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Veuillez exécuter ce script avec les droits root (sudo ./enable_autostart_gpu.sh)${NC}"
    exit 1
fi

REAL_USER=${SUDO_USER:-ubuntu}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVICE_FILE="/etc/systemd/system/alternia-gpu.service"

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${GREEN}   ⚙️  ACTIVATION DU SERVICE AUTO-START ALTERNIA GPU (systemd)  ⚙️${NC}"
echo -e "${BLUE}==============================================================================${NC}"

# 1. Copier le service
cp "$SCRIPT_DIR/systemd/alternia-gpu.service" "$SERVICE_FILE"

# 2. Ajuster automatiquement les chemins et l'utilisateur
sed -i "s|User=ubuntu|User=$REAL_USER|g" "$SERVICE_FILE"
sed -i "s|Group=ubuntu|Group=$REAL_USER|g" "$SERVICE_FILE"
sed -i "s|/home/ubuntu/AlternIA|$APP_DIR|g" "$SERVICE_FILE"

echo "✅ Fichier service configuré dans $SERVICE_FILE :"
grep -E "User=|WorkingDirectory=|ExecStart=" "$SERVICE_FILE"

# 3. Arrêter tout ancien processus manuel
killall cloudflared 2>/dev/null || true
pkill -f "colab_server.py" 2>/dev/null || true

# 4. Recharger et activer au démarrage
systemctl daemon-reload
systemctl enable alternia-gpu.service

# 5. Démarrer immédiatement le service
echo -e "\n${BLUE}🚀 Démarrage immédiat du service alternia-gpu...${NC}"
systemctl restart alternia-gpu.service
sleep 3

# 6. Vérification du statut
echo -e "\n${GREEN}==============================================================================${NC}"
echo -e "${GREEN}  🎉 LE SERVICE EST DÉSORMAIS ACTIF ET PERMANENT AU DÉMARRAGE !               ${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo -e "État du service :"
systemctl --no-pager status alternia-gpu.service | head -n 12

echo -e "\n${YELLOW}💡 COMPORTEMENT GARANTI :${NC}"
echo -e "  • Dès que vous allumez votre serveur AWS, le script se lance en 5 secondes."
echo -e "  • En cas de redémarrage (reboot) ou crash inattendu, systemd le relance automatiquement."
echo -e "  • Pour voir les logs en direct à tout moment :"
echo -e "    ${BLUE}sudo journalctl -u alternia-gpu -f${NC}"
echo -e "  • Pour arrêter / redémarrer le service :"
echo -e "    ${BLUE}sudo systemctl stop alternia-gpu${NC}"
echo -e "    ${BLUE}sudo systemctl restart alternia-gpu${NC}"
