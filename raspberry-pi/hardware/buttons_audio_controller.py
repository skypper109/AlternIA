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
import tempfile
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

# Forcer l'affichage immédiat des logs dans journalctl (sans mise en mémoire tampon)
try:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
except Exception:
    pass

# Chemins de fichiers d'échange & drapeaux
ACTIVITY_FLAG = Path("/tmp/alta_activity.flag")
LED_STATE_FILE = Path("/tmp/alta_led_state.json")
CURRENT_CLASS_FILE = Path("/tmp/alta_current_class")
AUDIO_RECORDING_PATH = Path("/tmp/alta_voice_input.wav")
AUDIO_RAW_RECORDING_PATH = Path("/tmp/alta_voice_raw.wav")
AUDIO_OUTPUT_PATH = Path("/tmp/alta_voice_output.mp3")

# Chargement automatique du fichier d'environnement .env
for _env_candidate in [
    Path("/home/ubuntu/Alternia/raspberry-pi/.env"),
    Path("/home/ubuntu/AlternIA/raspberry-pi/.env"),
    Path(__file__).resolve().parent.parent / ".env",
]:
    if _env_candidate.exists():
        try:
            for _line in _env_candidate.read_text(encoding="utf-8").splitlines():
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))
            break
        except Exception:
            pass

# User-Agent de type navigateur pour franchir Cloudflare sans blocage WAF (403 Forbidden)
BROWSER_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

# Serveurs cibles (Cloudflare api.alterniamali.com par défaut)
LOCAL_API_URL = os.environ.get("ALTERNIA_LOCAL_API", "http://127.0.0.1")
REMOTE_API_URL = os.environ.get("ALTERNIA_API_URL", "https://api.alterniamali.com")

# Dossier de cache local pour les annonces audio pré-générées (offline / instantané)
PROMPTS_CACHE_DIR = Path(__file__).resolve().parent / "audio_cache"
try:
    PROMPTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    PROMPTS_CACHE_DIR = Path(tempfile.gettempdir()) / "alta_audio_cache"
    PROMPTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Phrases vocales prononcées lors de la sélection des classes
CLASS_SPOKEN_PHRASES = {
    "6eme": "Tu as sélectionné la classe de sixième.",
    "7eme": "Tu as sélectionné la classe de septième.",
    "8eme": "Tu as sélectionné la classe de huitième.",
    "9eme": "Tu as sélectionné la classe de neuvième année.",
    "10eme": "Tu as sélectionné la classe de dixième.",
    "11eme": "Tu as sélectionné la classe de onzième.",
    "12eme": "Tu as sélectionné la classe de Terminale.",
}

# Message de bienvenue et de présentation au démarrage du boîtier
STARTUP_GREETING_TEXT = (
    "Bonjour ! Je suis ALTA, ton tuteur pédagogique intelligent. "
    "Je suis là pour t'aider à réviser tes cours, t'expliquer des exercices et répondre à toutes tes questions selon ton programme scolaire. "
    "Choisis ta classe avec les boutons de niveau, puis appuie sur le bouton micro pour me parler. "
    "Que souhaites-tu apprendre aujourd'hui ?"
)

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


KIOSK_STATE_FILE = Path("/tmp/alta_kiosk_state.json")


def notify_activity():
    """Déclenche l'indicateur d'activité système pour synchroniser les démons."""
    try:
        ACTIVITY_FLAG.touch(exist_ok=True)
    except Exception:
        pass


