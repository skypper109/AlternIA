# AlternIA - Dispositif Pédagogique Intelligent et Tuteur Vocal pour le Secondaire au Mali

---

## 1. Presentation generale et vision du projet

AlternIA est un systeme d'assistance pedagogique base sur l'intelligence artificielle, concu pour accompagner les eleves du cycle secondaire au Mali (10eme, 11eme et 12eme Annee / Terminale).

Le projet repond aux defis structurels d'acces a un encadrement scolaire personnalise et aux ressources educatives dans les contextes a connectivite limitee ou instable. Il est concu des l'origine selon le paradigme **Edge AI / Local-First** :
- Le moteur d'inference linguistique (LLM) s'execute localement sur le dispositif physique sans dependance obligatoire a une connexion Internet permanente.
- La base de connaissances pedagogiques officielles du Mali est vectorisee et interrogee localement via un pipeline RAG (Retrieval-Augmented Generation).
- Le systeme adapte son niveau d'exigence, ses explications et son vocabulaire a la classe, a la serie et a la progression reelle de chaque eleve.
- Une interface vocale neuronale haute fidelite permet un dialogue naturel, fluide et didactique avec l'apprenant.

---

## 2. Contexte educatif et alignement sur le programme national malien

AlternIA embarque l'integralite de la structure curriculaire du ministere de l'Education nationale du Mali.

### 2.1. Niveaux et filieres supportes

1. **10eme Annee (Tronc Commun)**
   - Filieres : 10eme Commune Generale (CG), 10eme Commune Technique (CT).
   - Matieres principales : Mathematiques, Physique-Chimie, Francais, Anglais, Biologie, Histoire, Geographie.

2. **11eme Annee (Specialisation)**
   - Series :
     - 11eme Sciences (11eme SC)
     - 11eme Lettres (11eme LL)
     - 11eme Sciences Economiques (11eme SECO)
     - 11eme Sciences et Technologies Industrielles (11eme STI)
   - Matieres adaptees a chaque serie : Mathematiques, Sciences Physiques, Chimie, Francais, Philosophie, Anglais, Biologie, Geologie, Histoire, Geographie.

3. **12eme Annee (Terminale & Baccalaureat)**
   - Series :
     - TSE : Terminale Sciences Exactes (priorite forte Mathematiques, Physique-Chimie)
     - TSExp : Terminale Sciences Experimentales (Sciences Naturelles, Physique-Chimie, Mathematiques)
     - TSS : Terminale Sciences Sociales (Histoire, Geographie, Philosophie, Francais, Mathematiques appliquees)
     - TSEco : Terminale Sciences Economiques (Economie, Mathematiques appliquees, Gestion)
     - TLL : Terminale Lettres et Langues (Litterature, Philosophie, Langues vivantes)

### 2.2. Objectif d'alignement pedagogique
Lorsqu'un eleve pose une question, AlternIA ne repond pas de facon generique : le systeme identifie la classe, consulte les manuels et programmes officiels de la serie selectionnee, et formule une reponse rigoureusement conforme aux attentes du programme scolaire malien.

---

## 3. Architecture globale du systeme

Le projet est compose de 4 briques logicielles interconnectees :

