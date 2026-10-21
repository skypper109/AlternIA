#!/usr/bin/env python3
"""
══════════════════════════════════════════════════════════════════════════════
Contrôleur Matériel AlternIA Box (Raspberry Pi 5)
══════════════════════════════════════════════════════════════════════════════

Ce module gère l'ensemble des entrées/sorties physiques du boîtier AlternIA :
1. Boutons Poussoirs Dédiés (4 boutons GPIO avec résistances Pull-Up internes) :
   • BOUTON 1 (GPIO 5)  : Niveau 1 — Fondamental (6ème -> 7ème -> 8ème -> 9ème / DEF)
   • BOUTON 2 (GPIO 6)  : Niveau 2 — Secondaire (10ème <-> 11ème)
   • BOUTON 3 (GPIO 13) : Niveau 3 — Terminale (12ème Année / Baccalauréat)
   • BOUTON 4 (GPIO 26) : Micro Toggle (1er clic = Démarrer enregistrement, 2ème clic = Couper & Envoyer)

2. LED Tricolore Intégrée (RGB sur GPIO 17=Rouge, 27=Vert, 22=Bleu) :
   • Niveau 1 (Fondamental)   : Turquoise / Vert Émeraude doux
   • Niveau 2 (Secondaire)    : Bleu Royal
   • Niveau 3 (Terminale)     : Ambre / Orange Doré
   • Enregistrement Micro     : Rouge Vif Clignotant / Pulsant (1er clic)
   • Réflexion / Envoi IA     : Violet Pulsant (2ème clic, traitement en cours)
   • Parole du dispositif     : Cyan / Bleu ciel Scintillant (TTS haut-parleur actif)
   • Retour en veille         : Restauration automatique de la couleur du niveau actif

3. Microphone (USB ou Jack) : Enregistrement vocal élève 16kHz via arecord ALSA
4. Haut-Parleur (I2S MAX98357A, USB ou Jack) : Lecture audio des réponses vocales IA

Broches I2S réservées pour l'amplificateur MAX98357A : GPIO 18 (BCLK), 19 (LRCLK), 21 (DIN).
"""

import os
import sys
import time
import math
import uuid
import subprocess
import threading
import urllib.request
import urllib.parse
import json
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION MATÉRIELLE & BROCHES GPIO (BCM)
# ══════════════════════════════════════════════════════════════════════════════

# 4 Boutons Poussoirs (Broches reliées à GND, pull-up interne du Pi 5 activée)
PIN_BTN_NIV1 = int(os.environ.get("PIN_BTN_NIV1", 5))   # Pin physique 29
PIN_BTN_NIV2 = int(os.environ.get("PIN_BTN_NIV2", 6))   # Pin physique 31
PIN_BTN_NIV3 = int(os.environ.get("PIN_BTN_NIV3", 13))  # Pin physique 33
PIN_BTN_MIC  = int(os.environ.get("PIN_BTN_MIC", 26))   # Pin physique 37

# LED Tricolore RGB (Broches contiguës sur le connecteur 40 broches)
PIN_LED_R = int(os.environ.get("PIN_LED_R", 17))       # Pin physique 11 (Canal Rouge)
PIN_LED_G = int(os.environ.get("PIN_LED_G", 27))       # Pin physique 13 (Canal Vert)
PIN_LED_B = int(os.environ.get("PIN_LED_B", 22))       # Pin physique 15 (Canal Bleu)

# Type de LED : True = Cathode Commune (GND), False = Anode Commune (+3.3V)
LED_ACTIVE_HIGH = os.environ.get("LED_ACTIVE_HIGH", "1").lower() in ("1", "true", "yes")

# Chemins de fichiers d'échange & drapeaux
ACTIVITY_FLAG = Path("/tmp/alta_activity.flag")
LED_STATE_FILE = Path("/tmp/alta_led_state.json")
CURRENT_CLASS_FILE = Path("/tmp/alta_current_class")
AUDIO_RECORDING_PATH = Path("/tmp/alta_voice_input.wav")
AUDIO_OUTPUT_PATH = Path("/tmp/alta_voice_output.mp3")

