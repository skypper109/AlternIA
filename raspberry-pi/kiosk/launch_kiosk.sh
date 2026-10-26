#!/bin/bash
# ==============================================================================
# Script de Lancement Kiosk Plein Écran (Sortie HDMI / Écran TV Raspberry Pi 5)
# Cible officielle : https://device.alterniamali.com
# Compatible : Écrans HDMI, TV 1080p/4K, Souris, Claviers USB et Touches Physiques
# ==============================================================================

set -u

# URL officielle de l'interface Kiosk élève et miroir local de secours
TARGET_URL="https://device.alterniamali.com"
LOCAL_FALLBACK="http://127.0.0.1/"

echo "📺 [AlternIA Kiosk] Démarrage de l'interface sur la sortie HDMI..."

# 1. Configuration automatique de l'environnement graphique (X11 & Wayland / Pi 5)
export DISPLAY="${DISPLAY:-:0}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"

# 2. Désactiver la mise en veille et l'économiseur d'écran HDMI sur la TV
xset s off 2>/dev/null || true
xset -dpms 2>/dev/null || true
xset s noblank 2>/dev/null || true

# 3. Gestion du curseur souris : masquage après 3s d'inactivité (réapparaît dès qu'on bouge la souris)
which unclutter >/dev/null 2>&1 && (killall unclutter 2>/dev/null || true; unclutter -idle 3 -root &)

# 4. Nettoyage des verrous et crash-flags Chromium pour éviter les boîtes de dialogue
CHROMIUM_DIR="$HOME/.config/chromium/Default"
mkdir -p "$CHROMIUM_DIR"
rm -f "$HOME/.config/chromium/SingletonLock" "$HOME/.config/chromium/SingletonCookie" "$HOME/.config/chromium/SingletonSocket" 2>/dev/null || true

CHROMIUM_PREF="$CHROMIUM_DIR/Preferences"
if [ -f "$CHROMIUM_PREF" ]; then
    sed -i 's/"exited_cleanly":false/"exited_cleanly":true/' "$CHROMIUM_PREF" 2>/dev/null || true
    sed -i 's/"exit_type":"Crashed"/"exit_type":"Normal"/' "$CHROMIUM_PREF" 2>/dev/null || true
fi

# 5. Détection de l'exécutable Chromium
CHROMIUM_BIN=""
if which chromium-browser >/dev/null 2>&1; then
    CHROMIUM_BIN="chromium-browser"
elif which chromium >/dev/null 2>&1; then
    CHROMIUM_BIN="chromium"
else
    echo "❌ [AlternIA Kiosk] Aucun navigateur Chromium trouvé sur le système."
    exit 1
fi

# 6. Boucle de maintien Kiosk (Relance automatique si déconnexion ou fermeture)
while true; do
    # Détermination de la cible (Cloud https://device.alterniamali.com ou miroir local)
    LAUNCH_URL="$LOCAL_FALLBACK"
    echo "🌐 [AlternIA Kiosk] Vérification de la liaison vers $TARGET_URL..."

    for i in {1..8}; do
        if curl -s --head --connect-timeout 2 "$TARGET_URL" >/dev/null 2>&1; then
            LAUNCH_URL="$TARGET_URL"
            echo "✅ [AlternIA Kiosk] Liaison Cloud active ! Chargement direct de $TARGET_URL."
            break
        fi
        sleep 1
    done

    if [ "$LAUNCH_URL" = "$LOCAL_FALLBACK" ]; then
        echo "⚠️ [AlternIA Kiosk] Mode local actif. Chargement du miroir local en attente de réseau."
    fi

    echo "🚀 [AlternIA Kiosk] Lancement de $CHROMIUM_BIN sur $LAUNCH_URL"

    "$CHROMIUM_BIN" \
        --kiosk \
        --noerrdialogs \
        --disable-infobars \
        --disable-session-crashed-bubble \
        --disable-features=Translate,TranslateUI \
        --disable-pinch \
        --ozone-platform-hint=auto \
        --password-store=basic \
        --overscroll-history-navigation=0 \
        --autoplay-policy=no-user-gesture-required \
        --check-for-update-interval=31536000 \
        --touch-events=enabled \
        --start-maximized \
        --window-size=1920,1080 \
        --window-position=0,0 \
        "$LAUNCH_URL"

    echo "⚠️ [AlternIA Kiosk] Chromium s'est arrêté. Redémarrage dans 2 secondes..."
    sleep 2
done
