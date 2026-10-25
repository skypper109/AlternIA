# 🚀 AlternIA Backend — API FastAPI & Services Pédagogiques

Le backend d'AlternIA est une suite d'API et de micro-services haute performance basée sur **FastAPI** et **SQLAlchemy**. Il orchestre les flux entre les boîtiers physiques (**Alta-Box**), les interfaces Kiosk HDMI, les applications mobiles des apprenants, les portails web d'administration scolaire et le moteur d'intelligence artificielle (**AI Engine**).

---

## 📋 Table des Matières

1. [Architecture & Technologies](#1-architecture--technologies)
2. [Cartographie des Routes & Endpoints API](#2-cartographie-des-routes--endpoints-api)
3. [Service OCR & Détection Curriculaire Malienne](#3-service-ocr--détection-curriculaire-malienne)
4. [Streaming Audio & Voix Ultra-Basse Latence](#4-streaming-audio--voix-ultra-basse-latence)
5. [Module Culturel : Grand-Mère Mah](#5-module-culturel--grand-mère-mah)
6. [WebSockets Temps Réel & Télémétrie](#6-websockets-temps-réel--télémétrie)
7. [Installation, Configuration & Lancement Local](#7-installation-configuration--lancement-local)
8. [Déploiement Serveur & Nginx](#8-déploiement-serveur--nginx)

---

## 1. Architecture & Technologies

```text
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                               ROUTES FASTAPI                                │
 │   /api/device   /api/chat   /api/culture   /api/podcasts   /api/apprenants  │
 └──────────────────────────────────────┬──────────────────────────────────────┘
                                        │
 ┌──────────────────────────────────────▼──────────────────────────────────────┐
 │                            COUCHE SERVICES MÉTIER                           │
 │   • ocr_service.py : Analyse hybride & validation programme scolaire        │
 │   • orchestrator_service.py : Pont direct avec AI Engine (RAG/Socratique)   │
 │   • culture_service.py : Contes, proverbes & sagesse (Grand-mère Mah)       │
 │   • boitier_service.py : Monitoring du parc, heartbeat & télémétrie         │
 │   • avatar_service.py / simli_service.py : Synchronisation labiale & vidéo  │
 └──────────────────────────────────────┬──────────────────────────────────────┘
                                        │
 ┌──────────────────────────────────────▼──────────────────────────────────────┐
 │                         PERSISTENCE & INFRASTRUCTURE                        │
 │   • Base de données SQLAlchemy (SQLite en Edge, MySQL / Postgres en Cloud)  │
 │   • Cache disque OCR (.ocr_cache) & fichiers audio générés                  │
 │   • Modèles de données Pydantic v2 avec validation stricte                  │
 └─────────────────────────────────────────────────────────────────────────────┘
```

- **Framework** : FastAPI (Python 3.11 / 3.12) avec gestion asynchrone native (`asyncio`).
- **ORM & Données** : SQLAlchemy avec support SQLite local (embarqué sur Pi 5) ou base de données relationnelle en cloud.
- **Sécurité & Accès** : Authentification JWT multi-rôles (Admin, Établissement, Parent, Apprenant, Boîtier matériel), CORS configuré pour les domaines officiels (`*.alterniamali.com`).

---

## 2. Cartographie des Routes & Endpoints API

### 📡 2.1. Boîtier Physique & Appareils (`/api/device`)
- `GET /api/device/status` : Statut opérationnel du boîtier (température CPU, mémoire, élèves connectés au Wi-Fi).
- `POST /api/device/stream-sentence` : Endpoint de streaming vocal TTS par phrase avec en-tête `X-Accel-Buffering: no` pour contourner le tampon Nginx et restituer la voix en **~2 secondes**.
- `POST /api/device/ocr/scan` : Réception d'une photo d'exercice scolaire prise par un smartphone ou la caméra du boîtier.
- `GET /api/device/history` : Historique des questions/réponses échangées sur le terminal.
- `POST /api/device/heartbeat` : Battement de cœur régulier (30s) transmis par le script de supervision du Raspberry Pi.

### 💬 2.2. Dialogue Pédagogique & Chat Socratique (`/api/chat`)
- `POST /api/chat/ask` : Question synchrone d'un élève avec injection du niveau (ex: `10eme`), série et matière.
- `GET /api/chat/stream` : Flux d'inférence en streaming SSE (*Server-Sent Events*) pour afficher le texte mot à mot en temps réel sur l'écran.
- `GET /api/chat/history/{student_id}` : Récupération du fil de conversation et des résolutions antérieures.

### 👵🏾 2.3. Patrimoine Culturel & Sagesse : Grand-Mère Mah (`/api/culture`)
- `GET /api/culture/story/daily` : Conte éducatif du jour enraciné dans les traditions maliennes (Bambara, Songhaï, Peul, Dogon, etc.).
- `GET /api/culture/proverbs` : Proverbes commentés et appliqués aux principes de persévérance et de méthode scientifique.
- `POST /api/culture/discuss` : Échange interactif bienveillant avec l'avatar culturel Grand-mère Mah.

### 🎙️ 2.4. Podcasts Pédagogiques (`/api/podcasts`)
- `GET /api/podcasts/feed` : Liste des leçons audio synthétisées par niveau et matière.
- `POST /api/podcasts/generate` : Synthèse à la demande d'un résumé de cours en capsule audio courte (3 à 5 minutes).

### 👥 2.5. Gestion Pédagogique & Suivi Scolaire
- `/api/apprenants` : Profils, niveaux de maîtrise curriculaire, historique d'apprentissage.
- `/api/etablissement` : Suivi global pour les directeurs et enseignants (taux de résolution, matières consultées).
- `/api/parent` : Supervision parentale des progrès de l'enfant.
- `/api/revision` & `/api/flashcards` : Fiches de révision mémorielles basées sur la répétition espacée (système de Leitner).
- `/api/defi-national` & `/api/duel` : Quiz et confrontations bienveillantes inter-écoles sur le programme officiel.

---

## 3. Service OCR & Détection Curriculaire Malienne

Le module [`src/services/ocr_service.py`](file:///Users/ibrahimsorydiallo/Desktop/OSC/AlternIA/backend/src/services/ocr_service.py) assure l'analyse automatique d'exercices photographiés :
1. **Validation & Filtrage** : Détection des documents invalides (tickets de caisse, photos floues ou hors-programme) pour éviter toute hallucination.
2. **Identification Curriculaire Robuste** : Système expert de mots-clés pondérés identifiant automatiquement le niveau scolaire (DEF 7e-9e ou Lycée 10e-12e) et la matière (Maths, Physique-Chimie, Biologie, Français).
3. **Pipeline Hybride** :
   - Moteur heuristique local ultra-rapide (<10 ms).
   - Inférence multimodale LLM Vision pour extraire le texte brut, les formules mathématiques et décomposer le problème en étapes socratiques progressives.

---

## 4. Streaming Audio & Voix Ultra-Basse Latence

Pour éliminer l'attente prolongée (~20 secondes) propre aux longs textes pédagogiques :
- La route `/api/device/stream-sentence` reçoit le texte fractionné phrase par phrase depuis l'orchestrateur.
- Chaque phrase est immédiatement transmise au moteur Neural TTS.
- Le flux audio MP3 est directement renvoyé avec les en-têtes :
  ```http
  Content-Type: audio/mpeg
  X-Accel-Buffering: no
  Cache-Control: no-cache
  ```
- Ceci permet au Raspberry Pi 5 de jouer la première phrase sur le haut-parleur en **moins de 2 secondes** pendant que le reste de la réponse se prépare.

---

## 5. WebSockets Temps Réel & Télémétrie

- `/ws/device` : Synchronisation des états matériels (écoute micro, réflexion IA, statut LED, volume sonore).
- `/ws/remote` : Écoute et émission d'événements de télécommande (navigation HDMI TV depuis les boutons physiques du boîtier).
- `/ws/session` : Flux duplex de session pédagogique interactif.

---

## 6. Installation, Configuration & Lancement Local

### Prérequis
- Python 3.11 ou 3.12
- Environnement virtuel recommandé (`venv`)

### 1. Installation des dépendances
```bash
cd AlternIA
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuration des Variables d'Environnement
Copiez le fichier `.env.example` en `.env` et ajustez vos paramètres :
```bash
cp .env.example .env
```
Paramètres essentiels :
```dotenv
DATABASE_URL=sqlite:///./backend_alternia.db
AI_ENGINE_URL=http://127.0.0.1:8001
CORS_ORIGINS=["https://device.alterniamali.com","https://admin.alterniamali.com","http://localhost:5173","http://localhost:4200"]
EDGE_TTS_VOICE=fr-FR-VivienneMultilingualNeural
```

### 3. Initialiser la Base de Données
```bash
python3 scripts/seed_db.py
```

### 4. Démarrer le Serveur
```bash
# Lancement direct via Uvicorn
uvicorn backend.src.main:app --host 0.0.0.0 --port 8000 --reload
```
Le serveur sera disponible sur `http://localhost:8000` et la documentation Swagger interactive sur `http://localhost:8000/docs`.

---

## 7. Déploiement Serveur & Nginx

En production sur instance AWS (`t3.xlarge` ou `g4dn.xlarge`) :
- Géré via le service systemd `alternia-backend.service`.
- Reverse-proxy Nginx avec configuration SSL Let's Encrypt :
  ```nginx
  location /api/ {
      proxy_pass http://127.0.0.1:8000;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_http_version 1.1;
      proxy_buffering off;
  }
  ```
