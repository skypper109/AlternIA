#!/bin/bash
# ==============================================================================
# Script de Configuration de la Cible Cloud pour Raspberry Pi 5 (Alta-Box)
# Permet de basculer la liaison du Raspberry Pi vers :
#   - Option 1 : Le Domaine Cloudflare Permanent (https://api.alterniamali.com)
#   - Option 2 : L'IP Directe du Serveur AWS GPU g4dn (http://<IP_AWS>:8000)
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${GREEN}   🇲🇱  CONFIGURATION DE LA CIBLE SERVEUR POUR ALTERNIA RASPBERRY PI  🇲🇱${NC}"
echo -e "${BLUE}==============================================================================${NC}"

TARGET_URL="$1"

if [ -z "$TARGET_URL" ]; then
    echo -e "Choisissez la destination serveur pour votre Raspberry Pi :\n"
    echo -e "  [1] \033[1;32mDomaine Officiel Cloudflare (Recommandé)\033[0m : https://api.alterniamali.com"
    echo -e "  [2] \033[1;36mIP Directe de votre Serveur AWS GPU (g4dn.2xlarge)\033[0m"
    echo -e "  [3] \033[1;33mSaisir une URL personnalisée\033[0m\n"
    read -p "Votre choix [1/2/3] (défaut: 1) : " CHOICE
    CHOICE=${CHOICE:-1}

    case "$CHOICE" in
        1)
            TARGET_URL="https://api.alterniamali.com"
            ;;
        2)
            read -p "Entrez l'IP publique de votre serveur AWS (ex: 100.54.122.220) : " AWS_IP
            TARGET_URL="http://${AWS_IP}:8000"
            ;;
        3)
            read -p "Entrez l'URL complète (ex: https://mon-tunnel.trycloudflare.com) : " CUSTOM_URL
            TARGET_URL="$CUSTOM_URL"
            ;;
        *)
            TARGET_URL="https://api.alterniamali.com"
            ;;
    esac
fi

# Nettoyer l'URL de tout slash de fin
TARGET_URL="${TARGET_URL%/}"

echo -e "\n🌐 \033[1;34mCible sélectionnée :\033[0m \033[1;32m$TARGET_URL\033[0m"

# 1. Vérification de la connectivité réseau vers la cible
echo -e "🔍 Test de connexion vers le serveur..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 6 "${TARGET_URL}/api/device/info" 2>/dev/null || curl -s -o /dev/null -w "%{http_code}" --connect-timeout 6 "${TARGET_URL}/docs" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "307" ] || [ "$HTTP_CODE" = "308" ]; then
    echo -e "✅ \033[1;32mConnexion établie avec succès ! (HTTP $HTTP_CODE)\033[0m"
else
    echo -e "⚠️ \033[1;33mAttention : Le serveur a répondu avec le code HTTP $HTTP_CODE (ou injoignable pour le moment). Configuration poursuivie...\033[0m"
fi

# 2. Mise à jour de la configuration d'environnement du Raspberry Pi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RPI_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$RPI_DIR/.env"

touch "$ENV_FILE"
if grep -q "ALTERNIA_API_URL=" "$ENV_FILE"; then
    sed -i "s|ALTERNIA_API_URL=.*|ALTERNIA_API_URL=$TARGET_URL|g" "$ENV_FILE"
else
    echo "ALTERNIA_API_URL=$TARGET_URL" >> "$ENV_FILE"
fi
echo "✅ Variable ALTERNIA_API_URL mise à jour dans $ENV_FILE"

# 3. Mise à jour de la configuration Nginx locale si présente
NGINX_CONF="/etc/nginx/sites-available/alta-box"
if [ -f "$NGINX_CONF" ]; then
    echo "⚙️ Mise à jour du proxy Nginx local (/etc/nginx/sites-available/alta-box)..."
    # Extraire l'hôte pour le header Host
    HOST_HEADER=$(echo "$TARGET_URL" | sed -E 's|https?://([^:/]+).*|\1|')
    
    sudo sed -i -E "s|proxy_pass https?://[^/]+/api/|proxy_pass $TARGET_URL/api/|g" "$NGINX_CONF"
    sudo sed -i -E "s|proxy_pass https?://[^/]+/ws/|proxy_pass $TARGET_URL/ws/|g" "$NGINX_CONF"
    sudo sed -i -E "s|proxy_pass https?://[^/]+/api/tts|proxy_pass $TARGET_URL/api/tts|g" "$NGINX_CONF"
    sudo sed -i -E "s|proxy_set_header Host [^;]+;|proxy_set_header Host $HOST_HEADER;|g" "$NGINX_CONF"

    # Vérification et rechargement de Nginx
    if sudo nginx -t > /dev/null 2>&1; then
        sudo systemctl reload nginx
        echo "✅ Nginx rechargé avec succès."
    fi
fi

# 4. Redémarrage de l'agent de télémétrie Raspberry Pi si actif
if systemctl is-active --quiet alta-agent.service 2>/dev/null; then
    sudo systemctl restart alta-agent.service 2>/dev/null || true
    echo "✅ Agent de télémétrie Raspberry Pi redémarré."
fi

echo -e "\n${GREEN}==============================================================================${NC}"
echo -e "${GREEN}  🎉 VOTRE RASPBERRY PI COMMUNIQUE DÉSORMAIS DIRECTEMENT AVEC :               ${NC}"
echo -e "${GREEN}  👉 $TARGET_URL                                                              ${NC}"
echo -e "${GREEN}==============================================================================${NC}"