```
+-------------------------------------------------------------------------+
|                          CLIENTS D'ACCES                                |
|  +-----------------------------------+  +----------------------------+  |
|  | Interface CLI Terminal Interactive|  | Application Mobile Flutter |  |
|  +-----------------------------------+  +----------------------------+  |
+------------------------------------+------------------------------------+
                                     |
                                     v
+------------------------------------+------------------------------------+
|                         BACKEND FASTAPI                                 |
|  - API RESTful (Curriculum, Profils apprenants, Diagnostic materiel)   |
|  - Streaming SSE Token-par-Token (/api/chat/stream)                     |
|  - Validation et normalisation des donnees d'entree Pydantic            |
+------------------------------------+------------------------------------+
                                     |
                                     v
+------------------------------------+------------------------------------+
|                     AI-ENGINE (ORCHESTRATEUR)                           |
|                                                                         |
|  +-------------------------+      +----------------------------------+  |
|  |   Moteur Pedagogique    |      |         RAG Contextuel           |  |
|  | - Detection d'intention |      | - Embeddings BGE Multilingues    |  |
|  | - Strategie (cours/exo) |      | - Base Vectorielle Qdrant/Local  |  |
|  | - Construction Prompts  |      | - Filtrage Classe / Matiere      |  |
|  +-------------------------+      +----------------------------------+  |
|               |                                    |                    |
|               +-----------------+------------------+                    |
|                                 |                                       |
|                                 v                                       |
|  +-------------------------------------------------------------------+  |
|  |                    LLM Local (GGUF / Llama.cpp)                   |  |
|  |    Inference locale Qwen 2.5 3B Instruct avec acceleration GPU    |  |
|  +-------------------------------------------------------------------+  |
|                                 |                                       |
|                                 v                                       |
|  +-------------------------+      +----------------------------------+  |
|  |   Memoire Apprenant     |      |      Synthese Vocale (TTS)       |  |
|  | - Historique durable    |      | - Voix Neurales Haute Definition |  |
|  | - Suivi des notions     |      | - Traduction phonetique maths    |  |
|  | - Statistiques maitrise |      | - Repli systeme hors-ligne       |  |
|  +-------------------------+      +----------------------------------+  |
+-------------------------------------------------------------------------+
```

---

## 4. Architecture detaillee de l'AI-Engine (`ai-engine`)

Le dossier `ai-engine/src/alternia/` contient l'ensemble de la logique algorithmique et de traitement automatique du langage naturel.

### 4.1. Ingestion et Chunking Pedagogique (`ingestion/`, `core/`)
- **Chargeur de documents (`ingestion/loaders/pdf.py`)** : Extraction structuree du texte depuis les manuels scolaires et programmes officiels au format PDF via PyMuPDF (`fitz`) et PyPDF.
- **Decoupeur pedagogique (`ingestion/chunking/pedagogical_chunker.py`)** : Decoupe semantique respectant la hierarchie du cours (Chapitre, Lecon, Notion, Exercice, Correction) plutot qu'une simple decoupe par nombre brut de caracteres.
- **Format de Chunk (`core/pedagogical_chunk.py`)** : Chaque fragment conserve ses metadonnees critiques (classe, matiere, serie, chapitre, lecon, niveau de difficulte, mots-cles).

### 4.2. Embeddings et Base Vectorielle (`embeddings/`, `rag/`)
- **Service d'Embedding (`rag/embeddings.py`, `embeddings/service.py`)** : Calcul des vecteurs d'embeddings denses via `sentence-transformers` (modele multilingue `BAAI/bge-small-en-v1.5` ou modeles francophones legers).
- **Magasin Vectoriel Hybride (`rag/vector_store.py`, `rag/qdrant_store.py`)** :
  - Mode local ultra-leger base sur index memoire/disque binaire pour dispositifs a ressources contraintes.
  - Mode Qdrant embarque pour indexations et recherches vectorielles filtrees a grande echelle.
- **Recherche Semantique (`rag/semantic_retriever.py`)** : Recherche hybride combinant similarite cosinus et filtrage strict sur les metadonnees (classe de l'eleve, matiere courante).

### 4.3. Moteur Pedagogique et Strategies Didactiques (`pedagogical/`, `pedagogy/`)
Le moteur pedagogique determine l'approche pedagogique optimale :
- **Detection d'intention** : Identification de l'intention de l'eleve (demande de definition, resolution d'exercice guidant pas a pas, demande de correction, question methodologique).
- **Strategies didactiques modularisees (`pedagogical/strategies/`)** :
  - *ExplanationStrategy* : Explication claire, progressive, illustree d'analogies issues du quotidien malien/ouest-africain.
  - *ExerciseStrategy* : Resolution socratique d'exercices (ne donne pas la reponse brute directement, mais guide par questions etapes par etapes).
- **Construction de Prompts (`pedagogical/prompt_builder.py`)** : Injecte le contexte curriculaire, la definition du profil de l'eleve et les extraits documentaires exacts dans le prompt systeme du LLM.

