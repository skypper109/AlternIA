"""
Gestionnaire matériel pour AlternIA Box (Raspberry Pi 4 / 5 & Desktop Simulation).

Gère les 4 boutons physiques du dispositif :
- Bouton 1 (GPIO 17) : Sélection Classe de 10ème (Tronc Commun)
- Bouton 2 (GPIO 27) : Sélection Classe de 11ème (Générale)
- Bouton 3 (GPIO 22) : Sélection Classe de 12ème (Terminale)
- Bouton 4 (GPIO 23) : Bouton Micro / Push-to-Talk (Communication vocale avec ALTA)
- Bouton Extinction (GPIO 26) : Safe Shutdown (appui long 3s)
- LEDs d'état (GPIO 24: Vert, GPIO 25: Bleu, GPIO 18: Rouge)
- Mode dégradé / Mock automatique si exécuté sur ordinateur / Mac
"""

import logging
import os
import threading
import time
from typing import Callable, Optional

logger = logging.getLogger("AlternIA.Hardware")


class HardwareManager:
    """
    Pilote matériel pour le boîtier éducatif physique AlternIA Box (4 boutons + LEDs).
    """

    # Attribution standard des broches GPIO (BCM)
    PIN_BTN_10EME = 17      # Bouton 1 : 10ème
    PIN_BTN_11EME = 27      # Bouton 2 : 11ème
    PIN_BTN_12EME = 22      # Bouton 3 : 12ème
    PIN_BTN_MIC = 23        # Bouton 4 : Micro / Communication vocale
    PIN_SAFE_SHUTDOWN = 26  # Bouton Extinction
    
    PIN_LED_GREEN = 24      # LED Verte (Prêt / Parlant)
    PIN_LED_BLUE = 25       # LED Bleue (Écoute Micro / RAG)
    PIN_LED_RED = 18        # LED Rouge (Erreur)

    def __init__(
        self,
        on_class_10: Optional[Callable[[], None]] = None,
        on_class_11: Optional[Callable[[], None]] = None,
        on_class_12: Optional[Callable[[], None]] = None,
        on_mic_press: Optional[Callable[[], None]] = None,
        on_mic_release: Optional[Callable[[], None]] = None,
        on_shutdown_request: Optional[Callable[[], None]] = None,
    ):
        self.on_class_10 = on_class_10
        self.on_class_11 = on_class_11
        self.on_class_12 = on_class_12
        self.on_mic_press = on_mic_press
        self.on_mic_release = on_mic_release
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
        """Initialise les broches GPIO si disponible sur Raspberry Pi."""
        if not self.is_rpi:
            logger.info("Mode développement (hors Raspberry Pi) : GPIO simulé.")
            return

        try:
            import RPi.GPIO as GPIO  # pyrefly: ignore
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)

            # Entrées : 4 Boutons + Extinction (avec résistance pull-up interne)
            GPIO.setup(self.PIN_BTN_10EME, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.PIN_BTN_11EME, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.PIN_BTN_12EME, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.PIN_BTN_MIC, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.PIN_SAFE_SHUTDOWN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            # Sorties : LEDs d'état
            GPIO.setup(self.PIN_LED_GREEN, GPIO.OUT, initial=GPIO.HIGH)
            GPIO.setup(self.PIN_LED_BLUE, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(self.PIN_LED_RED, GPIO.OUT, initial=GPIO.LOW)

            self._gpio_available = True
            self._start_button_listener()
            logger.info("GPIO initialisé avec succès : 4 boutons physiques configurés.")
        except Exception as exc:
            logger.warning(f"Impossible d'initialiser le GPIO : {exc}. Mode simulé actif.")
            self._gpio_available = False

    def set_led_status(self, status: str) -> None:
        """
        Change l'état des voyants lumineux :
        - 'ready' / 'idle' : Vert fixe
        - 'listening' : Bleu fixe (micro actif)
        - 'thinking' / 'rag' : Bleu clignotant / allumé
        - 'speaking' : Jaune (Vert + Bleu)
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
            elif status in {"speaking", "tts", "thinking"}:
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
        """Surveille les 4 boutons en tâche de fond avec anti-rebond."""
        def listener():
            import RPi.GPIO as GPIO  # pyrefly: ignore
            last_b1 = GPIO.HIGH
            last_b2 = GPIO.HIGH
            last_b3 = GPIO.HIGH
            last_b4 = GPIO.HIGH
            shutdown_start = None

            while not self._stop_event.is_set():
                # Bouton 1 : 10ème
                b1 = GPIO.input(self.PIN_BTN_10EME)
                if b1 == GPIO.LOW and last_b1 == GPIO.HIGH:
                    if self.on_class_10:
                        self.on_class_10()
                last_b1 = b1

                # Bouton 2 : 11ème
                b2 = GPIO.input(self.PIN_BTN_11EME)
                if b2 == GPIO.LOW and last_b2 == GPIO.HIGH:
                    if self.on_class_11:
                        self.on_class_11()
                last_b2 = b2

                # Bouton 3 : 12ème
                b3 = GPIO.input(self.PIN_BTN_12EME)
                if b3 == GPIO.LOW and last_b3 == GPIO.HIGH:
                    if self.on_class_12:
                        self.on_class_12()
                last_b3 = b3

                # Bouton 4 : Micro / PTT Communication
                b4 = GPIO.input(self.PIN_BTN_MIC)
                if b4 == GPIO.LOW and last_b4 == GPIO.HIGH:
                    if self.on_mic_press:
                        self.on_mic_press()
                elif b4 == GPIO.HIGH and last_b4 == GPIO.LOW:
                    if self.on_mic_release:
                        self.on_mic_release()
                last_b4 = b4

                # Bouton Extinction sécurisée (appui 3s)
                s_val = GPIO.input(self.PIN_SAFE_SHUTDOWN)
                if s_val == GPIO.LOW:
                    if shutdown_start is None:
                        shutdown_start = time.time()
                    elif time.time() - shutdown_start >= 3.0:
                        logger.info("Demande d'extinction matérielle (3s).")
                        if self.on_shutdown_request:
                            self.on_shutdown_request()
                        else:
                            os.system("sudo shutdown -h now")
                        break
                else:
                    shutdown_start = None

                time.sleep(0.04)

        t = threading.Thread(target=listener, daemon=True, name="AlternIA4ButtonsListener")
        t.start()

    def cleanup(self) -> None:
        """Libère les ressources GPIO."""
        self._stop_event.set()
        if self._gpio_available:
            try:
                import RPi.GPIO as GPIO  # pyrefly: ignore
                GPIO.cleanup()
            except Exception:
                pass
