#!/bin/bash
# ==============================================================================
# Script d'Installation & Configuration Tout-en-Un pour Raspberry Pi 5 (8 Go RAM)
# Boîtier Éducatif AlternIA (Alta-Box) — Point d'Accès Wi-Fi "Alta-box1"
# Mot de passe : Bamako+223 | Connecté à https://api.alterniamali.com
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${GREEN}   🇲🇱  ALTERNIA — INSTALLATION DU BOÎTIER WI-FI ALTA-BOX (Raspberry Pi 5) 🇲🇱${NC}"
echo -e "${BLUE}==============================================================================${NC}"

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Veuillez exécuter ce script avec les droits root (sudo ./setup_pi5_hotspot.sh)${NC}"
    exit 1
fi

REAL_USER=${SUDO_USER:-ubuntu}
USER_HOME=$(eval echo "~$REAL_USER")
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "\n${BLUE}[1/7] Mise à jour des dépôts et installation des paquets nécessaires...${NC}"
apt-get update -y
apt-get install -y \
    network-manager \
    nginx \
    curl \
    git \
    wget \
    jq \
    htop \
    iptables \
    iptables-persistent \
    alsa-utils \
    mpg123 \
    python3 \
    python3-pip \
    python3-gpiozero \
    python3-psutil

# Paquets graphiques et GPIO optionnels selon l'édition de Raspberry Pi OS
apt-get install -y gpiod python3-libgpiod 2>/dev/null || true
apt-get install -y chromium-browser 2>/dev/null || apt-get install -y chromium 2>/dev/null || true
apt-get install -y unclutter 2>/dev/null || true

echo -e "\n${BLUE}[2/7] Configuration du Point d'Accès Wi-Fi officiel 'Alta-box1' (NetworkManager)...${NC}"
# S'assurer que NetworkManager contrôle le Wi-Fi
systemctl enable NetworkManager
systemctl start NetworkManager

# Création de l'interface virtuelle uap0 pour diffusion simultanée (AP + STA)
if ! iw dev uap0 info >/dev/null 2>&1; then
    iw dev wlan0 interface add uap0 type __ap 2>/dev/null || true
fi

AP_IFACE="wlan0"
if iw dev uap0 info >/dev/null 2>&1; then
    AP_IFACE="uap0"
    ip link set dev uap0 up 2>/dev/null || true
    echo "📶 Mode Simultané activé : le Pi 5 diffusera 'Alta-box1' sur '$AP_IFACE' tout en restant connecté à votre Wi-Fi de bureau sur 'wlan0' !"
fi

# Suppression d'un ancien profil Hotspot s'il existe
nmcli connection delete "Alta-Hotspot" 2>/dev/null || true

# Création du profil Hotspot WPA2 officiel
nmcli connection add \
    type wifi \
    ifname "$AP_IFACE" \
    con-name "Alta-Hotspot" \
    autoconnect yes \
    ssid "Alta-box1"

nmcli connection modify "Alta-Hotspot" \
    802-11-wireless.mode ap \
    802-11-wireless.band bg \
    wifi-sec.key-mgmt wpa-psk \
    wifi-sec.psk "Bamako+223" \
    ipv4.method shared \
    ipv4.addresses 10.42.0.1/24

# Configuration du résolveur DNS local pour alta.box et redirection portail captif
mkdir -p /etc/NetworkManager/dnsmasq-shared.d
cat << 'EOF' > /etc/NetworkManager/dnsmasq-shared.d/alta-captive.conf
address=/alta.box/10.42.0.1
address=/alterniabox.local/10.42.0.1
EOF

# Démarrage immédiat du hotspot
nmcli connection up "Alta-Hotspot" || true
echo "✅ Point d'Accès Wi-Fi 'Alta-box1' actif sur $AP_IFACE (Pass : Bamako+223 | Passerelle : 10.42.0.1)."

echo -e "\n${BLUE}[3/7] Activation du Routage IP & NAT (Partage Internet vers AWS)...${NC}"
cat << 'EOF' > /etc/sysctl.d/90-alta-routing.conf
net.ipv4.ip_forward=1
net.ipv6.conf.all.forwarding=1
EOF
sysctl -p /etc/sysctl.d/90-alta-routing.conf > /dev/null

# Règles de redirection du portail captif pour le Wi-Fi (redirection vers Nginx local -> https://device.alterniamali.com)
iptables -t nat -C PREROUTING -i "$AP_IFACE" -p tcp --dport 80 -j DNAT --to-destination 10.42.0.1:80 2>/dev/null || \
iptables -t nat -A PREROUTING -i "$AP_IFACE" -p tcp --dport 80 -j DNAT --to-destination 10.42.0.1:80

# Règles de masquerade pour Wi-Fi bureau (wlan0), Ethernet (eth0) et clés 4G USB
iptables -t nat -C POSTROUTING -o wlan0 -j MASQUERADE 2>/dev/null || iptables -t nat -A POSTROUTING -o wlan0 -j MASQUERADE
iptables -t nat -C POSTROUTING -o eth0 -j MASQUERADE 2>/dev/null || iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
iptables -t nat -C POSTROUTING -o usb0 -j MASQUERADE 2>/dev/null || iptables -t nat -A POSTROUTING -o usb0 -j MASQUERADE
iptables -t nat -C POSTROUTING -o wwan0 -j MASQUERADE 2>/dev/null || iptables -t nat -A POSTROUTING -o wwan0 -j MASQUERADE

