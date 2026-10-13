#!/bin/bash
# ==============================================================================
# Script d'Installation Automatique - AlternIA Box pour Raspberry Pi 3
# Compatible Raspberry Pi OS (Bullseye / Bookworm - 32-bit & 64-bit)
# ==============================================================================

set -e

# Couleurs pour l'affichage
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================================================${NC}"
echo -e "${GREEN}  🇲🇱  INSTALLATION D'ALTERNIA BOX SUR RASPBERRY PI 3  🇲🇱${NC}"
echo -e "${BLUE}=====================================================================${NC}"

# 1. Vérification des droits
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}⚠️ Veuillez lancer ce script en tant qu'utilisateur standard (ex: pi), pas en root.${NC}"
    echo "Le script demandera sudo lorsque nécessaire."
    exit 1
fi

CURRENT_USER=$(whoami)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "\n${BLUE}[1/6] Mise à jour des dépôts APT...${NC}"
sudo apt update -y

echo -e "\n${BLUE}[2/6] Installation des dépendances système (Audio, GPIO, Utilitaires)...${NC}"
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-rpi.gpio \
    alsa-utils \
    libasound2-dev \
    portaudio19-dev \
    libportaudio2 \
    mpg123 \
    espeak-ng \
    curl \
    git

# Outils graphiques pour le mode Kiosk (si environnement de bureau installé)
if which Xorg > /dev/null 2>&1 || which startx > /dev/null 2>&1; then
    echo -e "${YELLOW}-> Environnement graphique détecté : installation des outils Kiosk...${NC}"
    sudo apt install -y chromium-browser unclutter x11-xserver-utils || true
fi

echo -e "\n${BLUE}[3/6] Configuration des permissions matérielles pour l'utilisateur '${CURRENT_USER}'...${NC}"
sudo usermod -a -G audio,gpio "${CURRENT_USER}" || true

echo -e "\n${BLUE}[4/6] Création de l'environnement virtuel Python (venv)...${NC}"
cd "$SCRIPT_DIR"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Environnement virtuel 'venv' créé."
else
    echo "ℹ️ Environnement virtuel 'venv' existant réutilisé."
fi

# Activation de l'environnement virtuel
source venv/bin/activate

echo -e "\n${BLUE}[5/6] Installation des paquets Python via pip...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Rendre les scripts exécutables
chmod +x rpi_client.py test_gpio.py test_audio.py start_kiosk.sh install.sh

echo -e "\n${BLUE}[6/6] Configuration du service automatique (Optionnel)...${NC}"
read -p "Voulez-vous activer le démarrage automatique d'AlternIA au boot ? (o/N) : " ENABLE_SERVICE
if [[ "$ENABLE_SERVICE" =~ ^[oOyY]$ ]]; then
    # Ajuster le chemin dans le fichier service si nécessaire
    SERVICE_FILE="/etc/systemd/system/alternia-box.service"
    sudo cp alternia-box.service "$SERVICE_FILE"
    sudo sed -i "s|/home/pi/alternia-rpi|$SCRIPT_DIR|g" "$SERVICE_FILE"
    sudo sed -i "s|User=pi|User=$CURRENT_USER|g" "$SERVICE_FILE"
    sudo systemctl daemon-reload
    sudo systemctl enable alternia-box.service
    echo -e "${GREEN}✅ Service systemd 'alternia-box.service' activé et prêt !${NC}"
else
    echo "ℹ️ Service non activé. Vous pourrez lancer l'application manuellement avec ./rpi_client.py"
fi

echo -e "\n${GREEN}=====================================================================${NC}"
echo -e "${GREEN}  🎉 INSTALLATION TERMINÉE AVEC SUCCÈS SUR VOTRE RASPBERRY PI 3 !   ${NC}"
echo -e "${GREEN}=====================================================================${NC}"
echo -e "Pour tester le matériel :"
echo -e "  1. Test Audio (Micro & HP) : ${YELLOW}./venv/bin/python3 test_audio.py${NC}"
echo -e "  2. Test GPIO (Boutons & LEDs) : ${YELLOW}./venv/bin/python3 test_gpio.py${NC}"
echo -e "  3. Lancer AlternIA Box : ${YELLOW}./venv/bin/python3 rpi_client.py${NC}"
echo -e "  4. Lancer l'Écran Kiosk Tactile : ${YELLOW}./start_kiosk.sh${NC}"
echo -e "\n💡 N'oubliez pas d'ajuster l'adresse du serveur dans ${YELLOW}config.py${NC} si votre backend tourne sur un autre PC !"
