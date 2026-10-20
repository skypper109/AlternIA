#!/bin/bash
# ==============================================================================
# Script de Lancement Kiosk Plein Écran (Sortie HDMI / Écran TV Raspberry Pi 5)
# Cible officielle : https://device.alterniamali.com
# ==============================================================================

set -u

# URL officielle de l'interface Kiosk élève et miroir local de secours
TARGET_URL="https://device.alterniamali.com"
LOCAL_FALLBACK="http://127.0.0.1/"

echo "📺 [AlternIA Kiosk] Démarrage de l'interface sur la sortie HDMI..."

# 1. Configuration des variables d'environnement graphique X11 / Wayland
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"

# 2. Désactiver la mise en veille de l'écran HDMI et l'économiseur
xset s off 2>/dev/null || true
xset -dpms 2>/dev/null || true
xset s noblank 2>/dev/null || true

# 3. Masquer le curseur de la souris après inactivité (unclutter)
which unclutter >/dev/null 2>&1 && unclutter -idle 2 -root &

# 4. Suppression des bannières de plantage de Chromium
CHROMIUM_PREF="$HOME/.config/chromium/Default/Preferences"
if [ -f "$CHROMIUM_PREF" ]; then
    sed -i 's/"exited_cleanly":false/"exited_cleanly":true/' "$CHROMIUM_PREF" 2>/dev/null || true
    sed -i 's/"exit_type":"Crashed"/"exit_type":"Normal"/' "$CHROMIUM_PREF" 2>/dev/null || true
fi

# 5. Détermination de la cible (Cloud https://device.alterniamali.com ou miroir local)
LAUNCH_URL="$LOCAL_FALLBACK"
echo "🌐 [AlternIA Kiosk] Vérification de la liaison vers $TARGET_URL..."

for i in {1..12}; do
    if curl -s --head --connect-timeout 2 "$TARGET_URL" >/dev/null 2>&1; then
        LAUNCH_URL="$TARGET_URL"
        echo "✅ [AlternIA Kiosk] Liaison Cloud active ! Chargement direct de $TARGET_URL."
        break
    fi
    sleep 1
done

if [ "$LAUNCH_URL" = "$LOCAL_FALLBACK" ]; then
    echo "⚠️ [AlternIA Kiosk] Cloud injoignable immédiatement. Utilisation du miroir local en attente de réseau."
    until curl -s --connect-timeout 1 "$LOCAL_FALLBACK" >/dev/null 2>&1; do
        sleep 1
    done
fi

# 6. Détection de l'exécutable Chromium
CHROMIUM_BIN=""
if which chromium-browser >/dev/null 2>&1; then
    CHROMIUM_BIN="chromium-browser"
elif which chromium >/dev/null 2>&1; then
    CHROMIUM_BIN="chromium"
else
    echo "❌ [AlternIA Kiosk] Aucun navigateur Chromium trouvé sur le système."
    exit 1
fi

# 7. Lancement de Chromium en mode Kiosk plein écran avec lecture audio automatique
echo "🚀 [AlternIA Kiosk] Lancement de $CHROMIUM_BIN sur $LAUNCH_URL"
exec "$CHROMIUM_BIN" \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-features=TranslateUI \
    --disable-pinch \
    --overscroll-history-navigation=0 \
    --autoplay-policy=no-user-gesture-required \
    --check-for-update-interval=31536000 \
    --touch-events=enabled \
    --window-size=1920,1080 \
    --window-position=0,0 \
    "$LAUNCH_URL"