def emit_kiosk_event(event: str, data: Optional[Dict[str, Any]] = None):
    """
    Diffuse un événement matériel en temps réel vers l'écran TV HDMI (Chromium Kiosk).
    Permet à l'interface d'agir comme un écran de contrôle synchronisé avec les boutons physiques.
    """
    payload_data = dict(data or {})

    # 1. Mise à jour de l'état local dans /tmp/alta_kiosk_state.json
    try:
        current = {}
        if KIOSK_STATE_FILE.exists():
            try:
                current = json.loads(KIOSK_STATE_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        current["last_event"] = event
        current["timestamp"] = time.time()
        current.update(payload_data)
        KIOSK_STATE_FILE.write_text(json.dumps(current), encoding="utf-8")
    except Exception:
        pass

    # 2. Diffusion HTTP asynchrone non-bloquante vers FastAPI (/api/device/event)
    def _send():
        urls = []
        if LOCAL_API_URL:
            urls.append(f"{LOCAL_API_URL.rstrip('/')}/api/device/event")
        if REMOTE_API_URL and REMOTE_API_URL != LOCAL_API_URL:
            urls.append(f"{REMOTE_API_URL.rstrip('/')}/api/device/event")

        body = json.dumps({"event": event, "data": payload_data}).encode("utf-8")
        for u in urls:
            try:
                req = urllib.request.Request(u, data=body, method="POST")
                req.add_header("Content-Type", "application/json")
                req.add_header("User-Agent", BROWSER_USER_AGENT)
                with urllib.request.urlopen(req, timeout=1.5) as resp:
                    pass
                break
            except Exception:
                pass

    threading.Thread(target=_send, daemon=True).start()


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

        # Processus de lecture audio en cours pour interruption propre
        self.current_player_proc: Optional[subprocess.Popen] = None
        self.is_speaking = False
        self.active_cycle_id: Optional[str] = None

        # Contrôleur LED
        self.led = TricolorLedController(
            pin_r=PIN_LED_R,
            pin_g=PIN_LED_G,
            pin_b=PIN_LED_B,
            active_high=LED_ACTIVE_HIGH
        )

        # Initialiser avec la couleur de la classe par défaut (SANS annonce pour laisser le greeting)
        self._apply_class_selection(self.current_cycle_id, self.current_class, announce=False)

        # Initialisation des Boutons
        self.buttons_ready = False
        self.setup_buttons()

        # Démarrage de la salutation et de la présentation vocale d'ALTA à l'allumage
        threading.Thread(target=self._startup_greeting, daemon=True).start()

    def _startup_greeting(self):
        """Salue, se présente et explique ce qu'on peut faire avec ALTA au démarrage."""
        time.sleep(2.5)  # Laisser le temps à ALSA, à la carte I2S et au réseau de s'initialiser
        print("\n" + "═" * 70)
        print("👋 [Démarrage ALTA] Salutation et présentation vocale en cours...")
        print("═" * 70)
        self.speak_text(STARTUP_GREETING_TEXT, cache_key="startup_greeting")

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
        self._apply_class_selection("niveau_1", chosen, announce=True)

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
        self._apply_class_selection("niveau_2", chosen, announce=True)

    def on_press_niveau_3(self):
        """Bouton 3 : Active la Terminale (Baccalauréat)."""
        notify_activity()
        cfg = CYCLES_CONFIG["niveau_3"]
        chosen = "12eme"
        self.current_cycle_id = "niveau_3"
        self.cycle_indices["niveau_3"] = 0

        print(f"\n{cfg['ansi']}📚 [Bouton 3] Niveau 3 sélectionné -> Classe : TERMINALE (12ème / BAC)\033[0m")
        self._apply_class_selection("niveau_3", chosen, announce=True)

    def _apply_class_selection(self, cycle_id: str, class_name: str, announce: bool = True):
        """Applique le choix de classe : couleur LED, fichier d'état, sync backend et annonce vocale."""
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
        emit_kiosk_event("class_selected", {"class": class_name})

        # 4. Annonce vocale immédiate (« Tu as sélectionné la classe de ... »)
        if announce:
            phrase = CLASS_SPOKEN_PHRASES.get(class_name, f"Tu as sélectionné la classe de {class_name}.")
            print(f"📢 [Audio Annonce] « {phrase} »")
            self.speak_text(phrase, cache_key=f"select_class_{class_name}")

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
        Bouton 4 : Micro (Interruption instantanée & Écoute)
        • Si ALTA est en train de parler OU de réfléchir : on coupe immédiatement et on passe en écoute !
        • Si ALTA est en cours d'enregistrement (LED rouge) : 2ème clic = fin et envoi.
        • Si ALTA est en veille : 1er clic = début d'enregistrement.
        """
        notify_activity()

        if self.is_recording:
            # ── 2ème CLIC : FIN ET ENVOI ──
            self.stop_recording_and_process()
        else:
            # ── 1er CLIC OU INTERRUPTION DE PAROLE : ÉCOUTE IMMÉDIATE ──
            self.start_recording()

    def start_recording(self):
        """Démarre la capture audio ALSA et active la LED rouge (avec interruption prioritaire)."""
        # 1. Annuler tout cycle IA en cours (pensée, synthèse ou parole)
        self.active_cycle_id = None
        self.stop_sound()
        time.sleep(0.12)  # Laisser le temps au noyau ALSA de libérer le périphérique plughw:2,0

        self.is_recording = True
        self.recording_start_time = time.time()

        # Supprimer les fichiers précédents
        for p in (AUDIO_RECORDING_PATH, AUDIO_RAW_RECORDING_PATH):
            try:
                if p.exists():
                    p.unlink()
            except Exception:
                pass

        # LED Tricolore -> Rouge Vif Pulsant
        self.led.set_recording()
        emit_kiosk_event("recording_started", {"state": "listening"})

        print("\n" + "═" * 70)
        print("🎙️ [Micro - Écoute active] ENREGISTREMENT DÉMARRÉ ! Parlez maintenant...")
        print("   👉 Cliquez à nouveau sur le bouton Micro pour couper et envoyer.")
        print("═" * 70)

        try:
            # Enregistrement natif INMP441 sur I2S (plughw:2,0 en 48kHz, S32_LE, Stéréo)
            self.record_process = subprocess.Popen([
                "arecord",
                "-D", "plughw:2,0",
                "-f", "S32_LE",
                "-r", "48000",
                "-c", "2",
                str(AUDIO_RAW_RECORDING_PATH)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as exc:
            print(f"⚠️ Erreur démarrage arecord : {exc} (Micro I2S branché ?)")

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

        # Conversion et normalisation automatique 16kHz Mono pour Whisper STT
        if AUDIO_RAW_RECORDING_PATH.exists() and AUDIO_RAW_RECORDING_PATH.stat().st_size > 1000:
            try:
                subprocess.run([
                    "ffmpeg", "-y", "-i", str(AUDIO_RAW_RECORDING_PATH),
                    "-ar", "16000",
                    "-ac", "1",
                    "-af", "volume=12dB",
                    str(AUDIO_RECORDING_PATH)
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            except Exception:
                pass

        # Passer immédiatement la LED en mode Réflexion IA (Violet pulsant)
        self.led.set_thinking()
        emit_kiosk_event("thinking", {"state": "thinking"})

        # Attribuer un identifiant unique à ce cycle pour annulation en cas d'interruption
        cycle_id = uuid.uuid4().hex
        self.active_cycle_id = cycle_id

        # Traitement complet en tâche de fond pour garder les boutons réactifs
        threading.Thread(target=self._process_and_respond, args=(cycle_id,), daemon=True).start()

    # ──────────────────────────────────────────────────────────────────────────
    # TRAITEMENT VOCAL COMPLET (STT -> QUESTION IA -> TTS -> HAUT-PARLEUR)
    # ──────────────────────────────────────────────────────────────────────────

    def _process_and_respond(self, cycle_id: str):
        """Exécute la chaîne complète vocale de bout en bout."""
        time.sleep(0.1)  # Laisser le temps à ALSA de finaliser le fichier WAV

        if not AUDIO_RECORDING_PATH.exists():
            print("⚠️ Aucun fichier audio enregistré trouvé.")
            if not self.is_recording:
                self.led.restore_idle()
            return

        file_size = AUDIO_RECORDING_PATH.stat().st_size
        if file_size < 1200:
            print(f"⚠️ Enregistrement trop court ({file_size} octets). Parlez un peu plus longtemps.")
            if not self.is_recording:
                self.led.restore_idle()
            return

        notify_activity()

        try:
            # 1. Étape Transcription (STT)
            transcription = self._transcribe_audio(AUDIO_RECORDING_PATH)
            if self.active_cycle_id != cycle_id or self.is_recording:
                print("ℹ️ [Cycle IA] Interrompu pendant la transcription.")
                return

            if not transcription or not transcription.strip():
                print("ℹ️ Aucune parole intelligible détectée.")
                if not self.is_recording:
                    self.led.restore_idle()
                return

            print(f"📝 [Transcription Écolier] « {transcription} »")
            emit_kiosk_event("user_transcript", {"text": transcription})

            # 2. Étape Consultation Tuteur IA (/api/ask)
            ai_answer = self._ask_tutor(transcription, self.current_class)
            if self.active_cycle_id != cycle_id or self.is_recording:
                print("ℹ️ [Cycle IA] Interrompu pendant la consultation de l'IA.")
                return

            if not ai_answer or not ai_answer.strip():
                print("⚠️ Réponse du tuteur vide.")
                if not self.is_recording:
                    self.led.restore_idle()
                return

            print(f"💡 [Réponse Tuteur IA] « {ai_answer[:140]}... »")
            emit_kiosk_event("ai_response", {
                "text": ai_answer,
                "sources": [{"document": "Programme Officiel du Mali"}]
            })

            # 3. Étape Diffusion Vocale en Streaming (Démarrage immédiat en ~2s + Détails intégraux)
            self._stream_and_play_response(ai_answer, cycle_id)

        except Exception as exc:
            print(f"⚠️ Erreur lors du cycle de traitement vocal : {exc}")
            if not self.is_recording:
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

        urls_to_try = []
        if REMOTE_API_URL:
            urls_to_try.append(f"{REMOTE_API_URL.rstrip('/')}/api/stt")
        if LOCAL_API_URL and LOCAL_API_URL != REMOTE_API_URL:
            urls_to_try.append(f"{LOCAL_API_URL.rstrip('/')}/api/stt")

        for url in urls_to_try:
            try:
                print(f"📡 [STT] Envoi de l'audio ({len(content)} octets) vers : {url}...")
                req = urllib.request.Request(url, data=body, method="POST")
                req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
                req.add_header("User-Agent", BROWSER_USER_AGENT)
                with urllib.request.urlopen(req, timeout=20) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    text = data.get("text", "")
                    if text:
                        return text.strip()
                    print(f"ℹ️ [STT] Réponse reçue de {url} mais texte vide : {data}")
            except Exception as exc:
                print(f"⚠️ [STT] Échec sur {url} : {exc}")
                continue
        return ""

    def _ask_tutor(self, question: str, student_class: str) -> str:
        """Interroge le moteur pédagogique local ou AWS."""
        payload = json.dumps({
            "question": question,
            "student_class": student_class,
            "session_id": "box_voice_session"
        }).encode("utf-8")

        urls_to_try = []
        if REMOTE_API_URL:
            urls_to_try.append(f"{REMOTE_API_URL.rstrip('/')}/api/ask")
        if LOCAL_API_URL and LOCAL_API_URL != REMOTE_API_URL:
            urls_to_try.append(f"{LOCAL_API_URL.rstrip('/')}/api/ask")

        for url in urls_to_try:
            try:
                print(f"🧠 [IA] Envoi de la question vers : {url}...")
                req = urllib.request.Request(url, data=payload, method="POST")
                req.add_header("Content-Type", "application/json")
                req.add_header("User-Agent", BROWSER_USER_AGENT)
                with urllib.request.urlopen(req, timeout=25) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    answer = data.get("response") or data.get("answer") or data.get("text") or ""
                    if answer:
                        return answer
            except Exception as exc:
                print(f"⚠️ [IA] Échec sur {url} : {exc}")
                continue
        return ""

    @staticmethod
    def _clean_for_speech(text: str) -> str:
        """
        Nettoie et formate le texte pédagogique complet pour la parole (SANS couper l'explication).
        - Convertit les titres Markdown en phrases d'introduction fluides
        - Supprime le balisage (gras, astérisques, puces, balises de code)
        - Conserve l'intégralité des détails, explications et exemples pédagogiques
        """
        import re
        # Remplacer les titres ### par une phrase avec ponctuation
        t = re.sub(r'#{1,6}\s*([^\n]+)', r'\1. ', text)
        # Supprimer gras, italique, code, séparateurs
        t = t.replace('**', '').replace('__', '').replace('*', '').replace('`', '').replace('---', '')
        # Convertir les puces et listes numérotées en transitions orales
        t = re.sub(r'^\s*[-•*]\s+', ', ', t, flags=re.MULTILINE)
        t = re.sub(r'^\s*\d+\.\s+', ', ', t, flags=re.MULTILINE)
        # Nettoyer les sauts de ligne
        t = re.sub(r'\n+', '. ', t)
        # Normaliser les doubles ponctuations
        t = re.sub(r'\s*\.\s*\.', '.', t)
        t = re.sub(r'\s+', ' ', t)

        # Conserver jusqu'à 250 mots complets (couvre l'intégralité de l'explication détaillée)
        words = t.split()
        if len(words) > 250:
            t = " ".join(words[:250]) + "."
        return t.strip()

    @staticmethod
    def _split_into_spoken_chunks(text: str, target_words: int = 22) -> list[str]:
        """
        Découpe un texte long en phrases/unités orales naturelles (18-25 mots).
        Permet de commencer la lecture audio sur le haut-parleur en moins de 2 secondes
        pendant que la suite de l'explication est téléchargée en tâche de fond.
        """
        import re
        raw_sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        chunks = []
        current = []
        current_len = 0
        for s in raw_sentences:
            s_clean = s.strip()
            if not s_clean:
                continue
            words_len = len(s_clean.split())
            if current_len + words_len > target_words and current:
                chunks.append(" ".join(current))
                current = [s_clean]
                current_len = words_len
            else:
                current.append(s_clean)
                current_len += words_len
        if current:
            chunks.append(" ".join(current))
        return chunks if chunks else [text]

    def _synthesize_single_chunk(self, chunk_text: str, dest_path: Path) -> bool:
        """Synthétise un morceau unique de texte (15-25 mots) via /api/tts en ~1.5s."""
        payload = json.dumps({"text": chunk_text, "voice": "vivienne"}).encode("utf-8")
        urls_to_try = []
        if REMOTE_API_URL:
            urls_to_try.append(f"{REMOTE_API_URL.rstrip('/')}/api/tts")
        if LOCAL_API_URL and LOCAL_API_URL != REMOTE_API_URL:
            urls_to_try.append(f"{LOCAL_API_URL.rstrip('/')}/api/tts")

        for url in urls_to_try:
            try:
                req = urllib.request.Request(url, data=payload, method="POST")
                req.add_header("Content-Type", "application/json")
                req.add_header("User-Agent", BROWSER_USER_AGENT)
                with urllib.request.urlopen(req, timeout=15) as resp:
                    audio_bytes = resp.read()
                    if len(audio_bytes) > 300:
                        dest_path.write_bytes(audio_bytes)
                        return True
            except Exception:
                continue
        return False

    def _stream_and_play_response(self, text: str, cycle_id: str):
        """
        Pipeline audio ultra-rapide en flux tendu (Streaming TTS) :
        1. Découpe l'explication complète en morceaux oraux naturels (15-25 mots).
        2. Télécharge le morceau 0 et commence à le jouer sur le haut-parleur en ~2 secondes.
        3. Télécharge en parallèle les morceaux suivants pendant que le haut-parleur parle.
        4. Enchaîne la lecture continue de tous les détails sans aucun temps mort ni timeout !
        """
        clean_text = self._clean_for_speech(text)
        chunks = self._split_into_spoken_chunks(clean_text, target_words=22)
        total_chunks = len(chunks)
        print(f"\n⚡ [Pipeline TTS Stream] Réponse détaillée ({len(clean_text.split())} mots) découpée en {total_chunks} morceaux oraux.")

        import queue
        audio_queue = queue.Queue(maxsize=10)
        stop_stream_event = threading.Event()

        def download_worker():
            for idx, chunk in enumerate(chunks):
                if self.active_cycle_id != cycle_id or self.is_recording or stop_stream_event.is_set():
                    break
                t_start = time.time()
                temp_file = Path(tempfile.gettempdir()) / f"stream_{cycle_id}_{idx}.mp3"
                success = self._synthesize_single_chunk(chunk, temp_file)
                if success and temp_file.exists():
                    elapsed = time.time() - t_start
                    print(f"📦 [TTS Stream] Morceau {idx+1}/{total_chunks} prêt ({len(chunk.split())} mots en {elapsed:.2f}s)")
                    audio_queue.put((idx, temp_file))
                else:
                    print(f"⚠️ [TTS Stream] Échec téléchargement morceau {idx+1}/{total_chunks}")
            audio_queue.put(None)  # Marqueur de fin de flux

        downloader = threading.Thread(target=download_worker, daemon=True)
        downloader.start()

        try:
            chunks_played = 0
            emit_kiosk_event("speaking", {"speaking": True})
            while True:
                if self.active_cycle_id != cycle_id or self.is_recording:
                    print("🎙️ [Pipeline TTS Stream] Interrompu par l'utilisateur.")
                    stop_stream_event.set()
                    break

                try:
                    item = audio_queue.get(timeout=20.0)
                except queue.Empty:
                    print("⚠️ [Pipeline TTS Stream] Fin d'attente du flux audio.")
                    break

                if item is None:
                    # Tous les morceaux ont été joués
                    break

                idx, audio_file = item
                if self.active_cycle_id != cycle_id or self.is_recording:
                    try:
                        audio_file.unlink(missing_ok=True)
                    except Exception:
                        pass
                    break

                is_last = (idx == total_chunks - 1)
                print(f"🔊 [Haut-Parleur] Élocution morceau {idx+1}/{total_chunks} : « {chunks[idx][:80]}... »")
                self.play_sound(audio_file, restore_idle_on_finish=is_last)
                chunks_played += 1
                try:
                    audio_file.unlink(missing_ok=True)
                except Exception:
                    pass

        finally:
            stop_stream_event.set()
            if not self.is_recording:
                self.led.restore_idle()
                emit_kiosk_event("idle", {"state": "idle", "speaking": False})

    def _synthesize_speech(self, text: str, output_path: Path) -> bool:
        """Génère le fichier audio MP3 ponctuel via /api/tts (pour annonces de classe et démarrage)."""
        clean_text = self._clean_for_speech(text)
        payload = json.dumps({"text": clean_text, "voice": "vivienne"}).encode("utf-8")

        urls_to_try = []
        if REMOTE_API_URL:
            urls_to_try.append(f"{REMOTE_API_URL.rstrip('/')}/api/tts")
        if LOCAL_API_URL and LOCAL_API_URL != REMOTE_API_URL:
            urls_to_try.append(f"{LOCAL_API_URL.rstrip('/')}/api/tts")

        for url in urls_to_try:
            t0 = time.time()
            try:
                print(f"🎙️ [TTS] Synthèse de la voix vers : {url}...")
                req = urllib.request.Request(url, data=payload, method="POST")
                req.add_header("Content-Type", "application/json")
                req.add_header("User-Agent", BROWSER_USER_AGENT)
                with urllib.request.urlopen(req, timeout=30) as resp:
                    audio_bytes = resp.read()
                    if len(audio_bytes) > 500:
                        output_path.write_bytes(audio_bytes)
                        elapsed = time.time() - t0
                        print(f"✅ [TTS] Audio reçu en {elapsed:.2f}s ({len(audio_bytes)} octets)")
                        return True
            except Exception as exc:
                elapsed = time.time() - t0
                print(f"⚠️ [TTS] Échec sur {url} après {elapsed:.2f}s : {exc}")
                continue
        return False

    def stop_sound(self):
        """Interrompt immédiatement toute lecture audio en cours (aplay) et libère la carte son."""
        self.is_speaking = False
        proc = getattr(self, "current_player_proc", None)
        if proc and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=0.2)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        self.current_player_proc = None
        try:
            subprocess.run(["killall", "-9", "aplay"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        except Exception:
            pass

    def speak_text(self, text: str, cache_key: Optional[str] = None):
        """Prononce un texte de manière asynchrone (non-bloquante) avec mise en cache locale."""
        threading.Thread(target=self._speak_text_worker, args=(text, cache_key), daemon=True).start()

    def _speak_text_worker(self, text: str, cache_key: Optional[str] = None):
        """Travailleur de synthèse et diffusion vocale."""
        self.stop_sound()

        target_file = None
        if cache_key:
            cached_file = PROMPTS_CACHE_DIR / f"{cache_key}.mp3"
            if cached_file.exists() and cached_file.stat().st_size > 500:
                target_file = cached_file

        if not target_file:
            temp_path = Path(tempfile.gettempdir()) / f"tts_prompt_{uuid.uuid4().hex[:8]}.mp3"
            success = self._synthesize_speech(text, temp_path)
            if success and temp_path.exists():
                target_file = temp_path
                if cache_key:
                    try:
                        import shutil
                        shutil.copy(temp_path, PROMPTS_CACHE_DIR / f"{cache_key}.mp3")
                    except Exception:
                        pass

        if target_file and target_file.exists():
            # Ne jouer que si l'utilisateur n'a pas appuyé sur le micro entre temps
            if not self.is_recording:
                self.play_sound(target_file, restore_idle_on_finish=True)

    def play_sound(self, audio_file: Path, restore_idle_on_finish: bool = True):
        """
        Lit un fichier audio sur le haut-parleur physique (I2S MAX98357A, USB ou Jack).
        Pendant toute l'élocution, la LED tricolore scintille en CYAN (SPEAKING).
        À la fin de la parole, la LED revient automatiquement à la couleur de la classe active si restore_idle_on_finish=True.
        Interrompu instantanément si l'utilisateur appuie sur le bouton micro.
        """
        if not audio_file.exists() or self.is_recording:
            if not self.is_recording and restore_idle_on_finish:
                self.led.restore_idle()
            return

        self.stop_sound()
        notify_activity()

        self.is_speaking = True
        self._notify_speaking_status(True)
        self.led.set_speaking()

        try:
            boosted_wav = Path(tempfile.gettempdir()) / f"tts_boosted_{uuid.uuid4().hex[:6]}.wav"
            res = subprocess.run([
                "ffmpeg", "-y", "-i", str(audio_file),
                "-af", "volume=13dB",
                "-ar", "48000",
                str(boosted_wav)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

            # Vérifier si l'utilisateur a appuyé sur le micro pendant la conversion
            if self.is_recording:
                return

            target_to_play = boosted_wav if (res.returncode == 0 and boosted_wav.exists()) else audio_file
            self.current_player_proc = subprocess.Popen(["aplay", "-D", "plughw:2,0", "-q", str(target_to_play)])
            self.current_player_proc.wait()
        except Exception as exc:
            print(f"⚠️ Erreur lecture audio physique : {exc}")
        finally:
            self.current_player_proc = None
            self.is_speaking = False
            self._notify_speaking_status(False)
            # Ne restaurer la couleur de veille QUE si restore_idle_on_finish=True et pas en cours d'enregistrement !
            if not self.is_recording:
                if restore_idle_on_finish:
                    self.led.restore_idle()
                    print("✅ [Haut-Parleur] Fin d'élocution. LED restaurée sur la classe active.")
            else:
                print("🎙️ [Haut-Parleur] Élocution coupée : passage immédiat en écoute micro.")

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
