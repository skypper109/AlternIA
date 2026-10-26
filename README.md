# AlternIA — Écosystème Pédagogique Intelligent & Tuteur Vocal pour le Secondaire au Mali

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Kiosk](https://img.shields.io/badge/Frontend-Vite%20%7C%20HTML5%20%7C%20Vanilla%20JS-F7DF1E?style=flat-square&logo=javascript)](https://device.alterniamali.com)
[![Hardware](https://img.shields.io/badge/Hardware-Raspberry%20Pi%205%20(8GB)-C51A4A?style=flat-square&logo=raspberrypi)](https://www.raspberrypi.com/)
[![Audio I2S](https://img.shields.io/badge/Audio-I2S%20Duplex%20(MAX98357A%20%2B%20INMP441)-blue?style=flat-square)](https://github.com/)
[![RAG](https://img.shields.io/badge/RAG-Curriculum%20Malien%20%26%20Qdrant-orange?style=flat-square)](https://qdrant.tech/)
[![TTS](https://img.shields.io/badge/Audio-Sentence%20Streaming%20(~2s)-blueviolet?style=flat-square)](https://github.com/rany2/edge-tts)
[![STT](https://img.shields.io/badge/Vocal-Faster--Whisper-green?style=flat-square)](https://github.com/SYSTRAN/faster-whisper)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?style=flat-square&logo=python)](https://www.python.org/)

---

## 1. Présentation Générale et Vision du Projet

**AlternIA** est un écosystème d'assistance scolaire intelligent de nouvelle génération basé sur l'IA générative et l'Edge Computing, conçu spécifiquement pour accompagner les élèves du cycle fondamental et secondaire au **Mali** (DEF 7e-9e, 10ème Tronc Commun, 11ème Spécialités et 12ème Terminales).

Le projet résout les problématiques d'accès à un encadrement scolaire d'excellence dans les contextes à connectivité intermittente ou coûteuse :
- **Edge AI & Résilience Locale** : Le boîtier physique (**Alta-Box**, basé sur Raspberry Pi 5 8 Go) émet son propre point d'accès Wi-Fi autonome (**`Alta-box1`**), sert l'interface élève en local avec cache Nginx haute vitesse et peut exécuter l'inférence locale sans dépendance permanente à Internet.
- **Affichage Kiosk HDMI TV & Télécommande** : Affichage plein écran haute définition sur n'importe quel téléviseur ou vidéoprojecteur de classe, pilotable en direct par les boutons physiques du boîtier, le clavier ou la souris.
- **RAG Curriculaire Officiel du Mali** : Base de connaissances vectorisée indexant les manuels scolaires officiels (DEF et Lycée) pour ancrer les explications dans le programme national malien.
- **Méthode Socratique Adaptative** : Le tuteur ne divulgue jamais la réponse brute ; il guide l'élève pas à pas avec des questions progressives et bienveillantes.
- **Chaîne Audio I2S Duplex & Streaming par Phrase (~2s)** : DAC amplificateur **MAX98357A** et microphone numérique **INMP441** sur bus I2S synchrone, avec restitution vocale en streaming phrase par phrase et coupure immédiate au micro (**Barge-In**).
- **Module Culturel : Grand-Mère Mah** : Transmission de contes et proverbes maliens pour renforcer l'ancrage culturel et la confiance scolaire.
- **Analyse OCR Hybride** : Numérisation et décomposition d'exercices scolaires manuscrits ou imprimés.

---

## 2. Contexte Éducatif & Alignement Curriculaire Malien

AlternIA respecte fidèlement les programmes du ministère de l'Éducation nationale du Mali :

1. **Cycle Fondamental (Second Cycle - DEF)** :
   - 7ème, 8ème et 9ème Année (Diplôme d'Études Fondamentales).
   - Matières : Mathématiques, Sciences Physiques, Biologie, Français, Histoire-Géographie, Anglais.

2. **10ème Année (Tronc Commun)** :
   - 10ème Commune Générale (CG) et 10ème Commune Technique (CT).
   - Matières : Mathématiques, Physique-Chimie, Français, Anglais, Biologie, Histoire, Géographie.

3. **11ème Année (Spécialisation)** :
   - Séries : 11ème Sciences (`11ème SC`), Lettres & Littérature (`11ème LL`), Sciences Économiques (`11ème SECO`), Sciences & Technologies Industrielles (`11ème STI`).

4. **12ème Année (Terminale & Baccalauréat)** :
   - Séries : Terminale Sciences Exactes (`TSE`), Sciences Expérimentales (`TSExp`), Sciences Sociales (`TSS`), Sciences Économiques (`TSEco`), Lettres et Langues (`TLL`).

---

## 3. Architecture Globale de l'Écosystème

```text
+---------------------------------------------------------------------------------------------------+
|                                        CLIENTS D'ACCÈS                                            |
|  +------------------------+  +--------------------------+  +------------------+  +--------------+ |
|  | Écran TV HDMI Kiosk    |  | Portail Smartphone Wi-Fi |  | Application App  |  | Portail Web  | |
|  | Chromium 1080p plein   |  | Alta-box1 Captif         |  | Flutter Mobile   |  | Alta Admin   | |
|  | écran + Remote Control |  | device.alterniamali.com  |  | det-mobile       |  | Angular 18   | |
|  +------------------------+  +--------------------------+  +------------------+  +--------------+ |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                          BOÎTIER MATÉRIEL ALTA-BOX (RASPBERRY PI 5)                               |
|  - Hotspot Wi-Fi autonome (Alta-box1) & passerelle 10.42.0.1                                      |
|  - Contrôleur GPIO : 4 boutons physiques (cycles/niveaux + micro toggle PTT)                      |
|  - Signalétique lumineuse : LED tricolore RGB interactive (Turquoise, Bleu, Ambre, Rouge, Violet) |
|  - Audio I2S duplex partagé : DAC MAX98357A (HP 3W/5W) + Micro INMP441 (horloge partagée GPIO 18/19)|
|  - Cache audio local hors-ligne (audio_cache/) & Interruption vocale instantanée (Barge-In)       |
|  - Alimentation batterie : Pack 2x 18650 + module BMS Boost 5V 3-5A + Bouton Inox Ø16mm avec LED |
|  - Châssis Cyber Bloc V2 : Modélisation OpenSCAD et impression 3D bicolore                        |
+-------------------------------------------------+-------------------------------------------------+
                                                  | HTTP / WebSocket (/ws/device, /ws/remote)
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                        BACKEND FASTAPI                                            |
|  - Routes /api/device : Télémétrie, streaming TTS par phrase (X-Accel-Buffering: no), scan OCR    |
|  - Routes /api/chat : Dialogue socratique, streaming de jetons SSE (/api/chat/stream)             |
|  - Routes /api/culture : Sagesse et contes de Grand-Mère Mah                                      |
|  - Routes /api/podcasts : Résumés de cours audio générés par le programme malien                  |
|  - Service OCR Hybride : Détection curriculaire malienne robuste (DEF/Lycée) & décomposition      |
|  - Base de données SQLAlchemy (SQLite en Edge, MySQL/Postgres en production Cloud)                |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                    AI-ENGINE (ORCHESTRATEUR)                                      |
|                                                                                                   |
|  +------------------------------------+          +---------------------------------------------+  |
|  |        Moteur Pédagogique          |          |            RAG Curriculaire Malien          |  |
|  | - Classification d'intentions      |          | - Ingestion de manuels officiels (DEF/Lycée)|  |
|  | - Stratégies socratiques actives   |          | - Embeddings denses bilingues/multilingues  |  |
|  | - Autorisation rôle du tuteur      |          | - Base vectorielle Qdrant / Store Local     |  |
|  +------------------------------------+          +---------------------------------------------+  |
|                   |                                                     |                         |
|                   +--------------------------+--------------------------+                         |
|                                              |                                                    |
|                                              v                                                    |
|  +---------------------------------------------------------------------------------------------+  |
|  |                            Inférence LLM (Local Edge & Cloud)                               |  |
|  |             Local : Qwen 2.5 (1.5B / 3B GGUF) | Cloud : Groq Llama 3.3 70B / Gemini         |  |
|  +---------------------------------------------------------------------------------------------+  |
|                                              |                                                    |
|                                              v                                                    |
|  +------------------------------------+          +---------------------------------------------+  |
|  |         Mémoire Apprenant          |          |          Traitement Vocal (STT / TTS)       |  |
|  | - Historique multi-tours           |          | - STT : Faster-Whisper local / distant      |  |
|  | - Notions acquises et blocages     |          | - TTS : Neural Edge TTS (Vivienne)          |  |
|  | - Suivi de progression             |          | - Sentence Streaming Pipeline (~2s latence) |  |
|  +------------------------------------+          +---------------------------------------------+  |
+---------------------------------------------------------------------------------------------------+
```

---

## 4. Composants Principaux du Projet

### 4.1. Raspberry Pi 5 (`raspberry-pi/`)
- **Contrôleur Matériel (`hardware/buttons_audio_controller.py`)** : Gère l'ensemble des boutons, des LEDs et des périphériques audio via `gpiozero` et `libgpiod`.
- **Bus Audio I2S Duplex** : Le DAC **MAX98357A** et le microphone **INMP441** partagent les broches BCLK (GPIO 18) et LRCLK (GPIO 19), avec données sortantes sur DIN (GPIO 21) et entrantes sur SD (GPIO 20).
- **Affichage Kiosk HDMI TV (`kiosk/launch_kiosk.sh`)** : Lance Chromium en plein écran sans bordures sur `https://device.alterniamali.com`, pilotable en direct par les boutons du boîtier via WebSocket (`/ws/remote`).
- **Alimentation Autonome** : Pack 2 accus 18650, module BMS Boost 5V 3A-5A, bouton poussoir inox Ø16mm avec anneau LED.
- **Boîtier 3D Cyber Bloc V2 (`cad_3d/`)** : Pièces STL prêtes à imprimer en 3D et code OpenSCAD paramétrique.

### 4.2. Frontend du Dispositif (`device/frontend/`)
- Application web monopage ultra-rapide (Vite, HTML5, Vanilla JavaScript moderne, CSS modulaire).
- Visualiseur d'ondes audio interactif (**Vortex UI**), rendu mathématique et scientifique **KaTeX**.
- Synchronisation temps réel bidirectionnelle avec le boîtier physique (**`DeviceSyncService`**).

### 4.3. Backend FastAPI (`backend/`)
- Routes REST, WebSockets (`/ws/device`, `/ws/remote`) et streaming Server-Sent Events.
- **Streaming vocal non-bufferisé (`/api/device/stream-sentence`)** : Envoi de l'audio phrase par phrase avec `X-Accel-Buffering: no` pour démarrer l'écoute en ~2s.
- **Pipeline OCR Hybride (`ocr_service.py`)** : Identification automatique du niveau et de la matière selon le programme malien et décomposition socratique.
- **Module Grand-Mère Mah (`culture_service.py`)** : Contes et proverbes africains intégrés aux parcours d'apprentissage.

### 4.4. Moteur d'IA Pédagogique (`ai-engine/`)
- **Orchestrateur Pédagogique (`orchestration/orchestrator.py`)** : Détection des intentions, tolérance des questions méta-tuteur, filtrage bienveillant.
- **RAG Curriculaire (`rag/`)** : Ingestion et indexation sémantique des manuels officiels maliens de la 7ème année à la Terminale.
- **Sentence Streaming TTS (`tts/engine.py`)** : Synthèse vocale neuronale découpée par phrase avec gestion instantanée de l'interruption vocale (**Barge-In**).

### 4.5. Application Mobile Flutter (`det-mobile/`)
- Application mobile multiplateforme pour smartphones d'élèves (Salon holographique, cartes socratiques, lecteur de podcasts, scan d'exercices, connexion au boîtier Alta-Box).

---

## 5. Démarrage Rapide

### 5.1. Démarrer le Backend & Moteur IA (Local)

```bash
# 1. Cloner le projet et créer l'environnement virtuel
git clone https://github.com/skypper109/AlternIA.git
cd AlternIA
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Amorcer la base de données (programmes maliens, utilisateurs, boîtier démo)
python3 scripts/seed_db.py

# 3. Lancer le serveur (CPU ou GPU)
./start_cpu.sh
```

La documentation Swagger interactive sera disponible sur `http://localhost:8000/docs`.

### 5.2. Démarrer l'Interface Kiosk Dispositif

```bash
cd device/frontend
npm install
npm run dev
```
L'interface s'ouvre sur `http://localhost:5173`.

### 5.3. Déployer sur Raspberry Pi 5

Sur le Raspberry Pi 5 sous Debian 12 Bookworm 64-bit :
```bash
cd ~/AlternIA/raspberry-pi
sudo ./setup_pi5_hotspot.sh
sudo ./hardware/setup_max98357a_audio.sh
sudo ./scripts/setup_hdmi_kiosk.sh
```

---

## 6. Structure du Répertoire

```text
AlternIA/
├── README.md                          # Documentation générale du projet
├── requirements.txt                   # Dépendances Python globales
├── start_cpu.sh / start_gpu.sh        # Scripts de démarrage rapide
├── run_alternia.py                    # Orchestrateur de processus
│
├── raspberry-pi/                      # Infrastructure Boîtier Alta-Box (Raspberry Pi 5)
│   ├── hardware/                      # Contrôleur GPIO, scripts I2S, guide de câblage
│   ├── kiosk/                         # Script de lancement Chromium Kiosk HDMI TV
│   ├── cad_3d/                        # Modélisation 3D OpenSCAD & fichiers STL Cyber Bloc V2
│   ├── scripts/                       # Scripts de configuration HDMI et tests vocaux
│   ├── nginx/                         # Configuration du reverse-proxy et cache Edge local
│   └── systemd/                       # Déclarations des démons systemd auto-start
│
├── device/                            # Dispositif interactif
│   ├── frontend/                      # Application web Kiosk TV & mobile (Vite/HTML5/JS/KaTeX)
│   └── hardware/                      # Couche d'abstraction matérielle (HAL)
│
├── backend/                           # Serveur API FastAPI
│   ├── src/
│   │   ├── routes/                    # Routeurs (device, chat, culture, podcasts, auth...)
│   │   ├── services/                  # OCR hybride, culture, boîtier, analytique...
│   │   ├── models/                    # Modèles Pydantic v2
│   │   └── db/                        # Modèles SQLAlchemy
│   └── tests/                         # Tests d'intégration API
│
├── ai-engine/                         # Cerveau Pédagogique & RAG
│   ├── src/alternia/
│   │   ├── orchestration/             # Orchestrateur central et classification d'intentions
│   │   ├── pedagogical/               # Stratégies socratiques et scope curriculaire
│   │   ├── rag/                       # Chunker, embeddings et indexation des manuels
│   │   ├── tts/                       # Sentence streaming TTS et gestion du barge-in
│   │   ├── stt/                       # Transcription vocale Faster-Whisper
│   │   └── llm/                       # Inférence Qwen 2.5 local GGUF et APIs Cloud
│   └── tests/                         # Tests unitaires du moteur pédagogique
│
├── culturelens_ai/                    # Vision par ordinateur pour les monuments maliens
├── knowledge-base/                    # Manuels officiels du programme malien (DEF à Terminale)
├── scripts/                           # Synchronisation Flutter/Backend, seed_db, utilitaires
└── aws-deployment/                    # Déploiement Cloud AWS EC2 (t3.xlarge / g4dn.xlarge GPU)
```

---

## 7. Licence et Contribution

Le projet **AlternIA** est développé pour promouvoir l'égalité des chances et la réussite scolaire au Mali et en Afrique grâce à une intelligence artificielle éducative éthique, souveraine et accessible hors-ligne.
