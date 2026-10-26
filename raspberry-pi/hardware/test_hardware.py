#!/usr/bin/env python3
"""
══════════════════════════════════════════════════════════════════════════════
Script de Test Matériel AlternIA Box (Raspberry Pi 5)
══════════════════════════════════════════════════════════════════════════════
Ce script teste tous les périphériques matériels :
1. Haut-Parleur (I2S MAX98357A, USB ou Jack)
2. Microphone (USB ou Jack)
3. LED Tricolore RGB (GPIO 17=Rouge, 27=Vert, 22=Bleu)
4. 4 Boutons Poussoirs (GPIO 5=Niv 1, 6=Niv 2, 13=Niv 3, 26=Micro Toggle)

Usage :
  python3 test_hardware.py
"""

import os
import sys
import time
import subprocess
from pathlib import Path

print("=" * 76)
print("   🇲🇱  TEST MATÉRIEL OFFICIEL ALTERNIA BOX (Raspberry Pi 5)  🇲🇱")
print("=" * 76)

# 1. Test du Haut-Parleur
print("\n[1/4] Test du Haut-Parleur / Sortie Audio...")
try:
    print("🔊 Émission d'un son sinusoïdal de test (2 secondes)...")
    subprocess.run(["speaker-test", "-t", "sine", "-f", "440", "-l", "1"], check=False)
    print("✅ Si vous avez entendu le bip, l'amplificateur audio fonctionne correctement.")
except Exception as e:
    print(f"⚠️ Erreur test haut-parleur : {e}")

# 2. Test du Microphone
print("\n[2/4] Test du Microphone...")
test_wav = Path("/tmp/test_mic.wav")
try:
    print("🎙️ Enregistrement de 3 secondes sur le micro I2S (Parlez à voix haute)...")
    subprocess.run([
        "arecord", "-D", "plughw:2,0", "-f", "S32_LE", "-r", "48000", "-c", "2", "-d", "3", str(test_wav)
    ], check=True)
    boosted_wav = Path("/tmp/test_mic_boosted.wav")
    subprocess.run([
        "ffmpeg", "-y", "-i", str(test_wav), "-ar", "48000", "-af", "volume=12dB", str(boosted_wav)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    target = boosted_wav if boosted_wav.exists() else test_wav
    print("🔊 Réécoute immédiate de l'enregistrement dans le haut-parleur...")
    subprocess.run(["aplay", "-D", "plughw:2,0", "-q", str(target)], check=True)
    print("✅ Si vous avez entendu votre voix, le microphone fonctionne parfaitement.")
except Exception as e:
    print(f"⚠️ Erreur test microphone : {e} (Assurez-vous que le micro I2S est branché)")

# 3. Test de la LED Tricolore RGB
print("\n[3/4] Test de la LED Tricolore RGB (GPIO 17=Rouge, 27=Vert, 22=Bleu)...")
pin_r = int(os.environ.get("PIN_LED_R", 17))
pin_g = int(os.environ.get("PIN_LED_G", 27))
pin_b = int(os.environ.get("PIN_LED_B", 22))

test_colors = [
    ("🔴 Rouge (Enregistrement Micro)", (1.0, 0.0, 0.0)),
    ("🟢 Turquoise / Vert (Niveau 1 Fondamental)", (0.0, 1.0, 0.55)),
    ("🔵 Bleu Royal (Niveau 2 Secondaire)", (0.1, 0.35, 1.0)),
    ("🟠 Ambre / Orange (Niveau 3 Terminale)", (1.0, 0.45, 0.0)),
    ("🟣 Violet (Réflexion IA)", (0.75, 0.0, 1.0)),
    ("🌊 Cyan (Dispositif en train de parler)", (0.15, 0.85, 1.0)),
]

try:
    from gpiozero import RGBLED  # type: ignore
    led = RGBLED(red=pin_r, green=pin_g, blue=pin_b, active_high=True, pwm=True)
    print(f"💡 Initialisation de la LED RGB sur GPIO {pin_r}, {pin_g}, {pin_b}...")
    for label, (r, g, b) in test_colors:
        print(f"   -> Affichage : {label}")
        led.color = (r, g, b)
        time.sleep(1.0)
    led.off()
    print("✅ Test LED Tricolore terminé avec succès.")
except ImportError:
    print("ℹ️ Module gpiozero non installé, simulation des couleurs LED :")
    for label, (r, g, b) in test_colors:
        cr, cg, cb = int(r * 255), int(g * 255), int(b * 255)
        print(f"   \033[38;2;{cr};{cg};{cb}m[SIMULATION LED] {label} (RGB: {cr}, {cg}, {cb})\033[0m")
        time.sleep(0.3)
except Exception as e:
    print(f"ℹ️ Test physique LED non disponible ({e}), simulation console OK.")

# 4. Test des 4 Boutons GPIO
print("\n[4/4] Test des 4 Boutons GPIO...")
print("   • Bouton 1 (GPIO 5)  : Niveau 1 (Fondamental : 6e, 7e, 8e, 9e / DEF)")
print("   • Bouton 2 (GPIO 6)  : Niveau 2 (Secondaire : 10e, 11e)")
print("   • Bouton 3 (GPIO 13) : Niveau 3 (Terminale / Baccalauréat)")
print("   • Bouton 4 (GPIO 26) : Micro Toggle (1er clic = Record, 2e = Stop & Send)")
print("Appuyez sur un bouton physique pour tester (Ctrl+C pour quitter)...")

try:
    from gpiozero import Button  # type: ignore
    b1 = Button(5, pull_up=True, bounce_time=0.08)
    b2 = Button(6, pull_up=True, bounce_time=0.08)
    b3 = Button(13, pull_up=True, bounce_time=0.08)
    b4 = Button(26, pull_up=True, bounce_time=0.08)

    b1.when_pressed = lambda: print("\033[38;2;0;255;140m🟢 [CLIC DÉTECTÉ] Bouton 1 (GPIO 5) : Niveau 1 Fondamental (6e-9e DEF)\033[0m")
    b2.when_pressed = lambda: print("\033[38;2;25;90;255m🔵 [CLIC DÉTECTÉ] Bouton 2 (GPIO 6) : Niveau 2 Secondaire (10e-11e)\033[0m")
    b3.when_pressed = lambda: print("\033[38;2;255;115;0m🟠 [CLIC DÉTECTÉ] Bouton 3 (GPIO 13) : Niveau 3 Terminale (BAC)\033[0m")
    b4.when_pressed = lambda: print("\033[38;2;255;0;0m🔴 [CLIC DÉTECTÉ] Bouton 4 (GPIO 26) : Micro Toggle (Enregistrement/Envoi)\033[0m")

    while True:
        time.sleep(0.1)
except ImportError:
    print("⚠️ gpiozero n'est pas installé sur cette machine (pip install gpiozero).")
except KeyboardInterrupt:
    print("\n👋 Fin du test matériel.")