# Serveurs cibles
LOCAL_API_URL = os.environ.get("ALTERNIA_LOCAL_API", "http://127.0.0.1:8000")
REMOTE_API_URL = os.environ.get("ALTERNIA_API_URL", "https://api.alterniamali.com")

# ══════════════════════════════════════════════════════════════════════════════
# STRUCTURE DES NIVEAUX ET PALETTE DE COULEURS RGB (0.0 -> 1.0)
# ══════════════════════════════════════════════════════════════════════════════

CYCLES_CONFIG = {
    "niveau_1": {
        "title": "Niveau 1 — Fondamental (DEF)",
        "classes": ["6eme", "7eme", "8eme", "9eme"],
        "default": "9eme",
        "color": (0.0, 1.0, 0.55),  # Turquoise / Vert Émeraude
        "ansi": "\033[38;2;0;255;140m",
    },
    "niveau_2": {
        "title": "Niveau 2 — Secondaire (Lycée)",
        "classes": ["10eme", "11eme"],
        "default": "10eme",
        "color": (0.1, 0.35, 1.0),  # Bleu Royal
        "ansi": "\033[38;2;25;90;255m",
    },
    "niveau_3": {
        "title": "Niveau 3 — Terminale (BAC)",
        "classes": ["12eme"],
        "default": "12eme",
        "color": (1.0, 0.45, 0.0),  # Ambre / Orange Doré
        "ansi": "\033[38;2;255;115;0m",
    },
}

# Couleurs d'états spéciaux
COLOR_RECORDING = (1.0, 0.0, 0.0)      # Rouge vif (Enregistrement micro en cours)
COLOR_THINKING  = (0.75, 0.0, 1.0)     # Violet / Magenta (Envoi / Réflexion IA)
COLOR_SPEAKING  = (0.15, 0.85, 1.0)    # Cyan / Bleu ciel (Le haut-parleur parle)
COLOR_OFF       = (0.0, 0.0, 0.0)      # Éteint


def notify_activity():
    """Déclenche l'indicateur d'activité système pour synchroniser les démons."""
    try:
        ACTIVITY_FLAG.touch(exist_ok=True)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# CONTRÔLEUR DE LED TRICOLORE (RGB)
# ══════════════════════════════════════════════════════════════════════════════

