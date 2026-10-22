#!/usr/bin/env python3
"""
Test de Présentation Vocale AlternIA (Raspberry Pi 5 -> Serveur AWS GPU)
Télécharge la voix du tuteur IA et la diffuse dans le haut-parleur I2S.
"""

import os
import sys
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path

# URL du serveur (domaine officiel ou IP directe)
SERVER_URL = os.environ.get("ALTERNIA_API_URL", "https://api.alterniamali.com").rstrip("/")
AUDIO_CARD = "plughw:2,0"

TEXTE_PRESENTATION = (
    "Bonjour les enfants ! Je suis AlternIA, votre tuteur pédagogique intelligent. "
    "Je suis propulsé par un modèle Qwen embarqué sur votre nouveau serveur accéléré par carte graphique. "
    "Le son de votre haut-parleur fonctionne à merveille. Je suis prêt à vous accompagner dans toutes vos leçons !"
)

def main():
    server = sys.argv[1] if len(sys.argv) > 1 else SERVER_URL
    print("=" * 72)
    print("   🇲🇱  TEST DE PRÉSENTATION VOCALE ALTERNIA (Raspberry Pi 5)  🇲🇱")
    print("=" * 72)
    print(f"🌐 Connexion au serveur : {server}")
    print(f"🔊 Périphérique Audio   : {AUDIO_CARD} (MAX98357A I2S)\n")

    # 1. Tester la connectivité avec le serveur
    print("⏳ Vérification de la liaison avec le serveur...")
    try:
        req = urllib.request.Request(f"{server}/api/device/info", headers={"User-Agent": "AlternIA-Box"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            print("✅ Serveur AlternIA en ligne et réactif !")
    except Exception as e:
        print(f"ℹ️ Note connexion ({e}). Tentative directe sur l'endpoint vocal...")

    # 2. Synthèse vocale de présentation
    out_file = Path("/tmp/alternia_presentation.mp3")
    encoded_text = urllib.parse.quote(TEXTE_PRESENTATION)
    tts_url = f"{server}/api/tts?text={encoded_text}&voice=vivienne"

    print("🎙️ Génération de la présentation vocale en cours...")
    try:
        req = urllib.request.Request(tts_url, headers={"User-Agent": "AlternIA-Box"})
        with urllib.request.urlopen(req, timeout=15) as resp, open(out_file, "wb") as f:
            f.write(resp.read())
        print(f"✅ Audio téléchargé ({out_file.stat().st_size} octets)")
    except Exception as e:
        print(f"❌ Échec téléchargement audio : {e}")
        return

    # 3. Lecture audio sur le haut-parleur (avec boost numérique +12dB et 48kHz)
    print("📢 Diffusion dans le haut-parleur noir...")
    boosted_wav = Path("/tmp/alternia_presentation_boosted.wav")
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", str(out_file),
            "-af", "volume=12dB",
            "-ar", "48000",
            str(boosted_wav)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        target = boosted_wav if boosted_wav.exists() else out_file
        res = subprocess.run(["aplay", "-D", AUDIO_CARD, "-q", str(target)], check=False)
        if res.returncode == 0:
            print("\n🎉 Présentation terminée avec succès !")
            return
    except Exception:
        pass

if __name__ == "__main__":
    main()
