#!/usr/bin/env python3
"""
══════════════════════════════════════════════════════════════════════════════
Contrôleur d'Indicateur Lumineux (LED) pour Raspberry Pi 5 (Alta-Box)
══════════════════════════════════════════════════════════════════════════════

Comportement lumineux officiel :
1. Démarrage / Recherche de connexion : Clignotement lent (1 Hz).
2. Connexion établie avec le serveur AWS (api.alterniamali.com) :
   Lumière stable / pulsation fixe confirmant la liaison Cloud active.
3. Interactions élèves (connexion au Wi-Fi, requêtes, questions posées, audio) :
   Clignotement ultra-rapide et ininterrompu ("sans cesse") pendant toute l'activité !

Supporte :
- La LED d'activité native du Raspberry Pi 5 (/sys/class/leds/ACT/ ou pwr_led)
- Une LED d'état externe optionnelle connectée sur GPIO (par défaut GPIO 17)
"""

import os
import sys
import time
import threading
from pathlib import Path

# Chemins système LED sur Raspberry Pi OS Bookworm
ACT_LED_PATH = Path("/sys/class/leds/ACT")
PWR_LED_PATH = Path("/sys/class/leds/PWR")

# Fichier drapeau indiquant une interaction élève en cours
ACTIVITY_FLAG = Path("/tmp/alta_activity.flag")
SERVER_STATUS_FLAG = Path("/tmp/alta_server_connected.flag")

# Broche GPIO optionnelle pour LED externe (si branchée)
EXTERNAL_LED_PIN = 17
gpio_available = False
gpio_led = None

try:
    import gpiod
    # Utilisation de libgpiod (standard officiel Pi 5 sous Bookworm)
    chip = gpiod.Chip('gpiochip4')
    gpio_led = chip.get_line(EXTERNAL_LED_PIN)
    gpio_led.request(consumer="alta-led", type=gpiod.LINE_REQ_DIR_OUT)
    gpio_available = True
except Exception:
    try:
        from gpiozero import LED
        gpio_led = LED(EXTERNAL_LED_PIN)
        gpio_available = True
    except Exception:
        gpio_available = False


class LedController:
    def __init__(self):
        self.state = "BOOTING"  # "BOOTING", "CONNECTED", "INTERACTING"
        self.running = True
        self.last_interaction_time = 0
        self._setup_system_led()

    def _setup_system_led(self):
        """Prend le contrôle manuel de la LED ACT du Pi."""
        if ACT_LED_PATH.exists():
            try:
                trigger_file = ACT_LED_PATH / "trigger"
                if trigger_file.exists():
                    os.system("echo none > /sys/class/leds/ACT/trigger 2>/dev/null || true")
            except Exception:
                pass

    def _set_led(self, state: bool):
        """Allume (True) ou éteint (False) la LED native et externe."""
        val = "1" if state else "0"
        
        # 1. LED native Pi 5
        brightness_file = ACT_LED_PATH / "brightness"
        if brightness_file.exists():
            try:
                brightness_file.write_text(val)
            except Exception:
                pass
        
        # 2. LED externe GPIO (si câblée)
        if gpio_available and gpio_led:
            try:
                if hasattr(gpio_led, 'set_value'):
                    gpio_led.set_value(1 if state else 0)
                elif hasattr(gpio_led, 'on') and hasattr(gpio_led, 'off'):
                    gpio_led.on() if state else gpio_led.off()
            except Exception:
                pass

    def check_flags(self):
        """Vérifie si une interaction ou une connexion serveur est active."""
        now = time.time()
        
        # Si le fichier d'activité a été touché dans les 2 dernières secondes
        if ACTIVITY_FLAG.exists():
            try:
                mtime = ACTIVITY_FLAG.stat().st_mtime
                if now - mtime < 2.5:
                    self.state = "INTERACTING"
                    return
            except Exception:
                pass

        # Si le serveur AWS répond
        if SERVER_STATUS_FLAG.exists():
            try:
                mtime = SERVER_STATUS_FLAG.stat().st_mtime
                if now - mtime < 45.0:  # Heartbeat toutes les 30s
                    self.state = "CONNECTED"
                    return
            except Exception:
                pass

        self.state = "BOOTING"

    def run(self):
        """Boucle principale du contrôleur LED."""
        print("💡 [Alta-LED] Contrôleur d'indicateur lumineux actif sur Raspberry Pi 5.")
        
        while self.running:
            self.check_flags()

            if self.state == "INTERACTING":
                # Clignotement ultra-rapide et ininterrompu (20 Hz)
                for _ in range(5):
                    self._set_led(True)
                    time.sleep(0.04)
                    self._set_led(False)
                    time.sleep(0.04)

            elif self.state == "CONNECTED":
                # Connexion AWS OK : LED allumée fixe avec un battement de coeur doux
                self._set_led(True)
                time.sleep(0.8)
                self._set_led(False)
                time.sleep(0.08)
                self._set_led(True)
                time.sleep(0.08)
                self._set_led(False)
                time.sleep(0.08)

            else:
                # Démarrage ou pas encore connecté : Clignotement lent régulier (1 Hz)
                self._set_led(True)
                time.sleep(0.5)
                self._set_led(False)
                time.sleep(0.5)

    def stop(self):
        self.running = False
        self._set_led(False)


if __name__ == "__main__":
    controller = LedController()
    try:
        controller.run()
    except KeyboardInterrupt:
        controller.stop()
        print("\nArrêt du contrôleur LED.")
