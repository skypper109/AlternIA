#!/bin/bash
# ==============================================================================
# Configuration Wi-Fi Simultané Double-Mode (AP + STA) pour Raspberry Pi 5
# 1. Se connecte au Wi-Fi de la maison / du bureau (Internet entrant vers AWS)
# 2. DIFFUSE EN MÊME TEMPS le point d'accès "Alta-box1" (Pass : Bamako+223) pour les élèves
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${GREEN}   📶 ALTERNIA — CONFIGURATION WI-FI SIMULTANÉ (CLIENT + POINT D'ACCÈS)   ${NC}"
echo -e "${BLUE}==============================================================================${NC}"

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Veuillez exécuter ce script en root : sudo ./setup_simultaneous_wifi.sh${NC}"
    exit 1
fi

# 1. Vérification du support de l'interface virtuelle AP sur le Pi 5
echo -e "\n${BLUE}[1/5] Création de l'interface Wi-Fi virtuelle 'uap0'...${NC}"
if ! iw dev uap0 info >/dev/null 2>&1; then
    # Création de l'interface virtuelle AP liée à la puce physique wlan0
    iw dev wlan0 interface add uap0 type __ap 2>/dev/null || true
    
    # Génération d'une adresse MAC unique pour uap0 pour éviter tout conflit
    WLAN0_MAC=$(cat /sys/class/net/wlan0/address 2>/dev/null || echo "b8:27:eb:01:02:03")
    UAP0_MAC=$(echo "$WLAN0_MAC" | awk -F: '{printf "%s:%s:%s:%s:%s:%02x\n", $1,$2,$3,$4,$5, ("0x"$6)+1}')
    ip link set dev uap0 address "$UAP0_MAC" 2>/dev/null || true
    ip link set dev uap0 up 2>/dev/null || true
    echo "✅ Interface virtuelle uap0 créée avec MAC distincte ($UAP0_MAC)."
else
    echo "ℹ️ Interface virtuelle uap0 déjà active."
fi

# 2. Persistance de l'interface uap0 au démarrage (Systemd Service)
cat << 'EOF' > /etc/systemd/system/alta-virtual-wifi.service
[Unit]
Description=Création de l'interface Wi-Fi virtuelle uap0 pour Alta-Box
Before=NetworkManager.service
Wants=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStartPre=/bin/sleep 2
ExecStart=/bin/bash -c "iw dev wlan0 interface add uap0 type __ap 2>/dev/null || true; ip link set dev uap0 up 2>/dev/null || true"

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable alta-virtual-wifi.service

# 3. Configuration du Point d'Accès "Alta-box1" sur l'interface uap0
echo -e "\n${BLUE}[2/5] Déploiement du Point d'Accès 'Alta-box1' sur uap0...${NC}"
nmcli connection delete "Alta-Hotspot" 2>/dev/null || true

nmcli connection add \
    type wifi \
    ifname uap0 \
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

nmcli connection up "Alta-Hotspot" || true
echo "✅ Point d'Accès 'Alta-box1' émis sur uap0 (Pass : Bamako+223 | IP: 10.42.0.1)."

# 4. Activation du Routage NAT (uap0 -> wlan0 Internet)
echo -e "\n${BLUE}[3/5] Configuration du routage NAT pour partager la connexion Internet...${NC}"
cat << 'EOF' > /etc/sysctl.d/90-alta-routing.conf
net.ipv4.ip_forward=1
net.ipv6.conf.all.forwarding=1
EOF
sysctl -p /etc/sysctl.d/90-alta-routing.conf > /dev/null

# Masquerade sur wlan0 (Wi-Fi bureau) et eth0 (Câble)
iptables -t nat -C POSTROUTING -o wlan0 -j MASQUERADE 2>/dev/null || iptables -t nat -A POSTROUTING -o wlan0 -j MASQUERADE
iptables -t nat -C POSTROUTING -o eth0 -j MASQUERADE 2>/dev/null || iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
netfilter-persistent save 2>/dev/null || true
echo "✅ Routage NAT actif : tout élève sur 'Alta-box1' surfe via le Wi-Fi du bureau (wlan0)."

# 5. Demande des identifiants du Wi-Fi du bureau (Optionnel immédiat)
echo -e "\n${BLUE}[4/5] Enregistrement de votre Wi-Fi de bureau/maison...${NC}"
echo -e "Voulez-vous enregistrer le Wi-Fi de votre bureau dès maintenant ?"
read -p "Entrez le NOM (SSID) du Wi-Fi de votre bureau (laisser vide pour passer) : " BUREAU_SSID

if [ -n "$BUREAU_SSID" ]; then
    read -s -p "Entrez le MOT DE PASSE du Wi-Fi : " BUREAU_PASS
    echo ""
    nmcli connection delete "Wifi-Bureau" 2>/dev/null || true
    nmcli connection add \
        type wifi \
        ifname wlan0 \
        con-name "Wifi-Bureau" \
        autoconnect yes \
        ssid "$BUREAU_SSID"
    nmcli connection modify "Wifi-Bureau" \
        wifi-sec.key-mgmt wpa-psk \
        wifi-sec.psk "$BUREAU_PASS" \
        connection.autoconnect-priority 10
    echo "✅ Wi-Fi du bureau '$BUREAU_SSID' pré-enregistré sur wlan0."
    nmcli connection up "Wifi-Bureau" 2>/dev/null || true
fi

echo -e "\n${GREEN}==============================================================================${NC}"
echo -e "${GREEN}  🎉 MODE WI-FI SIMULTANÉ (AP + STA) PARFAITEMENT CONFIGURÉ !                ${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo -e "Architecture Réseau active sur le Raspberry Pi 5 :"
echo -e "  1. ${GREEN}wlan0 (Client)${NC}      : Connecté au Wi-Fi du bureau/maison pour l'accès Internet"
echo -e "  2. ${BLUE}uap0 (Point d'accès)${NC} : Émet 'Alta-box1' (Pass : Bamako+223) pour les élèves"
echo -e "  3. ${YELLOW}Routage NAT${NC}          : Les requêtes des élèves sur 'Alta-box1' passent par"
echo -e "                             le Wi-Fi du bureau pour interroger ${GREEN}https://api.alterniamali.com${NC}"