class TricolorLedController:
    """
    Pilote une LED RGB matérielle (via gpiozero RGBLED ou GPIO direct) avec animations :
    - CLASS_IDLE : Respiration douce ou couleur fixe de la classe active
    - RECORDING  : Rouge vif pulsant rapide (Micro actif)
    - THINKING   : Violet pulsant (Calcul IA)
    - SPEAKING   : Cyan scintillant / modulé au rythme de la voix (Haut-parleur parle)
    """

    MODE_CLASS_IDLE = "CLASS_IDLE"
    MODE_RECORDING  = "RECORDING"
    MODE_THINKING   = "THINKING"
    MODE_SPEAKING   = "SPEAKING"
    MODE_OFF        = "OFF"

    def __init__(self, pin_r: int = PIN_LED_R, pin_g: int = PIN_LED_G, pin_b: int = PIN_LED_B, active_high: bool = LED_ACTIVE_HIGH):
        self.pin_r = pin_r
        self.pin_g = pin_g
        self.pin_b = pin_b
        self.active_high = active_high

        self.current_mode = self.MODE_CLASS_IDLE
        self.class_color: Tuple[float, float, float] = CYCLES_CONFIG["niveau_2"]["color"]
        self.current_rgb: Tuple[float, float, float] = self.class_color
        self.class_name: str = "10eme"
        
        self.running = True
        self.hardware_type = "SIMULATION"
        self.rgb_device = None
        self.gpio_fallback_pins = None
        self._last_log_state = ""

        self._setup_hardware()

        # Démarrage du thread d'animation fluide
        self.anim_thread = threading.Thread(target=self._animation_loop, daemon=True)
        self.anim_thread.start()

    def _setup_hardware(self):
        """Initialise le composant RGB avec gpiozero ou libgpiod, ou active le mode simulation."""
        try:
            from gpiozero import RGBLED  # type: ignore
            self.rgb_device = RGBLED(
                red=self.pin_r,
                green=self.pin_g,
                blue=self.pin_b,
                active_high=self.active_high,
                pwm=True
            )
            self.hardware_type = "GPIOZERO_PWM"
            print(f"💡 [LED RGB] Module PWM actif sur GPIO {self.pin_r}(R), {self.pin_g}(G), {self.pin_b}(B).")
            return
        except Exception as exc:
            pass

        # Fallback 1 : gpiozero sans PWM (LED classiques Tout-Ou-Rien)
        try:
            from gpiozero import LED  # type: ignore
            self.gpio_fallback_pins = {
                "r": LED(self.pin_r, active_high=self.active_high),
                "g": LED(self.pin_g, active_high=self.active_high),
                "b": LED(self.pin_b, active_high=self.active_high),
            }
            self.hardware_type = "GPIOZERO_BINARY"
            print(f"💡 [LED RGB] Mode digital actif (sans PWM) sur GPIO {self.pin_r}, {self.pin_g}, {self.pin_b}.")
            return
        except Exception:
            pass

        # Fallback 2 : Mode Simulation (pour dev sur PC / Mac sans GPIO)
        self.hardware_type = "SIMULATION"
        print(f"💡 [LED RGB] Mode simulation actif (LED visuelle console).")

    def _apply_raw_rgb(self, r: float, g: float, b: float):
        """Applique les intensités [0.0 - 1.0] sur les broches matérielles."""
        r = max(0.0, min(1.0, float(r)))
        g = max(0.0, min(1.0, float(g)))
        b = max(0.0, min(1.0, float(b)))
        self.current_rgb = (r, g, b)

        if self.rgb_device and hasattr(self.rgb_device, "color"):
            try:
                self.rgb_device.color = (r, g, b)
            except Exception:
                pass
        elif self.gpio_fallback_pins:
            try:
                if r > 0.2: self.gpio_fallback_pins["r"].on()
                else: self.gpio_fallback_pins["r"].off()

                if g > 0.2: self.gpio_fallback_pins["g"].on()
                else: self.gpio_fallback_pins["g"].off()

                if b > 0.2: self.gpio_fallback_pins["b"].on()
                else: self.gpio_fallback_pins["b"].off()
            except Exception:
                pass

        # Sauvegarde d'état système pour supervision
        try:
            LED_STATE_FILE.write_text(json.dumps({
                "mode": self.current_mode,
                "class": self.class_name,
                "rgb": [round(r, 2), round(g, 2), round(b, 2)],
                "timestamp": time.time()
            }))
        except Exception:
            pass

    def _animation_loop(self):
        """Boucle d'animation à haute fluidité (25 Hz) sans bloquer les boutons."""
        t = 0.0
        while self.running:
            mode = self.current_mode

            if mode == self.MODE_RECORDING:
                # 🎙️ Enregistrement : Rouge pulsant vif (fréquence ~2.5 Hz)
                pulse = (math.sin(t * 15.0) + 1.0) / 2.0  # entre 0.0 et 1.0
                brightness = 0.25 + 0.75 * pulse
                self._apply_raw_rgb(COLOR_RECORDING[0] * brightness, 0.0, 0.0)

            elif mode == self.MODE_THINKING:
                # 🧠 Réflexion IA : Violet respirant doucement (fréquence ~1.5 Hz)
                pulse = (math.sin(t * 6.0) + 1.0) / 2.0
                brightness = 0.2 + 0.8 * pulse
                self._apply_raw_rgb(
                    COLOR_THINKING[0] * brightness,
                    COLOR_THINKING[1] * brightness,
                    COLOR_THINKING[2] * brightness
                )

            elif mode == self.MODE_SPEAKING:
                # 🔊 Parole du dispositif : Cyan scintillant dynamique (rythme vocal)
                wave1 = math.sin(t * 18.0)
                wave2 = math.cos(t * 31.0)
                mod = max(0.3, min(1.0, 0.65 + 0.25 * wave1 + 0.1 * wave2))
                self._apply_raw_rgb(
                    COLOR_SPEAKING[0] * mod,
                    COLOR_SPEAKING[1] * mod,
                    COLOR_SPEAKING[2] * mod
                )

            elif mode == self.MODE_CLASS_IDLE:
                # 📚 Veille active : Respiration douce et apaisante autour de la couleur de classe
                breath = 0.85 + 0.15 * math.sin(t * 2.0)
                cr, cg, cb = self.class_color
                self._apply_raw_rgb(cr * breath, cg * breath, cb * breath)

            elif mode == self.MODE_OFF:
                self._apply_raw_rgb(0.0, 0.0, 0.0)

            t += 0.04
            time.sleep(0.04)

    def set_class_color(self, color_tuple: Tuple[float, float, float], class_name: str = ""):
        """Définit la couleur du niveau actif et repasse la LED en veille active."""
        self.class_color = color_tuple
        if class_name:
            self.class_name = class_name
        self.current_mode = self.MODE_CLASS_IDLE
        self._log_state_change(f"Classe active ({self.class_name})", color_tuple)

    def set_recording(self):
        """Active l'état lumineux d'enregistrement micro (Rouge pulsant)."""
        self.current_mode = self.MODE_RECORDING
        self._log_state_change("Enregistrement Micro", COLOR_RECORDING, symbol="🔴")

    def set_thinking(self):
        """Active l'état lumineux de calcul / requête IA (Violet pulsant)."""
        self.current_mode = self.MODE_THINKING
        self._log_state_change("Traitement & Réflexion IA", COLOR_THINKING, symbol="🟣")

    def set_speaking(self):
        """Active l'état lumineux lorsque le dispositif s'exprime (Cyan scintillant)."""
        self.current_mode = self.MODE_SPEAKING
        self._log_state_change("Dispositif en train de parler", COLOR_SPEAKING, symbol="🌊")

    def restore_idle(self):
        """Restaure automatiquement la couleur du niveau / classe active."""
        self.current_mode = self.MODE_CLASS_IDLE
        self._log_state_change(f"Retour veille classe ({self.class_name})", self.class_color)

    def set_off(self):
        """Éteint la LED."""
        self.current_mode = self.MODE_OFF
        self._apply_raw_rgb(0.0, 0.0, 0.0)

    def _log_state_change(self, label: str, color: Tuple[float, float, float], symbol: str = "💡"):
        """Affiche un log stylé en direct dans le terminal sans le saturer."""
        if self._last_log_state == label:
            return
        self._last_log_state = label
        r, g, b = [int(c * 255) for c in color]
        ansi_color = f"\033[38;2;{r};{g};{b}m"
        print(f"{ansi_color}{symbol} [LED Tricolore] État -> {label} (RGB: {r}, {g}, {b})\033[0m")

    def stop(self):
        self.running = False
        self.set_off()


