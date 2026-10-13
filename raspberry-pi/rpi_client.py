#!/usr/bin/env python3
"""
AlternIA Box - Client Matériel Autonome pour Raspberry Pi 3.
Gère les boutons GPIO, le micro USB/ALSA, les LEDs d'état,
la sélection des classes (Fondamental & Lycée) et de l'école.
"""

import logging
import os
import signal
import subprocess
import sys
import threading
import time
from typing import Optional

import requests

import config

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (AlternIA-RPi) %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("AlternIA.RPi")


class RPiHardwareManager:
    """Gère les entrées boutons et sorties LEDs sur le Raspberry Pi 3."""

    def __init__(self, client: "AlternIABoxClient"):
        self.client = client
        self.is_rpi = self._detect_raspberry_pi()
        self._gpio_available = False
        self._mic_recording = False
        self._shutdown_timer: Optional[threading.Timer] = None

        self._init_gpio()

    def _detect_raspberry_pi(self) -> bool:
        """Détecte si l'exécution se fait sur Raspberry Pi."""
        try:
            if os.path.exists("/proc/device-tree/model"):
                with open("/proc/device-tree/model", "r") as f:
                    model = f.read().lower()
                    if "raspberry pi" in model:
                        return True
        except Exception:
            pass
        return False

    def _init_gpio(self) -> None:
        """Initialise la bibliothèque RPi.GPIO."""
        if not self.is_rpi:
            logger.info("ℹ️ Exécution hors Raspberry Pi : Mode simulation GPIO actif.")
            return

        try:
            import RPi.GPIO as GPIO  # type: ignore

            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)

            # Entrées (Boutons avec Pull-Up interne)
            for pin in [
                config.PIN_BTN_1,
                config.PIN_BTN_2,
                config.PIN_BTN_3,
                config.PIN_BTN_MIC,
                config.PIN_BTN_CYCLE,
                config.PIN_SAFE_SHUTDOWN,
            ]:
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            # Sorties (LEDs d'état)
            for pin in [config.PIN_LED_GREEN, config.PIN_LED_BLUE, config.PIN_LED_RED]:
                GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

            # Allumer LED Verte (Prêt)
            GPIO.output(config.PIN_LED_GREEN, GPIO.HIGH)

            # Attachement des interruptions / événements boutons
            GPIO.add_event_detect(
                config.PIN_BTN_1,
                GPIO.FALLING,
                callback=lambda ch: self._on_btn_1_pressed(),
                bouncetime=250,
            )
            GPIO.add_event_detect(
                config.PIN_BTN_2,
                GPIO.FALLING,
                callback=lambda ch: self._on_btn_2_pressed(),
                bouncetime=250,
            )
            GPIO.add_event_detect(
                config.PIN_BTN_3,
                GPIO.FALLING,
                callback=lambda ch: self._on_btn_3_pressed(),
                bouncetime=250,
            )
            GPIO.add_event_detect(
                config.PIN_BTN_CYCLE,
                GPIO.FALLING,
                callback=lambda ch: self.client.toggle_cycle(),
                bouncetime=300,
            )

            # Bouton Micro : PTT (Push-To-Talk)
            GPIO.add_event_detect(
                config.PIN_BTN_MIC,
                GPIO.BOTH,
                callback=self._on_mic_event,
                bouncetime=80,
            )

            # Bouton extinction propre
            GPIO.add_event_detect(
                config.PIN_SAFE_SHUTDOWN,
                GPIO.BOTH,
                callback=self._on_shutdown_event,
                bouncetime=100,
            )

            self._gpio_available = True
            logger.info("✅ GPIO initialisé avec succès sur Raspberry Pi 3.")
        except Exception as exc:
            logger.warning(f"⚠️ Erreur initialisation RPi.GPIO : {exc}. Mode simulé actif.")
            self._gpio_available = False

    def set_leds(self, green: bool = False, blue: bool = False, red: bool = False) -> None:
        """Contrôle les 3 LEDs d'état."""
        if not self._gpio_available:
            return
        try:
            import RPi.GPIO as GPIO  # type: ignore

            GPIO.output(config.PIN_LED_GREEN, GPIO.HIGH if green else GPIO.LOW)
            GPIO.output(config.PIN_LED_BLUE, GPIO.HIGH if blue else GPIO.LOW)
            GPIO.output(config.PIN_LED_RED, GPIO.HIGH if red else GPIO.LOW)
        except Exception:
            pass

    def _on_btn_1_pressed(self) -> None:
        """Action Bouton 1 selon le cycle."""
        cls = config.CYCLE_BUTTON_MAPPING[self.client.current_cycle][1]
        self.client.set_class(cls)

    def _on_btn_2_pressed(self) -> None:
        """Action Bouton 2 selon le cycle."""
        cls = config.CYCLE_BUTTON_MAPPING[self.client.current_cycle][2]
        self.client.set_class(cls)

    def _on_btn_3_pressed(self) -> None:
        """Action Bouton 3 selon le cycle."""
        cls = config.CYCLE_BUTTON_MAPPING[self.client.current_cycle][3]
        self.client.set_class(cls)

    def _on_mic_event(self, channel: int) -> None:
        """Gestion Push-To-Talk du Bouton Micro."""
        if not self._gpio_available:
            return
        import RPi.GPIO as GPIO  # type: ignore

        is_pressed = GPIO.input(config.PIN_BTN_MIC) == GPIO.LOW
        if is_pressed and not self._mic_recording:
            self._mic_recording = True
            self.client.start_listening()
        elif not is_pressed and self._mic_recording:
            self._mic_recording = False
            self.client.stop_listening_and_send()

    def _on_shutdown_event(self, channel: int) -> None:
        """Appui 3s pour extinction sécurisée du Raspberry Pi."""
        if not self._gpio_available:
            return
        import RPi.GPIO as GPIO  # type: ignore

        if GPIO.input(config.PIN_SAFE_SHUTDOWN) == GPIO.LOW:
            # Démarrer timer 3 secondes
            self._shutdown_timer = threading.Timer(3.0, self._trigger_safe_shutdown)
            self._shutdown_timer.start()
        else:
            if self._shutdown_timer:
                self._shutdown_timer.cancel()
                self._shutdown_timer = None

    def _trigger_safe_shutdown(self) -> None:
        logger.warning("🛑 Extinction sécurisée demandée. Arrêt du Raspberry Pi 3...")
        self.set_leds(red=True)
        self.client.speak_text("Extinction du boîtier AlternIA. À bientôt !")
        os.system("sudo shutdown -h now")

    def cleanup(self) -> None:
        if self._gpio_available:
            try:
                import RPi.GPIO as GPIO  # type: ignore

                GPIO.cleanup()
            except Exception:
                pass


