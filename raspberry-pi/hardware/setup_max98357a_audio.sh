#!/bin/bash
# ==============================================================================
# Script d'Activation Automatique du Pilote I2S MAX98357A sur Raspberry Pi 5
# Active la carte son numérique I2S DAC pour le haut-parleur AlternIA Box
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${GREEN}   🔊  ACTIVATION DE L'AMPLIFICATEUR AUDIO I2S MAX98357A (Pi 5)  🔊${NC}"
echo -e "${BLUE}==============================================================================${NC}"

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Exécutez ce script avec sudo (sudo ./setup_max98357a_audio.sh)${NC}"
    exit 1
fi

# 1. Localisation du fichier config.txt (Bookworm utilise /boot/firmware/config.txt)
CONFIG_FILE="/boot/firmware/config.txt"
if [ ! -f "$CONFIG_FILE" ]; then
    CONFIG_FILE="/boot/config.txt"
fi

echo -e "⚙️ Configuration de l'overlay dans \033[1;33m$CONFIG_FILE\033[0m..."

# Désactiver la sortie audio HDMI/Casque par défaut si besoin
sed -i 's/^dtparam=audio=on/#dtparam=audio=on/' "$CONFIG_FILE" 2>/dev/null || true

# Ajouter l'overlay MAX98357A si non présent
if ! grep -q "dtoverlay=max98357a" "$CONFIG_FILE"; then
    cat << 'EOF' >> "$CONFIG_FILE"

# ── Module Audio I2S MAX98357A (AlternIA Box) ──
dtoverlay=max98357a
EOF
    echo "✅ Overlay 'dtoverlay=max98357a' ajouté à $CONFIG_FILE."
else
    echo "ℹ️ Overlay max98357a déjà configuré dans $CONFIG_FILE."
fi

# 2. Configuration ALSA par défaut (/etc/asound.conf)
cat << 'EOF' > /etc/asound.conf
pcm.!default {
    type plug
    slave.pcm "dmixer"
}

pcm.dmixer {
    type dmix
    ipc_key 1024
    slave {
        pcm "hw:MAX98357A"
        channels 2
        rate 44100
    }
    bindings {
        0 0
        1 1
    }
}

ctl.!default {
    type hw
    card "MAX98357A"
}
EOF
echo "✅ Fichier ALSA /etc/asound.conf configuré avec succès."

# 3. Installation des outils ALSA si absents
apt-get update -y -q
apt-get install -y -q alsa-utils mpg123 sox libsox-fmt-all

echo -e "\n${GREEN}==============================================================================${NC}"
echo -e "${GREEN}  🎉 PILOTE I2S MAX98357A ACTIVÉ AVEC SUCCÈS !                                ${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo -e "⚠️ Pour que le noyau Linux charge le pilote I2S, un redémarrage est nécessaire :"
echo -e "   👉 ${BLUE}sudo reboot${NC}\n"
echo -e "Après le redémarrage, testez le haut-parleur avec :"
echo -e "   👉 ${YELLOW}speaker-test -t sine -f 440 -l 1${NC}"
