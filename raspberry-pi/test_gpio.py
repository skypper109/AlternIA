#!/usr/bin/env python3
"""
Outil de Diagnostic et de Test Matériel GPIO pour Raspberry Pi 3.
Permet de tester les 4 boutons de classe/micro et les 3 LEDs d'état.
"""

import sys
import time
import config

try:
    import RPi.GPIO as GPIO  # type: ignore
except ImportError:
    print("❌ Erreur : RPi.GPIO n'est pas installé ou vous n'êtes pas sur un Raspberry Pi.")
    print("   Sur Raspberry Pi OS : sudo apt install python3-rpi.gpio")
    sys.exit(1)


def test_leds():
    print("\n💡 1. Test des LEDs d'état...")
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    leds = [
        ("Verte (Prêt)", config.PIN_LED_GREEN),
        ("Bleue (Micro)", config.PIN_LED_BLUE),
        ("Rouge (Erreur)", config.PIN_LED_RED),
    ]

    for name, pin in leds:
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
        print(f"   -> Allumage LED {name} (GPIO {pin})...")
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(1.0)
        GPIO.output(pin, GPIO.LOW)

    print("   -> Test combiné : Toutes les LEDs allumées pendant 1.5s...")
    for _, pin in leds:
        GPIO.output(pin, GPIO.HIGH)
    time.sleep(1.5)
    for _, pin in leds:
        GPIO.output(pin, GPIO.LOW)
    print("✅ Test LEDs terminé avec succès.")


def test_buttons():
    print("\n🔘 2. Test interactif des boutons physiques (Appuyez sur chaque bouton)...")
    print("   (Pour quitter, appuyez sur Ctrl+C)")

    buttons = {
        config.PIN_BTN_1: "Bouton 1 (6ème Fondamental / 10ème Lycée)",
        config.PIN_BTN_2: "Bouton 2 (7e/8e Fondamental / 11ème Lycée)",
        config.PIN_BTN_3: "Bouton 3 (9ème DEF / Terminale Baccalauréat)",
        config.PIN_BTN_MIC: "Bouton 4 (Micro Push-To-Talk)",
        config.PIN_BTN_CYCLE: "Bouton Cycle (Bascule Fondamental / Lycée)",
        config.PIN_SAFE_SHUTDOWN: "Bouton Extinction Propre (Safe Shutdown)",
    }

    for pin in buttons:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    last_states = {pin: GPIO.HIGH for pin in buttons}

    try:
        while True:
            for pin, label in buttons.items():
                current = GPIO.input(pin)
                if current == GPIO.LOW and last_states[pin] == GPIO.HIGH:
                    print(f"   👉 [CLIC DÉTECTÉ] : {label} (GPIO {pin}) !")
                last_states[pin] = current
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nFin du test des boutons.")
    finally:
        GPIO.cleanup()


def main():
    print("=" * 65)
    print("  🇲🇱  DIAGNOSTIC MATÉRIEL GPIO — ALTERNIA BOX (RASPBERRY PI 3)  🇲🇱")
    print("=" * 65)
    test_leds()
    test_buttons()


if __name__ == "__main__":
    main()
