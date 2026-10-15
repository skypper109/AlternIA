#!/bin/bash
# ==============================================================================
# Script de Lancement Kiosk Plein Écran (Écran Tactile / HDMI Raspberry Pi 5)
# ==============================================================================

# Attendre que le serveur Nginx local soit opérationnel
until curl -s http://127.0.0.1 > /dev/null; do
    sleep 1
done

# Désactiver la mise en veille de l'écran
xset s off 2>/dev/null || true
xset -dpms 2>/dev/null || true
xset s noblank 2>/dev/null || true

# Masquer le curseur de souris si inactif (unclutter)
which unclutter > /dev/null && unclutter -idle 2 -root &

# Résolution et suppression des alertes de crash Chromium
sed -i 's/"exited_cleanly":false/"exited_cleanly":true/' ~/.config/chromium/Default/Preferences 2>/dev/null || true
sed -i 's/"exit_type":"Crashed"/"exit_type":"Normal"/' ~/.config/chromium/Default/Preferences 2>/dev/null || true

# Lancement de Chromium en mode Kiosk ultra-fluide
exec chromium-browser \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-features=TranslateUI \
    --disable-pinch \
    --overscroll-history-navigation=0 \
    --autoplay-policy=no-user-gesture-required \
    --check-for-update-interval=31536000 \
    http://127.0.0.1/
