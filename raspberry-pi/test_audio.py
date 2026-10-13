#!/usr/bin/env python3
"""
Outil de Diagnostic et de Test Audio pour Raspberry Pi 3.
Vérifie la détection du microphone USB, la sortie haut-parleur (Jack ou HDMI/USB)
et effectue un enregistrement/lecture de test.
"""

import os
import subprocess
import time

TEST_WAV = "/tmp/alternia_test_audio.wav"


def check_audio_devices():
    print("\n🎤 1. Périphériques de Capture (Microphones détectés par ALSA) :")
    try:
        res = subprocess.run(["arecord", "-l"], capture_output=True, text=True)
        print(res.stdout if res.stdout else "   Aucun microphone détecté !")
    except FileNotFoundError:
        print("   ❌ 'arecord' introuvable. Installez : sudo apt install alsa-utils")

    print("\n🔊 2. Périphériques de Lecture (Haut-parleurs détectés par ALSA) :")
    try:
        res = subprocess.run(["aplay", "-l"], capture_output=True, text=True)
        print(res.stdout if res.stdout else "   Aucune sortie audio détectée !")
    except FileNotFoundError:
        print("   ❌ 'aplay' introuvable. Installez : sudo apt install alsa-utils")


def record_and_playback():
    print("\n🎙️ 3. Test d'enregistrement vocal (3 secondes)...")
    print("   👉 Parlez fort dans le microphone maintenant : « Bonjour AlternIA Mali ! »")
    time.sleep(0.5)

    try:
        # Enregistrement
        cmd_record = [
            "arecord",
            "-f", "S16_LE",
            "-r", "16000",
            "-c", "1",
            "-d", "3",
            "-q",
            TEST_WAV,
        ]
        subprocess.run(cmd_record, check=True)
        print("   ✅ Enregistrement terminé !")

        size = os.path.getsize(TEST_WAV) if os.path.exists(TEST_WAV) else 0
        print(f"   Taille du fichier capté : {size} octets")

        if size > 1000:
            print("\n🔊 4. Lecture du son enregistré sur les haut-parleurs...")
            cmd_play = ["aplay", "-q", TEST_WAV]
            subprocess.run(cmd_play, check=True)
            print("   ✅ Lecture terminée avec succès !")
        else:
            print("   ⚠️ Le fichier audio est vide ou inaudible. Vérifiez le branchement du micro.")

    except Exception as exc:
        print(f"   ❌ Erreur pendant le test audio : {exc}")
    finally:
        if os.path.exists(TEST_WAV):
            try:
                os.remove(TEST_WAV)
            except Exception:
                pass


def main():
    print("=" * 65)
    print("  🇲🇱  DIAGNOSTIC AUDIO (ALSA) — ALTERNIA BOX (RASPBERRY PI 3)  🇲🇱")
    print("=" * 65)
    check_audio_devices()
    record_and_playback()
    print("\n💡 Astuce : Si le micro est trop faible, réglez le gain avec : alsamixer")


if __name__ == "__main__":
    main()
