"""
Configuration matérielle et réseau pour le client AlternIA Box sur Raspberry Pi 3.
Ce fichier centralise l'affectation des broches GPIO, la configuration audio ALSA,
l'URL du serveur AlternIA et les paramètres par défaut de l'élève (classe & école).
"""

import os
from pathlib import Path

# Répertoire racine du projet client RPi
BASE_DIR = Path(__file__).resolve().parent

# ==============================================================================
# 1. CONNEXION RÉSEAU AU SERVEUR ALTERNIA
# ==============================================================================
# Adresse du serveur AlternIA (Backend FastAPI / AI Engine)
# Peut être un PC local (ex: http://192.168.1.50:8000), le Pi lui-même (http://localhost:8000),
# ou un serveur Cloud / Colab / Tunnel ngrok.
SERVER_URL = os.getenv("ALTERNIA_SERVER_URL", "http://127.0.0.1:8000")

# Timeout des requêtes HTTP vers le serveur (secondes)
REQUEST_TIMEOUT = 30

# ==============================================================================
# 2. PROFIL PAR DÉFAUT DE L'ÉLÈVE (CYCLE, CLASSE & ÉTABLISSEMENT)
# ==============================================================================
# Cycle actif : 'fondamental' ou 'lycee'
DEFAULT_CYCLE = os.getenv("ALTERNIA_DEFAULT_CYCLE", "fondamental")

# Classe initiale :
# Fondamental : '6eme', '7eme', '8eme', '9eme' (DEF)
# Lycée       : '10eme', '11eme', '12eme' (Terminale)
DEFAULT_CLASS = os.getenv("ALTERNIA_DEFAULT_CLASS", "6eme")

# Nom de l'établissement scolaire
DEFAULT_SCHOOL = os.getenv("ALTERNIA_DEFAULT_SCHOOL", "École Fondamentale Mamadou Konaté (Bamako)")

# Identifiant unique de l'appareil
DEVICE_ID = os.getenv("ALTERNIA_DEVICE_ID", "RPI3-ALT-BOX-01")

# ==============================================================================
# 3. ATTRIBUTION DES BROCHES GPIO (NUMÉROTATION BCM - RASPBERRY PI 3)
# ==============================================================================
# ATTENTION : Les numéros correspondent au schéma BCM (Broadcom), pas aux numéros physiques.
# Tous les boutons utilisent les résistances de tirage internes PULL-UP (état bas = appuyé).

# Mode standard 4 boutons physiques :
# - Bouton 1 : Classe 1 (ou 6ème en fondamental / 10ème en lycée)
# - Bouton 2 : Classe 2 (ou 7ème/8ème en fondamental / 11ème en lycée)
# - Bouton 3 : Classe 3 (ou 9ème DEF en fondamental / 12ème Terminale en lycée)
# - Bouton 4 : Micro Push-To-Talk (maintenir ou cliquer pour parler)
PIN_BTN_1 = 17       # Broche physique 11 -> GPIO17
PIN_BTN_2 = 27       # Broche physique 13 -> GPIO27
PIN_BTN_3 = 22       # Broche physique 15 -> GPIO22
PIN_BTN_MIC = 23     # Broche physique 16 -> GPIO23 (Micro)

# Bouton optionnel de bascule de cycle (Fondamental <-> Lycée)
PIN_BTN_CYCLE = 12   # Broche physique 32 -> GPIO12 (Appui = change de cycle)

# Bouton extinction propre du Raspberry Pi (Appui 3s) pour protéger la carte SD
PIN_SAFE_SHUTDOWN = 26  # Broche physique 37 -> GPIO26

# Voyants Lumineux LEDs (sorties GPIO)
PIN_LED_GREEN = 24   # Broche physique 18 -> GPIO24 (Prêt / Veille)
PIN_LED_BLUE = 25    # Broche physique 22 -> GPIO25 (Écoute Micro / Enregistrement)
PIN_LED_RED = 18     # Broche physique 12 -> GPIO18 (Erreur / Extinction)

# ==============================================================================
# 4. CONFIGURATION AUDIO (MICROPHONE USB & HAUT-PARLEUR)
# ==============================================================================
# Paramètres d'enregistrement audio ALSA
AUDIO_FORMAT = "int16"
AUDIO_CHANNELS = 1          # Mono pour la voix
AUDIO_RATE = 16000          # 16 kHz (standard Whisper / STT)
AUDIO_CHUNK = 1024          # Taille de buffer
AUDIO_MAX_RECORD_SEC = 20   # Durée maximale d'un enregistrement (secondes)
AUDIO_SILENCE_THRESHOLD = 500  # Seuil de détection du silence
AUDIO_MIN_DURATION_SEC = 0.5   # En dessous de 0.5s, le son est ignoré

# Périphérique ALSA personnalisé (si None, utilise le périphérique par défaut)
ALSA_INPUT_DEVICE = os.getenv("ALTERNIA_ALSA_INPUT", None)
ALSA_OUTPUT_DEVICE = os.getenv("ALTERNIA_ALSA_OUTPUT", None)

# Fichier temporaire pour l'enregistrement vocal
TEMP_WAV_PATH = "/tmp/alternia_user_query.wav"
TEMP_TTS_PATH = "/tmp/alternia_tts_response.mp3"

# ==============================================================================
# 5. LABELS ET ANNONCES VOCALES OFFICIELLES DU MALI
# ==============================================================================
CLASS_NAMES = {
    "6eme": "6ème Année (Fondamental 1er Cycle)",
    "7eme": "7ème Année (Fondamental 2ème Cycle)",
    "8eme": "8ème Année (Fondamental 2ème Cycle)",
    "9eme": "9ème Année (Examen National DEF)",
    "10eme": "10ème Année (Tronc Commun Lycée)",
    "11eme": "11ème Année (Sciences & Lettres)",
    "12eme": "12ème Année (Terminale Baccalauréat)",
}

CLASS_SPEECH_ANNOUNCEMENTS = {
    "6eme": "Sixième année fondamentale activée.",
    "7eme": "Septième année fondamentale activée.",
    "8eme": "Huitième année fondamentale activée.",
    "9eme": "Neuvième année, préparation au DEF activée.",
    "10eme": "Dixième année tronc commun activée.",
    "11eme": "Onzième année du lycée activée.",
    "12eme": "Classe de Terminale, préparation au baccalauréat activée.",
}

# Mapping des boutons en fonction du cycle actif :
CYCLE_BUTTON_MAPPING = {
    "fondamental": {
        1: "6eme",
        2: "8eme",
        3: "9eme",  # Examen DEF
    },
    "lycee": {
        1: "10eme",
        2: "11eme",
        3: "12eme", # Terminale BAC
    }
}
