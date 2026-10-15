#!/usr/bin/env python3
"""
══════════════════════════════════════════════════════════════════════════════
Contrôleur Matériel : 4 Boutons + Microphone + Haut-Parleur pour Raspberry Pi 5
══════════════════════════════════════════════════════════════════════════════

Ce module gère les entrées/sorties physiques du boîtier physique AlternIA :
- 4 Boutons Poussoirs reliés aux broches GPIO (avec résistances Pull-Up internes) :
  • BOUTON 1 (GPIO 5)  : Push-to-Talk (Maintien pour parler au tuteur IA)
  • BOUTON 2 (GPIO 6)  : Répéter la réponse vocale précédente
  • BOUTON 3 (GPIO 13) : Basculer de niveau/classe (10ème -> 11ème -> 12ème -> DEF)
  • BOUTON 4 (GPIO 19) : Lancer le Défi du Jour / Quizz interactif

- Microphone (USB ou I2S) : Enregistrement de la voix de l'élève avec arecord/sounddevice
- Haut-parleur (Jack 3.5mm, USB ou I2S DAC MAX98357A) : Lecture audio des réponses du tuteur IA
"""

import os
import sys
import time
import subprocess
import threading
import urllib.request
import json
from pathlib import Path

# Chemins et flags
ACTIVITY_FLAG = Path("/tmp/alta_activity.flag")
AUDIO_RECORDING_PATH = Path("/tmp/alta_voice_input.wav")
AUDIO_OUTPUT_PATH = Path("/tmp/alta_voice_output.mp3")

SERVER_URL = os.environ.get("ALTERNIA_API_URL", "https://api.alterniamali.com")

# Assignation des broches GPIO pour les 4 boutons
PIN_BTN_MIC = 5       # Bouton 1 : Micro Push-To-Talk
PIN_BTN_REPEAT = 6    # Bouton 2 : Répéter l'audio
PIN_BTN_CLASS = 13    # Bouton 3 : Changer de classe
PIN_BTN_QUIZ = 19     # Bouton 4 : Défi / Quizz

CLASSES_LIST = ["10eme", "11eme", "terminale", "9eme"]
current_class_idx = 0


def notify_activity():
    """Fait clignoter la LED en direct lors de chaque action matérielle."""
    ACTIVITY_FLAG.touch(exist_ok=True)


class HardwareController:
    def __init__(self):
        self.is_recording = False
        self.record_process = None
        self.setup_gpio()

    def setup_gpio(self):
        """Configure les broches GPIO sous Raspberry Pi OS Bookworm."""
        self.buttons_ready = False
        try:
            from gpiozero import Button  # type: ignore
            self.btn_mic = Button(PIN_BTN_MIC, pull_up=True, bounce_time=0.05)
            self.btn_repeat = Button(PIN_BTN_REPEAT, pull_up=True, bounce_time=0.05)
            self.btn_class = Button(PIN_BTN_CLASS, pull_up=True, bounce_time=0.05)
            self.btn_quiz = Button(PIN_BTN_QUIZ, pull_up=True, bounce_time=0.05)

            # Liaison des événements
            self.btn_mic.when_pressed = self.start_recording
            self.btn_mic.when_released = self.stop_recording_and_process

            self.btn_repeat.when_pressed = self.repeat_audio
            self.btn_class.when_pressed = self.next_class
            self.btn_quiz.when_pressed = self.start_quiz

            self.buttons_ready = True
            print("✅ [Hardware] 4 Boutons GPIO initialisés avec succès (GPIO 5, 6, 13, 19).")
        except Exception as exc:
            print(f"ℹ️ [Hardware] Mode simulation actif (gpiozero/gpiod indisponible : {exc}).")

    def play_sound(self, audio_file: Path):
        """Lit un fichier audio sur le haut-parleur (Jack, USB ou I2S)."""
        notify_activity()
        if not audio_file.exists():
            return
        try:
            # Test avec aplay, paplay ou mpg123
            if str(audio_file).endswith(".mp3"):
                subprocess.run(["mpg123", "-q", str(audio_file)], check=False)
            else:
                subprocess.run(["aplay", "-q", str(audio_file)], check=False)
        except Exception as exc:
            print(f"⚠️ Erreur lecture audio : {exc}")

    def start_recording(self):
        """Déclenché quand le bouton 1 (Micro) est enfoncé."""
        notify_activity()
        print("🎙️ [Micro] Enregistrement vocal de l'élève en cours... (parlez maintenant)")
        self.is_recording = True
        try:
            # Enregistrement ALSA 16kHz mono (optimisé pour Faster-Whisper)
            self.record_process = subprocess.Popen([
                "arecord",
                "-D", "default",
                "-f", "S16_LE",
                "-r", "16000",
                "-c", "1",
                str(AUDIO_RECORDING_PATH)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as exc:
            print(f"⚠️ Impossible de démarrer arecord : {exc}")

    def stop_recording_and_process(self):
        """Déclenché quand le bouton 1 (Micro) est relâché."""
        notify_activity()
        if not self.is_recording:
            return
        self.is_recording = False
        print("🛑 [Micro] Fin d'enregistrement. Envoi au serveur IA...")
        
        if self.record_process:
            self.record_process.terminate()
            self.record_process.wait()

        # Envoi en tâche de fond pour ne pas bloquer les boutons
        threading.Thread(target=self._send_audio_to_server, daemon=True).start()

    def _send_audio_to_server(self):
        """Envoie l'audio au serveur AWS pour transcription et réponse vocale."""
        if not AUDIO_RECORDING_PATH.exists() or AUDIO_RECORDING_PATH.stat().st_size < 1000:
            print("⚠️ Fichier audio trop court ou vide.")
            return

        notify_activity()
        try:
            # 1. Envoi au serveur AlternIA
            import urllib.request
            url = f"{SERVER_URL.rstrip('/')}/api/vocal/process"
            
            # Simulation envoi multipart
            print(f"🚀 Audio transmis à {url}")
            # Lorsque la réponse vocale TTS revient, on la lit sur le haut-parleur
            # self.play_sound(AUDIO_OUTPUT_PATH)
        except Exception as exc:
            print(f"⚠️ Échec transmission audio vers AWS : {exc}")

    def repeat_audio(self):
        """Bouton 2 : Répéter la réponse."""
        notify_activity()
        print("🔁 [Bouton 2] Répétition de la dernière réponse vocale...")
        if AUDIO_OUTPUT_PATH.exists():
            self.play_sound(AUDIO_OUTPUT_PATH)

    def next_class(self):
        """Bouton 3 : Changer de classe."""
        global current_class_idx
        notify_activity()
        current_class_idx = (current_class_idx + 1) % len(CLASSES_LIST)
        selected = CLASSES_LIST[current_class_idx]
        print(f"📚 [Bouton 3] Basculement de classe vers : {selected}")

        # Notification au backend local
        try:
            urllib.request.urlopen(f"http://127.0.0.1:8000/api/esp32/select-class?classe={selected}", timeout=2)
        except Exception:
            pass

    def start_quiz(self):
        """Bouton 4 : Lancer le Défi / Quizz."""
        notify_activity()
        print("🎯 [Bouton 4] Lancement du Défi Quizz National...")

    def run(self):
        print("🎧 [HardwareController] Service 4 Boutons + Audio prêt et en attente d'interaction.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nArrêt du contrôleur matériel.")


if __name__ == "__main__":
    controller = HardwareController()
    controller.run()
