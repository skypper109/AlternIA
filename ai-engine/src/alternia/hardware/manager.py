"""
Gestionnaire matériel pour AlternIA Box (Raspberry Pi 4 / 5).

Gère :
- Bouton physique Push-to-Talk (GPIO 17)
- Bouton d'extinction sécurisée / Safe Shutdown (GPIO 26)
- LED d'état RVB (GPIO 22: Vert=Prêt, 23: Bleu=Écoute/RAG, 24: Jaune=Synthèse)
- Mode dégradé / Mock automatique si exécuté hors Raspberry Pi
"""

import logging
import os
import sys
import threading
import time
from typing import Callable, Optional

logger = logging.getLogger("AlternIA.Hardware")


class HardwareManager:
    """
    Pilote matériel pour le boîtier éducatif AlternIA Box.
    """

    PIN_PUSH_TO_TALK = 17
    PIN_SAFE_SHUTDOWN = 26
    PIN_LED_GREEN = 22
    PIN_LED_BLUE = 23
    PIN_LED_RED = 24

    def __init__(
        self,
        on_ptt_press: Optional[Callable[[], None]] = None,
        on_ptt_release: Optional[Callable[[], None]] = None,
        on_shutdown_request: Optional[Callable[[], None]] = None,
    ):
        self.on_ptt_press = on_ptt_press
        self.on_ptt_release = on_ptt_release
        self.on_shutdown_request = on_shutdown_request

        self.is_rpi = self._detect_raspberry_pi()
        self._gpio_available = False
        self._stop_event = threading.Event()

        self._init_gpio()

    def _detect_raspberry_pi(self) -> bool:
        """Détecte si l'exécution se fait sur une carte Raspberry Pi."""
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
        """Initialise les broches GPIO si disponible."""
        if not self.is_rpi:
            logger.info("Mode développement (hors Raspberry Pi) : GPIO simulé.")
            return

        try:
            import RPi.GPIO as GPIO  # pyrefly: ignore
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)

            # Entrées (Boutons avec pull-up interne)
            GPIO.setup(self.PIN_PUSH_TO_TALK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.PIN_SAFE_SHUTDOWN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            # Sorties (LEDs)
            GPIO.setup(self.PIN_LED_GREEN, GPIO.OUT, initial=GPIO.HIGH)
            GPIO.setup(self.PIN_LED_BLUE, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(self.PIN_LED_RED, GPIO.OUT, initial=GPIO.LOW)

            self._gpio_available = True
            self._start_button_listener()
            logger.info("GPIO initialisé avec succès sur Raspberry Pi.")
        except Exception as exc:
            logger.warning(f"Impossible d'initialiser le GPIO : {exc}. Mode simulé actif.")
            self._gpio_available = False

    def set_led_status(self, status: str) -> None:
        """
        Change l'état des voyants lumineux :
        - 'ready' / 'idle' : Vert fixe
        - 'listening' : Bleu fixe
        - 'thinking' / 'rag' : Bleu clignotant
        - 'speaking' : Jaune / Vert+Bleu
        - 'error' : Rouge
        """
        if not self._gpio_available:
            return

        try:
            import RPi.GPIO as GPIO  # pyrefly: ignore
            if status in {"ready", "idle"}:
                GPIO.output(self.PIN_LED_GREEN, GPIO.HIGH)
                GPIO.output(self.PIN_LED_BLUE, GPIO.LOW)
                GPIO.output(self.PIN_LED_RED, GPIO.LOW)
            elif status == "listening":
                GPIO.output(self.PIN_LED_GREEN, GPIO.LOW)
                GPIO.output(self.PIN_LED_BLUE, GPIO.HIGH)
                GPIO.output(self.PIN_LED_RED, GPIO.LOW)
            elif status in {"speaking", "tts"}:
                GPIO.output(self.PIN_LED_GREEN, GPIO.HIGH)
                GPIO.output(self.PIN_LED_BLUE, GPIO.HIGH)
                GPIO.output(self.PIN_LED_RED, GPIO.LOW)
            elif status == "error":
                GPIO.output(self.PIN_LED_GREEN, GPIO.LOW)
                GPIO.output(self.PIN_LED_BLUE, GPIO.LOW)
                GPIO.output(self.PIN_LED_RED, GPIO.HIGH)
        except Exception as exc:
            logger.debug(f"Erreur commande LED : {exc}")

    def _start_button_listener(self) -> None:
        """Écoute les événements des boutons en tâche de fond."""
        def listener():
            import RPi.GPIO as GPIO  # pyrefly: ignore
            last_ptt = GPIO.HIGH
            shutdown_press_start = None

            while not self._stop_event.is_set():
                # Bouton PTT
                ptt_val = GPIO.input(self.PIN_PUSH_TO_TALK)
                if ptt_val == GPIO.LOW and last_ptt == GPIO.HIGH:
                    if self.on_ptt_press:
                        self.on_ptt_press()
                elif ptt_val == GPIO.HIGH and last_ptt == GPIO.LOW:
                    if self.on_ptt_release:
                        self.on_ptt_release()
                last_ptt = ptt_val

                # Bouton Extinction (appui long 3s)
                shutdown_val = GPIO.input(self.PIN_SAFE_SHUTDOWN)
                if shutdown_val == GPIO.LOW:
                    if shutdown_press_start is None:
                        shutdown_press_start = time.time()
                    elif time.time() - shutdown_press_start >= 3.0:
                        logger.info("Demande d'extinction sécurisée reçue (appui 3s).")
                        if self.on_shutdown_request:
                            self.on_shutdown_request()
                        else:
                            os.system("sudo shutdown -h now")
                        break
                else:
                    shutdown_press_start = None

                time.sleep(0.05)

        t = threading.Thread(target=listener, daemon=True, name="AlternIAHardwareListener")
        t.start()

    def cleanup(self) -> None:
        """Nettoie les broches GPIO lors de l'arrêt."""
        self._stop_event.set()
        if self._gpio_available:
            try:
                import RPi.GPIO as GPIO  # pyrefly: ignore
                GPIO.cleanup()
            except Exception:
                pass