### 4.4. Memoire d'Apprentissage et Suivi Durable (`learner/`)
- **Profil d'Apprentissage (`learner/profile.py`, `learner/models.py`)** : Structure dataclass enregistrant :
  - `mastered_topics` : Notions validees et maitrisees.
  - `topics_to_review` : Notions posant des difficultes a retravailler.
  - `topic_progress` : Scores quantitatifs de reussite par notion.
  - `statistics` : Total des questions, exercices resolus, taux de succes.
- **Gestionnaire d'Apprentissage (`learner/manager.py`)** : Persistance et conversion des profils vers le contexte actif pour personnaliser les reponses en temps reel.

### 4.5. Client LLM Local (`llm/`)
- **Inference locale (`llm/local_client.py`)** : Execute les modeles au format GGUF via `llama-cpp-python`.
- **Modele pre-configure** : `Qwen2.5-3B-Instruct-Q4_K_M.gguf` offrant un equilibre remarquable entre qualite de raisonnement francophone, concision didactique et rapidite d'execution (15 a 40 tokens/s selon le materiel).
- **Acceleration materielle** : Prise en charge transparente de Metal (Apple Silicon / Mac), CUDA (Nvidia), et optimisation CPU multi-thread (ARM Cortex pour Raspberry Pi 4/5).
- **Generation Streaming** : Generateur de tokens au fil de l'eau pour affichage instantane sans temps de latence percue.

### 4.6. Moteur Text-To-Speech Haute Fidelite (`tts/`)
- **Synthese Neurale HD (`tts/engine.py`)** : Utilise le moteur Neural TTS avec des voix francaises ultra-naturelles et expressives :
  - `Vivienne` (Feminine, douce, pedagogique, profil ChatGPT Voice).
  - `Remy` (Masculine, naturelle et dynamique).
  - `Denise`, `Eloise`, `Henri`.
- **Nettoyage et lecture phonetique des maths** : Traduction automatique des symboles scientifiques avant synthese (`ax² + bx + c = 0` $\rightarrow$ *"a x au carre plus b x plus c egale zero"*, `√` $\rightarrow$ *"racine carree de"*, `±` $\rightarrow$ *"plus ou moins"*, `Δ` $\rightarrow$ *"delta"*).
- **Mode de repli systeme** : Bascule automatique sur la synthese vocale locale (`say` sur macOS, `espeak-ng` sur Linux) si le dispositif est hors-ligne.
- **Architecture de diffusion** : Le texte est streame a l'ecran a pleine vitesse, puis la voix prononce la reponse de facon continue et harmonieuse avec interruption immediate (`tts.stop()`) lors d'une nouvelle requete.

---

## 5. Architecture du Backend FastAPI (`backend`)

Le backend FastAPI ([backend/src/main.py](backend/src/main.py)) expose l'ensemble des fonctionnalites sous forme d'API HTTP REST et de flux SSE (Server-Sent Events).

### 5.1. Specifications des Endpoints

| Methode | Route | Description |
|---|---|---|
| `GET` | `/health` ou `/api/health` | Verification de l'etat du serveur, disponibilite RAG et LLM |
| `POST` | `/api/chat` (ou `/api/ask`) | Envoi d'une question avec reponse synchrone complete |
| `POST` | `/api/chat/stream` (ou `/api/ask/stream`) | Streaming Server-Sent Events (SSE) token par token |
| `GET` | `/api/curriculum` | Description de l'arborescence des classes et series maliennes |
| `GET` | `/api/learner/{student_id}` | Consultation du profil et des notions maitrisees/a revoir |
| `POST` | `/api/learner/{student_id}/interaction` | Enregistrement d'un resultat d'exercice ou quiz |
| `POST` | `/api/session/reset` | Reinitialisation de l'historique conversationnel |
| `GET` | `/api/device/info` | Metadonnees sur le boitier AlternIA local |

---

## 6. Installation et Deploiement Pas a Pas

### 6.1. Prerequis systeme
- Systeme d'exploitation : macOS (Apple Silicon ou Intel), Linux (Ubuntu/Debian, Raspberry Pi OS 64-bit).
- Python : Version 3.11 ou 3.12 recommandee.
- Gestionnaires de son systeme : `afplay` (inclus de base sur macOS), ou `mpv` / `ffplay` / `alsa` sur Linux.

