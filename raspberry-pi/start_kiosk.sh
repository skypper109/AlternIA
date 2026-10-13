#!/bin/bash
# ==============================================================================
# Script de lancement du Mode Kiosk Plein Écran pour AlternIA Box (Raspberry Pi 3)
# Conçu pour écran tactile officiel Raspberry Pi 7" ou tout écran HDMI.
# ==============================================================================

# URL de l'interface Kiosk AlternIA (peut être locale ou distante)
KIOSK_URL=${ALTERNIA_KIOSK_URL:-"http://localhost:8000/device"}

echo "🚀 Démarrage du Kiosk AlternIA sur Raspberry Pi 3..."
echo "🌐 URL cible : $KIOSK_URL"

# 1. Empêcher la mise en veille et l'économiseur d'écran
xset s noblank
xset s off
xset -dpms

# 2. Masquer le curseur de souris après 0.5s d'inactivité (si unclutter est installé)
if which unclutter > /dev/null 2>&1; then
    unclutter -idle 0.5 -root &
fi

# 3. Supprimer les drapeaux de plantage résiduels de Chromium
sed -i 's/"exited_cleanly":false/"exited_cleanly":true/' ~/.config/chromium/Default/Preferences 2>/dev/null || true
sed -i 's/"exit_type":"Crashed"/"exit_type":"Normal"/' ~/.config/chromium/Default/Preferences 2>/dev/null || true

# 4. Lancer Chromium en mode Kiosk plein écran avec accélération matérielle
chromium-browser \
    --noerrdialogs \
    --disable-infobars \
    --kiosk \
    --check-for-update-interval=31536000 \
    --disable-pinch \
    --overscroll-history-navigation=0 \
    --autoplay-policy=no-user-gesture-required \
    --enable-features=OverlayScrollbar \
    "$KIOSK_URL"