# ══════════════════════════════════════════════════════════════════════════════
# GESTIONNAIRE MATÉRIEL (4 BOUTONS + MICRO TOGGLE + HAUT-PARLEUR)
# ══════════════════════════════════════════════════════════════════════════════

class HardwareController:
    """
    Contrôleur matériel centralisé :
    - Bouton 1 : Niveau 1 (Fondamental : 6e, 7e, 8e, 9e / DEF)
    - Bouton 2 : Niveau 2 (Secondaire : 10e, 11e)
    - Bouton 3 : Niveau 3 (Terminale / Baccalauréat)
    - Bouton 4 : Micro TOGGLE (1er clic = Record, 2ème clic = Stop & Envoyer)
    """

    def __init__(self):
        self.current_cycle_id = "niveau_2"
        self.current_class = "10eme"
        self.cycle_indices = {
            "niveau_1": 3,  # Par défaut 9ème (classe du DEF)
            "niveau_2": 0,  # Par défaut 10ème
            "niveau_3": 0,  # 12ème
        }

        # État d'enregistrement bistable (Toggle)
        self.is_recording = False
        self.record_process: Optional[subprocess.Popen] = None
        self.recording_start_time = 0.0

        # Contrôleur LED
        self.led = TricolorLedController(
            pin_r=PIN_LED_R,
            pin_g=PIN_LED_G,
            pin_b=PIN_LED_B,
            active_high=LED_ACTIVE_HIGH
        )

        # Initialiser avec la couleur de la classe par défaut
        self._apply_class_selection(self.current_cycle_id, self.current_class, announce=False)

        # Initialisation des Boutons
        self.buttons_ready = False
        self.setup_buttons()

    def setup_buttons(self):
        """Configure les 4 boutons poussoirs matériels via gpiozero."""
        try:
            from gpiozero import Button  # type: ignore

            self.btn_niv1 = Button(PIN_BTN_NIV1, pull_up=True, bounce_time=0.08)
            self.btn_niv2 = Button(PIN_BTN_NIV2, pull_up=True, bounce_time=0.08)
            self.btn_niv3 = Button(PIN_BTN_NIV3, pull_up=True, bounce_time=0.08)
            self.btn_mic  = Button(PIN_BTN_MIC,  pull_up=True, bounce_time=0.08)

            # Assignation des callbacks
            self.btn_niv1.when_pressed = self.on_press_niveau_1
            self.btn_niv2.when_pressed = self.on_press_niveau_2
            self.btn_niv3.when_pressed = self.on_press_niveau_3
            self.btn_mic.when_pressed  = self.on_press_mic_toggle

            self.buttons_ready = True
            print("=" * 76)
            print("✅ [Hardware] 4 Boutons GPIO initialisés avec succès :")
            print(f"   • Bouton 1 (GPIO {PIN_BTN_NIV1}) : Niveau 1 (Fondamental : 6e, 7e, 8e, 9e / DEF)")
            print(f"   • Bouton 2 (GPIO {PIN_BTN_NIV2}) : Niveau 2 (Secondaire : 10e, 11e)")
            print(f"   • Bouton 3 (GPIO {PIN_BTN_NIV3}) : Niveau 3 (Terminale / Baccalauréat)")
            print(f"   • Bouton 4 (GPIO {PIN_BTN_MIC}) : Micro TOGGLE (1er clic = Record, 2e = Envoi)")
            print("=" * 76)
        except Exception as exc:
            print(f"ℹ️ [Hardware] Mode simulation actif pour les boutons ({exc}).")

    # ──────────────────────────────────────────────────────────────────────────
    # GESTION DES 3 BOUTONS DE NIVEAUX / CLASSES
    # ──────────────────────────────────────────────────────────────────────────

    def on_press_niveau_1(self):
        """Bouton 1 : Cycle parmi les classes du Niveau 1 (Fondamental : 6e -> 7e -> 8e -> 9e)."""
        notify_activity()
        cfg = CYCLES_CONFIG["niveau_1"]
        classes = cfg["classes"]

        if self.current_cycle_id != "niveau_1":
            # Premier appui sur ce niveau : activer la classe mémorisée ou par défaut
            self.current_cycle_id = "niveau_1"
            idx = self.cycle_indices["niveau_1"]
            chosen = classes[idx]
        else:
            # Ré-appui : passer à la classe suivante
            idx = (self.cycle_indices["niveau_1"] + 1) % len(classes)
            self.cycle_indices["niveau_1"] = idx
            chosen = classes[idx]

        print(f"\n{cfg['ansi']}📚 [Bouton 1] Niveau 1 sélectionné -> Classe : {chosen.upper()} (Fondamental / DEF)\033[0m")
        self._apply_class_selection("niveau_1", chosen)

    def on_press_niveau_2(self):
        """Bouton 2 : Bascule entre 10ème et 11ème (Secondaire / Lycée)."""
        notify_activity()
        cfg = CYCLES_CONFIG["niveau_2"]
        classes = cfg["classes"]

        if self.current_cycle_id != "niveau_2":
            self.current_cycle_id = "niveau_2"
            idx = self.cycle_indices["niveau_2"]
            chosen = classes[idx]
        else:
            idx = (self.cycle_indices["niveau_2"] + 1) % len(classes)
            self.cycle_indices["niveau_2"] = idx
            chosen = classes[idx]

        print(f"\n{cfg['ansi']}📚 [Bouton 2] Niveau 2 sélectionné -> Classe : {chosen.upper()} (Secondaire)\033[0m")
        self._apply_class_selection("niveau_2", chosen)

    def on_press_niveau_3(self):
        """Bouton 3 : Active la Terminale (Baccalauréat)."""
        notify_activity()
        cfg = CYCLES_CONFIG["niveau_3"]
        chosen = "12eme"
        self.current_cycle_id = "niveau_3"
        self.cycle_indices["niveau_3"] = 0

        print(f"\n{cfg['ansi']}📚 [Bouton 3] Niveau 3 sélectionné -> Classe : TERMINALE (12ème / BAC)\033[0m")
        self._apply_class_selection("niveau_3", chosen)

    def _apply_class_selection(self, cycle_id: str, class_name: str, announce: bool = True):
        """Applique le choix de classe : couleur LED, fichier d'état et sync backend."""
        self.current_cycle_id = cycle_id
        self.current_class = class_name
        cfg = CYCLES_CONFIG[cycle_id]

        # 1. Mise à jour de la LED Tricolore
        self.led.set_class_color(cfg["color"], class_name=class_name)

        # 2. Sauvegarde locale du choix
        try:
            CURRENT_CLASS_FILE.write_text(class_name)
        except Exception:
            pass

        # 3. Synchronisation asynchrone avec le backend (Kiosk & WebSockets)
        threading.Thread(target=self._notify_backend_class, args=(class_name,), daemon=True).start()

    def _notify_backend_class(self, class_name: str):
        """Notifie le backend local et l'interface Kiosk en tâche de fond."""
        try:
            url = f"{LOCAL_API_URL.rstrip('/')}/api/esp32/select-class?classe={urllib.parse.quote(class_name)}&mic_connected=true"
            req = urllib.request.Request(url, method="POST")
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                pass
        except Exception:
            pass

    # ──────────────────────────────────────────────────────────────────────────
    # GESTION DU BOUTON MICRO (MODE TOGGLE BISTABLE)
    # ──────────────────────────────────────────────────────────────────────────

    def on_press_mic_toggle(self):
        """
        Bouton 4 : Micro Bistable (Toggle)
        • 1er Clic : Démarre l'enregistrement audio (LED passe en ROUGE vif pulsant)
        • 2ème Clic : Coupe l'enregistrement et déclenche l'envoi au tuteur IA
        """
        notify_activity()

        if not self.is_recording:
            # ── 1er CLIC : DÉBUT D'ENREGISTREMENT ──
            self.start_recording()
        else:
            # ── 2ème CLIC : FIN ET ENVOI ──
            self.stop_recording_and_process()

    def start_recording(self):
        """Démarre la capture audio ALSA et active la LED rouge."""
        self.is_recording = True
        self.recording_start_time = time.time()

        # Supprimer le fichier précédent
        try:
            if AUDIO_RECORDING_PATH.exists():
                AUDIO_RECORDING_PATH.unlink()
        except Exception:
            pass

        # LED Tricolore -> Rouge Vif Pulsant
        self.led.set_recording()

        print("\n" + "═" * 70)
        print("🎙️ [Micro - Clic 1] ENREGISTREMENT DÉMARRÉ ! Parlez maintenant...")
        print("   👉 Cliquez à nouveau sur le bouton Micro pour couper et envoyer.")
        print("═" * 70)

        try:
            # ALSA 16kHz Mono 16-bit (compatible Faster-Whisper et Qwen)
            self.record_process = subprocess.Popen([
                "arecord",
                "-D", "default",
                "-f", "S16_LE",
                "-r", "16000",
                "-c", "1",
                str(AUDIO_RECORDING_PATH)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as exc:
            print(f"⚠️ Erreur démarrage arecord : {exc} (Micro USB ou Jack branché ?)")

    def stop_recording_and_process(self):
        """Coupe l'enregistrement audio et démarre le traitement IA."""
        self.is_recording = False
        duration = time.time() - self.recording_start_time

        print("\n" + "═" * 70)
        print(f"🛑 [Micro - Clic 2] ENREGISTREMENT COUPÉ (Durée : {duration:.1f}s).")
        print("   🚀 Transmission et génération de la réponse IA en cours...")
        print("═" * 70)

        # Arrêt du processus arecord
        if self.record_process:
            try:
                self.record_process.terminate()
                self.record_process.wait(timeout=1.0)
            except Exception:
                try:
                    self.record_process.kill()
                except Exception:
                    pass
            self.record_process = None

        # Passer immédiatement la LED en mode Réflexion IA (Violet pulsant)
        self.led.set_thinking()

        # Traitement complet en tâche de fond pour garder les boutons réactifs
        threading.Thread(target=self._process_and_respond, daemon=True).start()

    # ──────────────────────────────────────────────────────────────────────────
    # TRAITEMENT VOCAL COMPLET (STT -> QUESTION IA -> TTS -> HAUT-PARLEUR)
    # ──────────────────────────────────────────────────────────────────────────

    def _process_and_respond(self):
        """Exécute la chaîne complète vocale de bout en bout."""
        time.sleep(0.1)  # Laisser le temps à ALSA de finaliser le fichier WAV

        if not AUDIO_RECORDING_PATH.exists():
            print("⚠️ Aucun fichier audio enregistré trouvé.")
            self.led.restore_idle()
            return

        file_size = AUDIO_RECORDING_PATH.stat().st_size
        if file_size < 1200:
            print(f"⚠️ Enregistrement trop court ({file_size} octets). Parlez un peu plus longtemps.")
            self.led.restore_idle()
            return

        notify_activity()

        try:
            # 1. Étape Transcription (STT)
            transcription = self._transcribe_audio(AUDIO_RECORDING_PATH)
            if not transcription or not transcription.strip():
                print("ℹ️ Aucune parole intelligible détectée.")
                self.led.restore_idle()
                return

            print(f"📝 [Transcription Écolier] « {transcription} »")

            # 2. Étape Consultation Tuteur IA (/api/ask)
            ai_answer = self._ask_tutor(transcription, self.current_class)
            if not ai_answer or not ai_answer.strip():
                print("⚠️ Réponse du tuteur vide.")
                self.led.restore_idle()
                return

            print(f"💡 [Réponse Tuteur IA] « {ai_answer[:120]}... »")

            # 3. Étape Synthèse Vocale (TTS)
            tts_success = self._synthesize_speech(ai_answer, AUDIO_OUTPUT_PATH)
            if tts_success and AUDIO_OUTPUT_PATH.exists():
                # 4. Étape Lecture Haut-Parleur avec interaction LED
                self.play_sound(AUDIO_OUTPUT_PATH)
            else:
                self.led.restore_idle()

        except Exception as exc:
            print(f"⚠️ Erreur lors du cycle de traitement vocal : {exc}")
            self.led.restore_idle()

    def _transcribe_audio(self, wav_path: Path) -> str:
        """Transcrit le fichier audio via l'endpoint /api/stt local ou cloud."""
        content = wav_path.read_bytes()
        boundary = f"----AltaBoundary{uuid.uuid4().hex}"
        body = bytearray()
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(b'Content-Disposition: form-data; name="audio"; filename="recording.wav"\r\n')
        body.extend(b"Content-Type: audio/wav\r\n\r\n")
        body.extend(content)
        body.extend(b"\r\n")
        body.extend(f"--{boundary}--\r\n".encode("utf-8"))

        urls_to_try = [
            f"{LOCAL_API_URL.rstrip('/')}/api/stt",
            f"{REMOTE_API_URL.rstrip('/')}/api/stt"
        ]

        for url in urls_to_try:
            try:
                req = urllib.request.Request(url, data=body, method="POST")
                req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
                with urllib.request.urlopen(req, timeout=12) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    text = data.get("text", "")
                    if text:
                        return text.strip()
            except Exception:
                continue
        return ""

    def _ask_tutor(self, question: str, student_class: str) -> str:
        """Interroge le moteur pédagogique local ou AWS."""
        payload = json.dumps({
            "question": question,
            "student_class": student_class,
            "session_id": "box_voice_session"
        }).encode("utf-8")

        urls_to_try = [
            f"{LOCAL_API_URL.rstrip('/')}/api/ask",
            f"{REMOTE_API_URL.rstrip('/')}/api/ask"
        ]

        for url in urls_to_try:
            try:
                req = urllib.request.Request(url, data=payload, method="POST")
                req.add_header("Content-Type", "application/json")
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    # Extraction du texte réponse
                    answer = data.get("response") or data.get("answer") or data.get("text") or ""
                    if answer:
                        return answer
            except Exception:
                continue
        return ""

    def _synthesize_speech(self, text: str, output_path: Path) -> bool:
        """Génère le fichier audio MP3 de la réponse via /api/tts."""
        # Nettoyage succinct du texte pour la parole
        clean_text = text.replace("**", "").replace("#", "").replace("`", "").strip()
        # Limiter à 250 mots pour garder une réponse vocale concise et pédagogique
        words = clean_text.split()
        if len(words) > 80:
            clean_text = " ".join(words[:80]) + "..."

        payload = json.dumps({"text": clean_text, "voice": "vivienne"}).encode("utf-8")

        urls_to_try = [
            f"{LOCAL_API_URL.rstrip('/')}/api/tts",
            f"{REMOTE_API_URL.rstrip('/')}/api/tts"
        ]

        for url in urls_to_try:
            try:
                req = urllib.request.Request(url, data=payload, method="POST")
                req.add_header("Content-Type", "application/json")
                with urllib.request.urlopen(req, timeout=15) as resp:
                    audio_bytes = resp.read()
                    if len(audio_bytes) > 500:
                        output_path.write_bytes(audio_bytes)
                        return True
            except Exception:
                continue
        return False

    def play_sound(self, audio_file: Path):
        """
        Lit un fichier audio sur le haut-parleur physique (I2S MAX98357A, USB ou Jack).
        Pendant toute l'élocution, la LED tricolore scintille en CYAN (SPEAKING).
        À la fin de la parole, la LED revient automatiquement à la couleur de la classe active !
        """
        if not audio_file.exists():
            self.led.restore_idle()
            return

        notify_activity()
        print("🔊 [Haut-Parleur] Élocution de la réponse vocale en cours...")

        # 1. Signaler au backend que le dispositif parle
        self._notify_speaking_status(True)

        # 2. Activer l'animation lumineuse SPEAKING sur la LED tricolore
        self.led.set_speaking()

        # 3. Lecture audio matérielle
        try:
            if str(audio_file).endswith(".mp3"):
                subprocess.run(["mpg123", "-q", str(audio_file)], check=False)
            else:
                subprocess.run(["aplay", "-q", str(audio_file)], check=False)
        except Exception as exc:
            print(f"⚠️ Erreur lecture audio physique : {exc}")
        finally:
            # 4. Signaler la fin de parole
            self._notify_speaking_status(False)
            # 5. Restauration automatique de la couleur de la classe active
            self.led.restore_idle()
            print("✅ [Haut-Parleur] Fin d'élocution. LED restaurée sur la classe active.")

    def _notify_speaking_status(self, is_speaking: bool):
        """Notifie l'écosystème local de l'état de parole."""
        try:
            url = f"{LOCAL_API_URL.rstrip('/')}/api/esp32/tts-speaking?speaking={'true' if is_speaking else 'false'}"
            req = urllib.request.Request(url, method="POST")
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                pass
        except Exception:
            pass

    def run(self):
        """Boucle principale du contrôleur matériel."""
        print("\n🎧 [HardwareController] Contrôleur 4 Boutons + Audio + LED Tricolore opérationnel.")
        print("   En attente d'interactions physiques...\n")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nArrêt du contrôleur matériel.")
            self.led.stop()


# ══════════════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    controller = HardwareController()
    controller.run()
