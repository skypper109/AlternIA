#!/bin/bash
# ==============================================================================
# Script d'Installation & Configuration du Kiosk TV HDMI — AlternIA Box (Pi 5)
# Permet l'affichage automatique plein écran sur TV avec synchronisation boutons,
# support souris et clavier USB.
# ==============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}══════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  🇲🇱 Configuration de l'Affichage TV HDMI Kiosk — AlternIA Box      ${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════════════════${NC}"

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Ce script doit être exécuté avec les privilèges root (sudo).${NC}"
    exit 1
fi

TARGET_USER="ubuntu"
if ! id "$TARGET_USER" >/dev/null 2>&1; then
    TARGET_USER="${SUDO_USER:-$USER}"
fi

echo -e "\n${YELLOW}📦 1. Installation des paquets graphiques requis...${NC}"
apt-get update -qq
apt-get install -y -qq chromium-browser unclutter x11-xserver-utils curl || apt-get install -y -qq chromium unclutter x11-xserver-utils curl

echo -e "\n${YELLOW}⚙️ 2. Configuration du démarrage graphique automatique (Auto-Login)...${NC}"
systemctl set-default graphical.target

# Configuration Auto-Login LightDM si présent
if [ -f /etc/lightdm/lightdm.conf ]; then
    sed -i "s/^#autologin-user=.*/autologin-user=$TARGET_USER/" /etc/lightdm/lightdm.conf 2>/dev/null || true
    sed -i "s/^autologin-user=.*/autologin-user=$TARGET_USER/" /etc/lightdm/lightdm.conf 2>/dev/null || true
fi

# Configuration Auto-Login GDM si présent
if [ -f /etc/gdm3/custom.conf ]; then
    sed -i "s/AutomaticLoginEnable = false/AutomaticLoginEnable = true/" /etc/gdm3/custom.conf 2>/dev/null || true
    sed -i "s/AutomaticLogin = .*/AutomaticLogin = $TARGET_USER/" /etc/gdm3/custom.conf 2>/dev/null || true
fi

# Recherche du dossier Alternia / AlternIA
REPO_DIR=""
for candidate in "/home/$TARGET_USER/Alternia" "/home/$TARGET_USER/AlternIA" "/root/Alternia" "/root/AlternIA"; do
    if [ -d "$candidate/raspberry-pi/kiosk" ]; then
        REPO_DIR="$candidate"
        break
    fi
done

if [ -z "$REPO_DIR" ]; then
    echo -e "${RED}❌ Impossible de trouver le dossier du projet AlternIA dans /home/$TARGET_USER/.${NC}"
    exit 1
fi

chmod +x "$REPO_DIR/raspberry-pi/kiosk/launch_kiosk.sh"
chown -R "$TARGET_USER:$TARGET_USER" "$REPO_DIR/raspberry-pi/kiosk/launch_kiosk.sh"

echo -e "\n${YELLOW}🚀 3. Installation et activation du service systemd alta-kiosk...${NC}"
cp "$REPO_DIR/raspberry-pi/systemd/alta-kiosk.service" /etc/systemd/system/alta-kiosk.service
systemctl daemon-reload
systemctl enable alta-kiosk.service
systemctl restart alta-kiosk.service || true

echo -e "\n${GREEN}══════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ KIOSK TV HDMI CONFIGURÉ AVEC SUCCÈS !                          ${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════════════════════════${NC}"
echo -e "  • URL affichée sur la TV : ${BLUE}https://device.alterniamali.com${NC}"
echo -e "  • Mode secours hors-ligne: ${BLUE}http://127.0.0.1/${NC}"
echo -e "  • Synchronisation boutons: ${GREEN}Active en temps réel (WebSocket & Bus matériel)${NC}"
echo -e "  • Support souris/clavier : ${GREEN}Actif (curseur masqué à l'inactivité, visible au mouvement)${NC}"
echo -e "  • Statut du service      : ${YELLOW}sudo systemctl status alta-kiosk.service${NC}\n"