### 6.2. Installation des dependances

Cloner le depot et creer un environnement virtuel Python :

```bash
git clone https://github.com/skypper109/AlternIA.git
cd AlternIA

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

### 6.3. Telechargement du modele de langage (LLM)

Placer le fichier du modele LLM quantifie GGUF dans le repertoire dedie :

```bash
mkdir -p ai-engine/models/llm
```

Telecharger le modele `Qwen2.5-3B-Instruct` quantifie en Q4_K_M (environ 2.1 Go) :

```bash
curl -L -o ai-engine/models/llm/qwen2.5-3b-instruct-q4_k_m.gguf \
  https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf
```

### 6.4. Indexation de la base de connaissances malienne

Pour indexer ou reindexer l'ensemble des manuels scolaires situes dans `knowledge-base/` :

```bash
export PYTHONPATH="ai-engine/src:backend/src:$PYTHONPATH"
python ai-engine/src/alternia/rag/indexer.py
```

---

## 7. Guide d'utilisation

### 7.1. Mode Terminal Interactif (CLI Chat)

Le moyen le plus direct d'interagir avec AlternIA :

```bash
export PYTHONPATH="ai-engine/src:backend/src:$PYTHONPATH"
python ai-engine/src/alternia/cli/chat.py
```

#### Commandes speciales dans le terminal :
- `/classe 10eme` | `/classe 11eme` | `/classe 12eme` : Change la classe active et recalibre le RAG.
- `/matiere <nom>` : Bascule sur une matiere (`mathematiques`, `physique`, `chimie`, `francais`, etc.).
- `/voix` : Affiche les voix disponibles et la voix actuelle.
- `/voix vivienne` : Active la voix feminine neurale (style ChatGPT).
- `/voix remy` : Active la voix masculine neurale.
- `/voix system` : Bascule sur la synthese vocale locale hors-ligne.
- `/audio on` | `/audio off` : Active ou coupe la voix.
- `/sources` : Affiche les extraits de manuels scolaires maliens utilises pour repondre.
- `/profil` : Visualise le tableau de bord de l'apprenant (notions acquises, difficultes).
- `quit` ou `exit` : Quitte la session.

### 7.2. Lancement du Serveur Backend API

Pour demarrer le serveur d'API REST et Streaming :

```bash
export PYTHONPATH="ai-engine/src:backend/src:$PYTHONPATH"
uvicorn backend.src.main:app --host 0.0.0.0 --port 8000 --reload
```

Documentation Swagger interactive disponible sur : `http://localhost:8000/docs`.

---

## 8. Exemples d'appels API

### 8.1. Question synchrone (`/api/chat`)

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Comment resoudre une equation du second degre ax2 + bx + c = 0 ?",
    "student_class": "10eme",
    "subject": "mathematiques",
    "enable_rag": true
  }'
```

### 8.2. Streaming en temps reel SSE (`/api/chat/stream`)

```bash
curl -N -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Donne-moi la formule du discriminant et un exemple simple.",
    "student_class": "10eme",
    "subject": "mathematiques",
    "enable_rag": true
  }'
```

### 8.3. Enregistrement d'un resultat d'exercice (`/api/learner/{id}/interaction`)

```bash
curl -X POST http://localhost:8000/api/learner/eleve-001/interaction \
  -H "Content-Type: application/json" \
  -d '{
    "student_class": "10eme",
    "intent": "exercise",
    "subject": "mathematiques",
    "topic": "equations du second degre",
    "difficulty": "moyen",
    "success": true
  }'
