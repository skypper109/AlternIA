#!/usr/bin/env python3
"""
══════════════════════════════════════════════════════════════════════════════
Script de Test Matériel : 4 Boutons + Microphone + Haut-Parleur
══════════════════════════════════════════════════════════════════════════════
Usage :
  python3 test_hardware.py
"""

import sys
import time
import subprocess
from pathlib import Path

print("=" * 70)
print("   🇲🇱  TEST DU MATÉRIEL ALTERNIA BOX (Raspberry Pi 5)  🇲🇱")
print("=" * 70)

# 1. Test du Haut-Parleur
print("\n[1/3] Test du Haut-Parleur / Audio Output...")
try:
    print("🔊 Émission d'un bip sonore de test (2 secondes)...")
    subprocess.run(["speaker-test", "-t", "sine", "-f", "440", "-l", "1"], check=False)
    print("✅ Si vous avez entendu un son, le haut-parleur fonctionne correctement.")
except Exception as e:
    print(f"⚠️ Erreur test haut-parleur : {e}")

# 2. Test du Microphone
print("\n[2/3] Test du Microphone...")
test_wav = Path("/tmp/test_mic.wav")
try:
    print("🎙️ Enregistrement de 3 secondes dans le micro (Parlez fort)...")
    subprocess.run([
        "arecord", "-D", "default", "-f", "S16_LE", "-r", "16000", "-d", "3", str(test_wav)
    ], check=True)
    print("🔊 Réécoute de l'enregistrement...")
    subprocess.run(["aplay", str(test_wav)], check=True)
    print("✅ Si vous avez entendu votre voix, le microphone fonctionne parfaitement.")
except Exception as e:
    print(f"⚠️ Erreur test microphone : {e} (Assurez-vous qu'un micro USB ou Jack est branché)")

# 3. Test des 4 Boutons GPIO
print("\n[3/3] Test des 4 Boutons GPIO (GPIO 5, 6, 13, 26)...")
print("Appuyez sur n'importe quel bouton. Appuyez sur Ctrl+C pour quitter.")

try:
    from gpiozero import Button  # type: ignore
    b1 = Button(5, pull_up=True)
    b2 = Button(6, pull_up=True)
    b3 = Button(13, pull_up=True)
    b4 = Button(26, pull_up=True)

    b1.when_pressed = lambda: print("🟢 [CLIC] Bouton 1 (GPIO 5) : Micro Push-To-Talk détecté !")
    b2.when_pressed = lambda: print("🟡 [CLIC] Bouton 2 (GPIO 6) : Répéter Audio détecté !")
    b3.when_pressed = lambda: print("🔵 [CLIC] Bouton 3 (GPIO 13) : Changer Classe détecté !")
    b4.when_pressed = lambda: print("🟣 [CLIC] Bouton 4 (GPIO 26) : Défi Quizz détecté !")

    while True:
        time.sleep(0.1)
except ImportError:
    print("⚠️ gpiozero n'est pas encore installé (pip install gpiozero).")
except KeyboardInterrupt:
    print("\nFin du test.")
