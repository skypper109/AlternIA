# AlternIA - Dispositif Pédagogique Intelligent et Tuteur Vocal pour le Secondaire au Mali

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Angular](https://img.shields.io/badge/Frontend-Angular%2018-DD0031?style=flat-square&logo=angular)](https://angular.dev/)
[![LLM Local](https://img.shields.io/badge/Edge%20AI-Qwen2.5%20GGUF-412991?style=flat-square)](https://huggingface.co/Qwen)
[![RAG](https://img.shields.io/badge/RAG-Local%20%26%20Qdrant-orange?style=flat-square)](https://qdrant.tech/)
[![TTS](https://img.shields.io/badge/Audio-Neural%20Edge%20TTS-blue?style=flat-square)](https://github.com/rany2/edge-tts)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?style=flat-square&logo=python)](https://www.python.org/)

---

## 1. Présentation générale et vision du projet

**AlternIA** est un écosystème d'assistance pédagogique intelligent basé sur l'intelligence artificielle, spécialement conçu pour accompagner les élèves du cycle secondaire au Mali (10ème, 11ème et 12ème Année / Terminale).

Le projet répond aux défis structurels d'accès à un encadrement scolaire personnalisé et aux ressources éducatives dans les contextes à connectivité limitée ou instable :
- **Edge AI / Local-First** : Le moteur d'inférence linguistique (LLM) s'exécute localement sur le boîtier physique (AlternIA Box) sans dépendance obligatoire à Internet.
- **RAG Curriculaire Malien** : La base de connaissances des manuels et programmes officiels du Mali est vectorisée et interrogée localement via un pipeline RAG (*Retrieval-Augmented Generation*).
- **Pédagogie Adaptative & Socratique** : Le système adapte son niveau, ses explications et son vocabulaire à la classe, à la série et à la progression réelle de chaque élève sans donner directement les réponses aux exercices.
- **Interface Vocale Haute Définition** : Synthèse vocale neuronale fluide avec prononciation exacte des expressions mathématiques et scientifiques.
- **Portail d'Administration et Suivi Multi-Rôles** : Une application web moderne (*Alta*) et des APIs complètes pour les établissements scolaires, les enseignants et les parents d'élèves.

---

## 2. Contexte éducatif et alignement curriculaire malien

AlternIA intègre l'intégralité de la structure curriculaire du ministère de l'Éducation nationale du Mali.

### 2.1. Niveaux et filières supportés

1. **10ème Année (Tronc Commun)**
   - **Filières** : 10ème Commune Générale (CG), 10ème Commune Technique (CT).
   - **Matières** : Mathématiques, Physique-Chimie, Français, Anglais, Biologie, Histoire, Géographie.

2. **11ème Année (Spécialisation)**
   - **Séries** :
     - `11ème SC` : 11ème Sciences
     - `11ème LL` : 11ème Lettres et Littérature
     - `11ème SECO` : 11ème Sciences Économiques
     - `11ème STI` : 11ème Sciences et Technologies Industrielles
   - **Matières** : Mathématiques, Sciences Physiques, Chimie, Français, Philosophie, Anglais, Biologie, Géologie, Histoire, Géographie.

3. **12ème Année (Terminale & Baccalauréat)**
   - **Séries** :
     - `TSE` : Terminale Sciences Exactes (priorité Mathématiques, Physique-Chimie)
     - `TSExp` : Terminale Sciences Expérimentales (Sciences Naturelles, Physique-Chimie, Mathématiques)
     - `TSS` : Terminale Sciences Sociales (Histoire, Géographie, Philosophie, Français, Mathématiques appliquées)
     - `TSEco` : Terminale Sciences Économiques (Économie, Mathématiques appliquées, Gestion)
     - `TLL` : Terminale Lettres et Langues (Littérature, Philosophie, Langues vivantes)

---

## 3. Architecture globale de l'écosystème

```
+-----------------------------------------------------------------------------------------+
|                                    CLIENTS D'ACCÈS                                      |
|  +-------------------------------+  +--------------------------+  +------------------+  |
|  | Interface Web Alta (Angular)  |  | Application Mobile       |  | CLI Interactive  |  |
|  | Portails Directeurs / Parents |  | Flutter / Android        |  | Terminal Local   |  |
|  +-------------------------------+  +--------------------------+  +------------------+  |
+---------------------------------------------+-------------------------------------------+
                                              |
                                              v
+-----------------------------------------------------------------------------------------+
|                                  BACKEND FASTAPI                                        |
|  - Authentification multi-rôles (Admin École, Enseignants, Parents)                     |
|  - DTOs Pydantic avec support double camelCase / snake_case                             |
|  - Base de données SQLAlchemy (SQLite / MySQL)                                          |
|  - Gestion du parc de boîtiers physiques AlternIA Box                                   |
|  - Suivi des apprenants, statistiques d'apprentissage & alertes                         |
|  - Studio de voix & d'avatars pédagogiques                                              |
|  - Streaming SSE Token-par-Token (/api/chat/stream)                                     |
+---------------------------------------------+-------------------------------------------+
                                              |
                                              v
+-----------------------------------------------------------------------------------------+
|                              AI-ENGINE (ORCHESTRATEUR)                                  |
|                                                                                         |
|  +------------------------------------+      +---------------------------------------+  |
|  |        Moteur Pédagogique          |      |            RAG Contextuel             |  |
|  | - Détection d'intention             |      | - Ingestion et chunking de PDF        |  |
|  | - Stratégies socratiques & cours   |      | - Embeddings denses BGE Multilingues  |  |
|  | - Prompt engineering adaptatif     |      | - Base vectorielle locale / Qdrant    |  |
|  +------------------------------------+      +---------------------------------------+  |
|                   |                                              |                      |
|                   +----------------------+-----------------------+                      |
|                                          |                                              |
|                                          v                                              |
|  +-----------------------------------------------------------------------------------+  |
|  |                      LLM Local (GGUF via llama-cpp-python)                        |  |
|  |             Inférence locale Qwen 2.5 (1.5B / 3B Instruct quantifié Q4)           |  |
|  +-----------------------------------------------------------------------------------+  |
|                                          |                                              |
|                                          v                                              |
|  +------------------------------------+      +---------------------------------------+  |
|  |       Mémoire Apprenant            |      |         Synthèse Vocale (TTS)         |  |
|  | - Historique conversationnel       |      | - Voix neuronales HD (Vivienne, Rémy) |  |
|  | - Profil de maîtrise des notions   |      | - Traduction phonétique des formules  |  |
|  | - Détection des points de blocage  |      | - Mode de repli hors-ligne (say/espeak|  |
|  +------------------------------------+      +---------------------------------------+  |
+-----------------------------------------------------------------------------------------+
```

---

## 4. Composants principaux

### 4.1. Moteur d'Intelligence Artificielle (`ai-engine`)
- **LLM Local (`llm/local_client.py`)** : Inférence haute performance avec quantification GGUF (`Qwen2.5-3B-Instruct` ou `Qwen2.5-1.5B-Instruct` pour Raspberry Pi / Edge), support d'accélération matérielle Metal (macOS), CUDA (Nvidia) et CPU multi-thread.
- **RAG & Chunking Pédagogique (`rag/`, `ingestion/`)** : Découpage sémantique préservant la hiérarchie didactique (chapitre, leçon, notion, exercices), embeddings denses BAAI/bge, et recherche hybride filtrée par classe et matière.
- **Moteur Pédagogique & Stratégies (`pedagogical/`)** : Détection d'intentions et application de stratégies socratiques (guidage étape par étape sans donner directement la solution).
- **TTS Haute Définition (`tts/`)** : Voix neuronales (`Vivienne`, `Remy`), nettoyage phonétique avancé des formules mathématiques (`x² + 2x = 0` $\rightarrow$ *"x au carré plus deux x égal zéro"*), gestion des flux audio et mode hors-ligne.
- **Mémoire & Progression (`learner/`, `conversation/`)** : Suivi des notions maîtrisées et à revoir, persistance de session et contextualisation des requêtes.

### 4.2. Serveur Backend FastAPI (`backend`)
- **API REST & Streaming SSE** : Endpoints modulaires pour le dialogue pédagogique, la gestion des sessions et le diagnostic système.
- **Authentification & Gestion des Profils (`services/auth_service.py`, `models/auth.py`)** : Inscription et connexion pour directeurs d'établissement (`admin_ecole`), enseignants et parents, hachage sécurisé des mots de passe, gestion du statut actif/inactif.
- **Gestion des Boîtiers (`services/boitier_service.py`)** : Télémétrie en temps réel (batterie, stockage, statut Wi-Fi, dernière synchronisation, configuration réseau).
- **Analytique & Alertes (`services/analytics_service.py`, `services/alerte_service.py`)** : Détection des décrochages et alertes pédagogiques, calcul des KPIs d'apprentissage en temps réel.
- **Studio Vocal & Avatars (`services/avatar_service.py`)** : Gestion des avatars d'enseignants virtuels et génération d'échantillons audio en direct.
- **Persistance & Base de Données (`db/`)** : Modèles SQLAlchemy (`Utilisateur`, `Etablissement`, `Boitier`, `Apprenant`, `Alerte`, `SessionApprentissage`), compatible SQLite et MySQL/MariaDB (`init_alta_db.sql`).

### 4.3. Portail Web Client (`alta`)
- **Framework & Stack** : Développé en **Angular 18** (Standalone components, Signals, Reactive Forms).
- **Design System "Liquid Glass"** : Interface moderne, esthétique glassmorphism sombre, micro-interactions, responsive design et tableaux de bord immersifs.
- **Espaces Dédiés** :
  - *Espace Établissement* : Vue d'ensemble du parc de boîtiers, statistiques des classes, gestion des comptes utilisateurs, résolution des alertes.
  - *Espace Parent* : Suivi individuel des enfants, temps d'apprentissage quotidien, notions acquises et configuration du boîtier familial.
  - *Studio des Avatars* : Création, prévisualisation et test vocal des avatars pédagogiques.

---

## 5. Spécifications des Endpoints API

### Authentification & Profils (`/api/auth`)
| Méthode | Route | Description |
|---|---|---|
| `POST` | `/api/auth/connexion` | Connexion utilisateur (Directeur, Enseignant, Parent) |
| `POST` | `/api/auth/inscription-etablissement` | Inscription d'un établissement et création de l'administrateur |
| `POST` | `/api/auth/inscription-parent` | Inscription d'un parent et association du boîtier |
| `GET` | `/api/auth/me` | Récupération du profil utilisateur connecté |
| `PUT` | `/api/auth/profile` | Mise à jour du profil et mot de passe |
| `GET` | `/api/auth/users` | Liste des utilisateurs enregistrés (Admin) |
| `POST` | `/api/auth/users` | Création d'un utilisateur par l'administrateur |
| `POST` | `/api/auth/users/{id}/toggle-status` | Activation / désactivation d'un compte |

### Dialogue & Pédagogie (`/api/chat`)
| Méthode | Route | Description |
|---|---|---|
| `POST` | `/api/chat` (ou `/api/ask`) | Question synchrone avec réponse complète et métadonnées RAG |
| `POST` | `/api/chat/stream` | Flux de tokens en temps réel via Server-Sent Events (SSE) |
| `POST` | `/api/session/reset` | Réinitialisation du contexte conversationnel |

### Boîtiers & Télémétrie (`/api/boitiers`, `/api/device`)
| Méthode | Route | Description |
|---|---|---|
| `GET` | `/api/boitiers` | Liste de tous les boîtiers physiques déployés |
| `GET` | `/api/boitiers/{id}` | Détails matériels, batterie, stockage et statut |
| `POST` | `/api/boitiers/{id}/sync` | Déclenchement d'une synchronisation des données |
| `POST` | `/api/boitiers/{id}/wifi` | Configuration des paramètres Wi-Fi du boîtier |
| `GET` | `/api/device/info` | Diagnostic matériel du boîtier local |

### Apprenants, Analytique & Alertes
| Méthode | Route | Description |
|---|---|---|
| `GET` | `/api/apprenants` | Liste des élèves avec niveau de maîtrise et temps passé |
| `GET` | `/api/apprenants/{id}` | Profil détaillé d'un apprenant |
| `GET` | `/api/insights` | KPIs temps réel, notions critiques et points de blocage |
| `GET` | `/api/statistiques` | Répartition des matières et temps d'apprentissage |
| `GET` | `/api/alertes` | Liste des alertes pédagogiques |
| `PUT` | `/api/alertes/{id}/resoudre` | Résolution d'une alerte |

### Avatars & Synthèse Vocale (`/api/avatars`, `/api/tts`)
| Méthode | Route | Description |
|---|---|---|
| `GET` | `/api/avatars` | Liste des avatars pédagogiques configurés |
| `POST` | `/api/avatars` | Création d'un nouvel avatar personnalisé |
| `POST` | `/api/avatars/test-audio` | Synthèse vocale à la volée d'une phrase de test |

---

## 6. Installation et Déploiement

### 6.1. Prérequis
- **OS** : macOS (Apple Silicon / Intel), Linux (Ubuntu, Debian, Raspberry Pi OS 64-bit).
- **Python** : Version 3.11 ou 3.12.
- **Node.js** : Version 18+ (pour le portail Angular `alta`).
- **Outils audio** : `afplay` (inclus sur macOS) ou `mpv` / `ffplay` / `alsa` (Linux).

### 6.2. Cloner le projet et configurer l'environnement Python

```bash
git clone https://github.com/skypper109/AlternIA.git
cd AlternIA

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

### 6.3. Télécharger le modèle LLM local (GGUF)

```bash
mkdir -p ai-engine/models/llm

# Modèle Qwen 2.5 3B Instruct (recommandé pour Mac/PC) :
curl -L -o ai-engine/models/llm/qwen2.5-3b-instruct-q4_k_m.gguf \
  https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf

# Ou modèle ultra-léger 1.5B (recommandé pour Raspberry Pi / Edge) :
curl -L -o ai-engine/models/llm/qwen2.5-1.5b-instruct-q4_k_m.gguf \
  https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf
```

### 6.4. Indexer les manuels scolaires (RAG)

```bash
export PYTHONPATH="ai-engine/src:backend/src:$PYTHONPATH"
python ai-engine/src/alternia/rag/indexer.py
```

### 6.5. Démarrer le Backend FastAPI

```bash
export PYTHONPATH="ai-engine/src:backend/src:$PYTHONPATH"
uvicorn backend.src.main:app --host 0.0.0.0 --port 8000 --reload
```
> Accédez à la documentation Swagger interactive sur : `http://localhost:8000/docs`.

### 6.6. Démarrer le Portail Web Angular (Alta)

```bash
cd alta
npm install
npm start
```
> Le portail est accessible à l'adresse : `http://localhost:4200`.

### 6.7. Utiliser le Mode Terminal Interactif (CLI)

```bash
export PYTHONPATH="ai-engine/src:backend/src:$PYTHONPATH"
python ai-engine/src/alternia/cli/chat.py
```

---

## 7. Commandes du Terminal Interactif (CLI)

- `/classe 10eme` | `/classe 11eme` | `/classe 12eme` : Change la classe active et recalibre le RAG.
- `/matiere <nom>` : Bascule sur une matière (`mathematiques`, `physique`, `chimie`, `francais`, etc.).
- `/voix` : Affiche les voix disponibles et la voix courante.
- `/voix vivienne` | `/voix remy` : Sélectionne une voix neuronale haute fidélité.
- `/voix system` : Bascule sur la synthèse vocale système hors-ligne.
- `/audio on` | `/audio off` : Active ou coupe la voix.
- `/sources` : Affiche les extraits de manuels scolaires maliens utilisés pour répondre.
- `/profil` : Affiche les statistiques et le niveau de maîtrise de l'apprenant.
- `quit` ou `exit` : Quitte la session.

---

## 8. Tests et Assurance Qualité

Une suite complète de tests automatisés valide le moteur IA et l'ensemble des routes API :

```bash
# Exécution de tous les tests avec pytest
export PYTHONPATH=".:ai-engine/src:backend/src:$PYTHONPATH"
pytest backend/tests -v
```

---

## 9. Structure du Répertoire

```
AlternIA/
├── README.md                          # Documentation générale du projet
├── requirements.txt                   # Dépendances globales du projet
├── pyrightconfig.json                 # Configuration du typage statique
├── .gitignore                         # Exclusions Git
│
├── ai-engine/                         # Moteur d'Intelligence Pédagogique
│   ├── requirements.txt               # Dépendances du moteur IA
│   ├── models/llm/                    # Fichiers GGUF des modèles LLM locaux
│   ├── src/alternia/
│   │   ├── cli/chat.py                # Interface terminale interactive
│   │   ├── config/settings.py         # Paramètres et variables d'environnement
│   │   ├── conversation/              # Gestionnaire de sessions conversationnelles
│   │   ├── core/pedagogical_chunk.py  # Modèle de fragment pédagogique
│   │   ├── embeddings/service.py      # Calcul des vecteurs d'embeddings
│   │   ├── ingestion/                 # Extracteurs PDF et découpeurs pédagogiques
│   │   ├── learner/                   # Profil durable et suivi des notions
│   │   ├── llm/                       # Client LLM local Llama.cpp / GGUF
│   │   ├── orchestration/             # Orchestrateur central AlternIA
│   │   ├── pedagogical/               # Stratégies didactiques socratiques
│   │   ├── rag/                       # Moteur RAG, indexeur et recherche sémantique
│   │   └── tts/engine.py              # Synthèse vocale neuronale HD & fallback
│   └── tests/                         # Tests unitaires du moteur IA
│
├── alta/                              # Portail Web Frontend (Angular 18)
│   ├── package.json                   # Dépendances Node.js
│   ├── src/
│   │   ├── app/
│   │   │   ├── core/                  # Services d'authentification, modèles, constantes
│   │   │   └── features/              # Modules Établissement, Parents, Auth, Avatars
│   │   ├── styles.scss                # Thème global et design system Liquid Glass
│   │   └── index.html                 # Point d'entrée de l'application SPA
│
├── backend/                           # Serveur API FastAPI
│   ├── src/
│   │   ├── db/                        # Modèles SQLAlchemy, connexion DB et seeds
│   │   ├── models/                    # Schémas DTOs Pydantic (auth, boitier, chat, avatar)
│   │   ├── routes/                    # Routeurs API (auth, boitiers, chat, insights, etc.)
│   │   ├── services/                  # Logique métier et interfaçage avec l'AI-Engine
│   │   └── main.py                    # Point d'entrée de l'application FastAPI
│   └── tests/                         # Tests d'intégration des endpoints API
│
├── data/                              # Index vectoriels persistants (Qdrant / Local)
├── knowledge-base/                    # Manuels et programmes scolaires maliens (PDF)
│   ├── 10eme/
│   ├── 11eme/
│   └── 12eme/
├── device/                            # Utilitaires pour le boîtier physique AlternIA
└── scripts/                           # Scripts SQL d'initialisation et utilitaires
```

---

## 10. Licence et Contribution

Le projet **AlternIA** est développé pour favoriser l'égalité des chances et la réussite scolaire au Mali et en Afrique de l'Ouest grâce à une intelligence artificielle ouverte, souveraine et accessible hors-ligne.