# Sauvegarde des règles iptables
netfilter-persistent save 2>/dev/null || true
echo "✅ Routage IP, Masquerading NAT et Redirection Portail Captif activés."

echo -e "\n${BLUE}[4/7] Déploiement du Kiosk Élève et Configuration de Nginx Edge...${NC}"
mkdir -p /var/www/alta-kiosk /var/cache/nginx/alta_cache
chown -R www-data:www-data /var/cache/nginx/alta_cache

# Copie des fichiers compilés du Kiosk s'ils existent
if [ -d "$APP_DIR/device/frontend/dist" ]; then
    cp -r "$APP_DIR/device/frontend/dist/"* /var/www/alta-kiosk/
elif [ -d "$APP_DIR/device/frontend" ]; then
    echo "🔨 Compilation du Kiosk élève..."
    (cd "$APP_DIR/device/frontend" && npm install && npm run build) || true
    if [ -d "$APP_DIR/device/frontend/dist" ]; then
        cp -r "$APP_DIR/device/frontend/dist/"* /var/www/alta-kiosk/
    fi
fi

# Copie de la configuration Nginx
cp "$SCRIPT_DIR/nginx/alta-box.conf" /etc/nginx/sites-available/alta-box
ln -sf /etc/nginx/sites-available/alta-box /etc/nginx/sites-enabled/alta-box
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl restart nginx
systemctl enable nginx
echo "✅ Serveur Web Edge Nginx avec cache configuré."

echo -e "\n${BLUE}[5/7] Configuration des Permissions et Droits d'Accès...${NC}"
chmod +x "$SCRIPT_DIR/agent/box_heartbeat.py"
chmod +x "$SCRIPT_DIR/agent/led_indicator.py"
chmod +x "$SCRIPT_DIR/hardware/buttons_audio_controller.py"
chmod +x "$SCRIPT_DIR/hardware/test_hardware.py"
chmod +x "$SCRIPT_DIR/kiosk/launch_kiosk.sh"

chown -R "$REAL_USER:$REAL_USER" "$APP_DIR"

echo -e "\n${BLUE}[6/7] Déploiement des Services Systemd Auto-Start...${NC}"
# Ajuster les chemins dans les fichiers unitaires si besoin
sed -i "s|/home/ubuntu/AlternIA|$APP_DIR|g" "$SCRIPT_DIR/systemd/"*.service || true

cp "$SCRIPT_DIR/systemd/alta-hotspot.service" /etc/systemd/system/
cp "$SCRIPT_DIR/systemd/alta-agent.service" /etc/systemd/system/
cp "$SCRIPT_DIR/systemd/alta-led.service" /etc/systemd/system/
cp "$SCRIPT_DIR/systemd/alta-hardware.service" /etc/systemd/system/

# Service Kiosk uniquement si interface graphique présente
if [ -d /home/"$REAL_USER" ]; then
    cp "$SCRIPT_DIR/systemd/alta-kiosk.service" /etc/systemd/system/
    systemctl enable alta-kiosk.service 2>/dev/null || true
fi

systemctl daemon-reload
systemctl enable alta-hotspot.service
systemctl enable alta-agent.service
systemctl enable alta-led.service
systemctl enable alta-hardware.service

echo -e "\n${BLUE}[7/7] Démarrage immédiat des services du Boîtier...${NC}"
systemctl restart alta-hotspot.service || true
systemctl restart alta-agent.service || true
systemctl restart alta-led.service || true
systemctl restart alta-hardware.service || true

echo -e "\n${GREEN}==============================================================================${NC}"
echo -e "${GREEN}  🎉 LE BOÎTIER RASPBERRY PI 5 EST OPÉRATIONNEL & PRÊT AU DÉPLOIEMENT !     ${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo -e "Informations Réseau du Boîtier :"
echo -e "  • Point d'Accès Wi-Fi : ${GREEN}Alta_box1${NC}"
echo -e "  • Mot de passe Wi-Fi   : ${GREEN}Alta_box2026${NC}"
echo -e "  • Redirection Wi-Fi    : ${BLUE}https://device.alterniamali.com${NC} (Portail Captif automatique)"
echo -e "  • Sortie HDMI (Kiosk)  : ${GREEN}Chromium plein écran sur https://device.alterniamali.com${NC}"
echo -e "  • Serveur Cloud Relié  : ${GREEN}https://api.alterniamali.com${NC}"
echo -e "\nComportement de la LED d'activité :"
echo -e "  • ${YELLOW}Clignotement lent (1 Hz)${NC}      : Démarrage / Recherche de connexion"
echo -e "  • ${GREEN}Lumière fixe / Battement doux${NC} : Connecté au serveur AWS t3.xlarge"
echo -e "  • ${BLUE}Clignotement ultra-rapide${NC}     : Élèves en cours d'interaction / requêtes actives"
echo -e "\nPour tester le matériel (4 boutons + micro + haut-parleur) :"
echo -e "  ${YELLOW}python3 /home/ubuntu/AlternIA/raspberry-pi/hardware/test_hardware.py${NC}"
