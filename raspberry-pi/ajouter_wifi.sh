#!/bin/bash
# ==============================================================================
# Script d'Ajout d'un Réseau Wi-Fi Externe (Bureau, Domicile, Partage 4G)
# pour Raspberry Pi 5 (NetworkManager)
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Veuillez exécuter ce script en root : sudo ./ajouter_wifi.sh${NC}"
    exit 1
fi

SSID="$1"
PASSWORD="$2"

if [ -z "$SSID" ]; then
    echo -e "${BLUE}==============================================================================${NC}"
    echo -e "${GREEN}   📶 ENREGISTREMENT D'UN RÉSEAU WI-FI POUR LE BOÎTIER ALTA-BOX             ${NC}"
    echo -e "${BLUE}==============================================================================${NC}"
    echo -e "Ce script enregistre les identifiants d'un Wi-Fi distant (ex: Wi-Fi du boulot)"
    echo -e "pour que le Raspberry Pi s'y connecte automatiquement dès qu'il est sur place.\n"
    read -p "👉 Entrez le NOM du Wi-Fi (SSID) : " SSID
fi

if [ -z "$PASSWORD" ]; then
    read -s -p "👉 Entrez le MOT DE PASSE du Wi-Fi : " PASSWORD
    echo ""
fi

CON_NAME="Wifi-${SSID}"

# Suppression d'un ancien profil du même nom s'il existait
nmcli connection delete "$CON_NAME" 2>/dev/null || true

echo -e "\n⏳ Enregistrement du profil Wi-Fi '${GREEN}${SSID}${NC}' dans NetworkManager..."

# Création du profil Wi-Fi Client dans NetworkManager
nmcli connection add \
    type wifi \
    ifname wlan0 \
    con-name "$CON_NAME" \
    autoconnect yes \
    ssid "$SSID"

nmcli connection modify "$CON_NAME" \
    wifi-sec.key-mgmt wpa-psk \
    wifi-sec.psk "$PASSWORD" \
    connection.autoconnect-priority 10

echo -e "\n${GREEN}==============================================================================${NC}"
echo -e "${GREEN}  ✅ RÉSEAU WI-FI ENREGISTRÉ AVEC SUCCÈS !                                  ${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo -e "Le profil ${BLUE}'${CON_NAME}'${NC} est sauvegardé sur le Raspberry Pi 5."
echo -e "\n💡 ${YELLOW}Comment ça va se passer demain au boulot ?${NC}"
echo -e "1. Dès que vous allumez le Pi 5 au boulot, il détecte le réseau '${GREEN}${SSID}${NC}' et s'y connecte tout seul."
echo -e "2. Pour forcer la connexion manuellement si besoin :"
echo -e "     ${BLUE}sudo nmcli connection up '${CON_NAME}'${NC}"
echo -e "3. Pour revenir au mode Point d'Accès 'Alta-box1' pour les élèves :"
echo -e "     ${BLUE}sudo nmcli connection up 'Alta-Hotspot'${NC}"
echo -e "\nPour voir tous les réseaux Wi-Fi enregistrés : ${YELLOW}nmcli connection show${NC}"