class AlternIABoxClient:
    """Client principal AlternIA Box pour Raspberry Pi 3."""

    def __init__(self):
        self.server_url = config.SERVER_URL.rstrip("/")
        self.current_cycle = config.DEFAULT_CYCLE  # 'fondamental' ou 'lycee'
        self.current_class = config.DEFAULT_CLASS  # '6eme' par défaut
        self.current_school = config.DEFAULT_SCHOOL
        self.session_id = f"rpi3_session_{int(time.time())}"

        self.hardware = RPiHardwareManager(self)
        self._record_process: Optional[subprocess.Popen] = None
        self._is_recording = False
        self._is_processing = False

        # Vérifier la présence des utilitaires audio ALSA
        self._has_arecord = self._check_command("arecord")
        self._has_aplay = self._check_command("aplay")
        self._has_mpg123 = self._check_command("mpg123")

    def _check_command(self, cmd: str) -> bool:
        try:
            subprocess.run(["which", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            return False

    # =========================================================================
    # GESTION DES CLASSES ET CYCLES
    # =========================================================================

    def toggle_cycle(self) -> None:
        """Bascule entre le cycle Fondamental et le cycle Lycée."""
        if self.current_cycle == "fondamental":
            self.current_cycle = "lycee"
            self.set_class("10eme")
        else:
            self.current_cycle = "fondamental"
            self.set_class("6eme")
        logger.info(f"🔄 Bascule de cycle : {self.current_cycle.upper()} actif.")

    def set_class(self, class_id: str) -> None:
        """Définit la classe active et synchronise avec le serveur / LEDs."""
        self.current_class = class_id
        label = config.CLASS_NAMES.get(class_id, class_id)
        logger.info(f"🎓 Classe configurée : {label}")

        # Annonce vocale
        speech = config.CLASS_SPEECH_ANNOUNCEMENTS.get(class_id, f"Classe {class_id} sélectionnée.")
        self.speak_text(speech)

        # Synchronisation avec le serveur AlternIA
        self._sync_class_with_server(class_id)

    def set_school(self, school_name: str) -> None:
        """Définit l'établissement scolaire."""
        self.current_school = school_name.strip()
        logger.info(f"🏫 Établissement scolaire : {self.current_school}")
        self.speak_text(f"Établissement {self.current_school} enregistré.")

    def _sync_class_with_server(self, class_id: str) -> None:
        """Notifie le serveur AlternIA (LEDs ESP32 et Kiosk)."""
        def _post():
            try:
                requests.post(
                    f"{self.server_url}/api/esp32/select-class",
                    params={"classe": class_id, "mic_connected": "true"},
                    timeout=3,
                )
            except Exception as e:
                logger.debug(f"Note sync serveur : {e}")

        threading.Thread(target=_post, daemon=True).start()

    # =========================================================================
    # GESTION AUDIO (MICROPHONE & SYNTHÈSE VOCALE)
    # =========================================================================

    def start_listening(self) -> None:
        """Démarre l'enregistrement audio via arecord (ALSA natif léger)."""
        if self._is_recording or self._is_processing:
            return

        self._is_recording = True
        self.hardware.set_leds(blue=True)  # LED Bleue = Écoute
        logger.info("🎙️ Enregistrement de la question de l'élève en cours...")

        try:
            # Enregistrement WAV 16kHz Mono 16-bit
            cmd = [
                "arecord",
                "-D", config.ALSA_INPUT_DEVICE or "default",
                "-f", "S16_LE",
                "-r", str(config.AUDIO_RATE),
                "-c", "1",
                "-t", "wav",
                "-d", str(config.AUDIO_MAX_RECORD_SEC),
                "-q",
                config.TEMP_WAV_PATH,
            ]
            self._record_process = subprocess.Popen(cmd)
        except Exception as exc:
            logger.error(f"Erreur lancement arecord : {exc}")
            self._is_recording = False
            self.hardware.set_leds(green=True)

    def stop_listening_and_send(self) -> None:
        """Arrête l'enregistrement et envoie au serveur AlternIA."""
        if not self._is_recording:
            return

        self._is_recording = False
        if self._record_process:
            try:
                self._record_process.terminate()
                self._record_process.wait(timeout=1.0)
            except Exception:
                pass
            self._record_process = None

        logger.info("⏹️ Enregistrement terminé. Envoi au serveur AlternIA...")
        self.hardware.set_leds(green=True, blue=True)  # Cyan = Réflexion
        self._is_processing = True

        threading.Thread(target=self._process_and_query_server, daemon=True).start()

    def _process_and_query_server(self) -> None:
        """Transmet l'audio au serveur AlternIA avec la classe et l'école."""
        try:
            if not os.path.exists(config.TEMP_WAV_PATH) or os.path.getsize(config.TEMP_WAV_PATH) < 4000:
                logger.warning("Fichier audio trop court ou vide.")
                self.speak_text("Je n'ai pas entendu ta question. Réessaie en maintenant le bouton micro.")
                return

            # Appel API Vocal AlternIA
            files = {"file": ("query.wav", open(config.TEMP_WAV_PATH, "rb"), "audio/wav")}
            data = {
                "student_class": self.current_class,
                "school": self.current_school,
                "session_id": self.session_id,
                "device_id": config.DEVICE_ID,
            }

            resp = requests.post(
                f"{self.server_url}/api/chat/ask-voice",
                files=files,
                data=data,
                timeout=config.REQUEST_TIMEOUT,
            )

            if resp.status_code == 200:
                result = resp.json()
                text_response = result.get("response", "")
                logger.info(f"🤖 Réponse ALTA : {text_response}")

                audio_url = result.get("audio_url")
                if audio_url:
                    self._play_remote_audio(audio_url)
                else:
                    self.speak_text(text_response)
            else:
                logger.error(f"Erreur serveur ({resp.status_code}) : {resp.text}")
                self.hardware.set_leds(red=True)
                self.speak_text("Désolé, le serveur n'a pas pu traiter ta demande.")

        except requests.exceptions.ConnectionError:
            logger.error("Impossible de contacter le serveur AlternIA.")
            self.hardware.set_leds(red=True)
            self.speak_text("Erreur de connexion au serveur AlternIA.")
        except Exception as exc:
            logger.error(f"Erreur traitement vocal : {exc}", exc_info=True)
            self.hardware.set_leds(red=True)
            self.speak_text("Une erreur est survenue lors de la réponse.")
        finally:
            self._is_processing = False
            self.hardware.set_leds(green=True)  # Retour au vert (prêt)

    def speak_text(self, text: str) -> None:
        """Synthétise et joue un texte sur le haut-parleur local du Pi 3."""
        if not text:
            return

        logger.info(f"🔊 ALTA (TTS) : {text}")
        # 1. Tentative avec espeak-ng si disponible localement (très léger sur Pi 3)
        if self._check_command("espeak-ng"):
            try:
                subprocess.run(
                    ["espeak-ng", "-v", "fr-fr", "-s", "150", "-p", "50", text],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return
            except Exception:
                pass

        # 2. Sinon, demande de synthèse TTS au serveur AlternIA
        try:
            tts_resp = requests.get(
                f"{self.server_url}/api/tts/synthesize",
                params={"text": text},
                timeout=10,
                stream=True,
            )
            if tts_resp.status_code == 200:
                with open(config.TEMP_TTS_PATH, "wb") as f:
                    for chunk in tts_resp.iter_content(chunk_size=4096):
                        f.write(chunk)
                self._play_local_file(config.TEMP_TTS_PATH)
        except Exception as e:
            logger.debug(f"Note TTS : {e}")

    def _play_remote_audio(self, url: str) -> None:
        """Télécharge et joue un flux audio distant."""
        try:
            full_url = url if url.startswith("http") else f"{self.server_url}{url}"
            r = requests.get(full_url, stream=True, timeout=10)
            if r.status_code == 200:
                with open(config.TEMP_TTS_PATH, "wb") as f:
                    for chunk in r.iter_content(chunk_size=4096):
                        f.write(chunk)
                self._play_local_file(config.TEMP_TTS_PATH)
        except Exception as e:
            logger.error(f"Erreur lecture audio distant : {e}")

    def _play_local_file(self, file_path: str) -> None:
        """Joue un fichier WAV ou MP3 sur le périphérique audio ALSA."""
        if file_path.endswith(".wav") and self._has_aplay:
            cmd = ["aplay", "-q"]
            if config.ALSA_OUTPUT_DEVICE:
                cmd.extend(["-D", config.ALSA_OUTPUT_DEVICE])
            cmd.append(file_path)
            subprocess.run(cmd)
        elif self._has_mpg123:
            cmd = ["mpg123", "-q"]
            if config.ALSA_OUTPUT_DEVICE:
                cmd.extend(["-a", config.ALSA_OUTPUT_DEVICE])
            cmd.append(file_path)
            subprocess.run(cmd)
        else:
            # Fallback mpv / paplay
            subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", file_path])

    # =========================================================================
    # CYCLE DE VIE ET BOUCLE PRINCIPALE
    # =========================================================================

    def run(self) -> None:
        """Démarre le boîtier et la boucle d'événements."""
        self.hardware.set_leds(green=True)
        cycle_txt = "Fondamental" if self.current_cycle == "fondamental" else "Lycée"
        logger.info("=" * 65)
        logger.info("  🇲🇱  ALTERNIA BOX — DÉMARRAGE SUR RASPBERRY PI 3  🇲🇱")
        logger.info(f"  Serveur AlternIA : {self.server_url}")
        logger.info(f"  Cycle Actif      : {cycle_txt}")
        logger.info(f"  Classe Actuelle  : {config.CLASS_NAMES.get(self.current_class, self.current_class)}")
        logger.info(f"  Établissement    : {self.current_school}")
        logger.info("=" * 65)

        self.speak_text(f"Boîtier AlternIA prêt. Classe {config.CLASS_NAMES.get(self.current_class, self.current_class)} activée.")

        # Si nous sommes hors RPi, offrir une invite interactive pour tester
        if not self.hardware.is_rpi:
            self._run_desktop_simulation()
        else:
            # Sur vrai RPi, attendre les signaux de terminaison
            signal.pause()

    def _run_desktop_simulation(self) -> None:
        """Mode simulation clavier sur machine de développement."""
        print("\n🎛️  COMMANDES CLAVIER (Simulation RPi 3) :")
        print("  [6, 7, 8, 9] -> Classes Fondamentales")
        print("  [1, 2, 3]    -> Classes Lycée (10ème, 11ème, Terminale)")
        print("  [c]          -> Basculer de cycle (Fondamental <-> Lycée)")
        print("  [e]          -> Changer le nom de l'école")
        print("  [ESPACE]     -> Parler (1er appui: démarre écoute / 2e appui: envoie)")
        print("  [q]          -> Quitter\n")

        try:
            while True:
                cmd = input("👉 Touche [6,7,8,9, 1,2,3, c, e, ESPACE, q] : ").strip().lower()
                if cmd == "q":
                    break
                elif cmd in {"6", "7", "8", "9"}:
                    self.current_cycle = "fondamental"
                    self.set_class(f"{cmd}eme")
                elif cmd in {"1", "2", "3"}:
                    self.current_cycle = "lycee"
                    mapping = {"1": "10eme", "2": "11eme", "3": "12eme"}
                    self.set_class(mapping[cmd])
                elif cmd == "c":
                    self.toggle_cycle()
                elif cmd == "e":
                    nom = input("🏫 Nom de l'école : ").strip()
                    if nom:
                        self.set_school(nom)
                elif cmd == "" or cmd == " ":
                    if not self._is_recording:
                        self.start_listening()
                        input("🔴 Enregistrement en cours... Appuyez sur Entrée pour terminer : ")
                        self.stop_listening_and_send()
        except (KeyboardInterrupt, EOFError):
            pass

    def stop(self) -> None:
        """Arrêt propre du client."""
        logger.info("Arrêt du client AlternIA Box...")
        self.hardware.cleanup()


def main():
    client = AlternIABoxClient()

    def handle_sig(sig, frame):
        client.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sig)
    signal.signal(signal.SIGTERM, handle_sig)

    client.run()


if __name__ == "__main__":
    main()