```

---

## 9. Tests et Assurance Qualite

Le projet integre une suite de tests unitaires et d'integration couvrant l'integralite de la chaine fonctionnelle.

### 9.1. Execution de la suite de tests

```bash
export PYTHONPATH="ai-engine/src:backend/src:$PYTHONPATH"
pytest ai-engine/tests -v
```

### 9.2. Principaux modules de test
- `test_backend_api.py` : Verification des endpoints FastAPI, formats de reponse et gestion des classes.
- `test_tts_engine.py` : Validation de l'initialisation, du basculement des voix et du nettoyage phonetique des maths.
- `test_learner_profile.py` : Validation de l'evolution des profils apprenants et du suivi des notions.
- `test_rag_service.py` & `test_semantic_retriever.py` : Validation de la recherche semantique et des scores de pertinence.
- `test_pedagogical_engine.py` : Verification des prompts systemes et de l'adaptation curriculaire.

---

## 10. Arborescence du repertoire

```
AlternIA/
├── README.md                          # Documentation technique generale
├── requirements.txt                   # Dependances generales du projet
├── pyrightconfig.json                 # Configuration du typage statique
├── .gitignore                         # Exclusions de versionnement
│
├── ai-engine/                         # Moteur d'Intelligence Pedagogique
│   ├── requirements.txt               # Dependances specifiques au moteur IA
│   ├── models/
│   │   └── llm/                       # Repertoire du modele local GGUF
│   ├── src/
│   │   └── alternia/
│   │       ├── cli/
│   │       │   └── chat.py            # Interface terminale interactive
│   │       ├── config/
│   │       │   └── settings.py        # Configuration et variables d'environnement
│   │       ├── conversation/
│   │       │   ├── context.py         # Gestionnaire de session conversationnelle
│   │       │   ├── manager.py         # Cycle de vie des sessions
│   │       │   └── models.py          # Modeles de messages et historiques
│   │       ├── core/
│   │       │   └── pedagogical_chunk.py # Structure des fragments pedagogiques
│   │       ├── embeddings/
│   │       │   └── service.py         # Calcul des embeddings denses
│   │       ├── ingestion/
│   │       │   ├── chunking/          # Algorithmes de decoupage structure
│   │       │   └── loaders/           # Extracteurs de documents (PDF)
│   │       ├── learner/
│   │       │   ├── adaptation.py      # Adaptation didactique au niveau
│   │       │   ├── assessment.py      # Module d'evaluation des acquis
│   │       │   ├── manager.py         # Gestionnaire persistant des profils
│   │       │   ├── models.py          # Modeles de donnees de progression
│   │       │   └── profile.py         # Profil apprenant durable
│   │       ├── llm/
│   │       │   ├── client.py          # Interface abstraite client LLM
│   │       │   └── local_client.py    # Implementation locale Llama.cpp / GGUF
│   │       ├── orchestration/
│   │       │   └── orchestrator.py    # Orchestrateur central AlternIA
│   │       ├── pedagogical/
│   │       │   ├── engine.py          # Moteur de decision pedagogique
│   │       │   ├── models.py          # Modeles pedagogiques
│   │       │   ├── prompt_builder.py  # Constructeur de prompts adaptatifs
│   │       │   └── strategies/        # Strategies d'explication et d'exercices
│   │       ├── rag/
│   │       │   ├── embeddings.py      # Wrapper d'embedding RAG
│   │       │   ├── indexer.py         # Script d'indexation des manuels
│   │       │   ├── retriever.py       # Extracteur de documents pertinents
│   │       │   ├── semantic_retriever.py # Recherche semantique vectorielle
│   │       │   ├── service.py         # Service RAG haut niveau
│   │       │   └── vector_store.py    # Stockage vectoriel local
│   │       └── tts/
│   │           └── engine.py          # Moteur de synthese vocale HD (Neural Edge + fallback)
│   └── tests/                         # Suites de tests unitaires et d'integration
│
├── backend/                           # Serveur API FastAPI
│   └── src/
│       └── main.py                    # Application FastAPI, routes REST et SSE
│
├── knowledge-base/                    # Manuels et programmes scolaires maliens (PDF)
│   ├── 10eme/
│   ├── 11eme/
│   └── 12eme/
│
└── data/                              # Index vectoriels persistants (Qdrant / Local)
```

---

## 11. Licence et Contributions

Le projet AlternIA est developpe pour favoriser l'egalite des chances et la reussite scolaire au Mali par l'intelligence artificielle ouverte et souveraine.
