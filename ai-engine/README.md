# 🧠 AlternIA AI Engine — Moteur d'IA Pédagogique, RAG Curriculaire & Vocal

**AI Engine** est le cerveau décisionnel et pédagogique de l'écosystème AlternIA. Il transforme une question brute posée par un élève (par la voix, le texte ou la photo d'un exercice) en un accompagnement **socratique bienveillant**, rigoureusement aligné sur les **programmes scolaires officiels du Mali**.

---

## 📋 Table des Matières

1. [Architecture & Pipeline d'Inférence](#1-architecture--pipeline-dinférence)
2. [Orchestrateur & Gestion du Périmètre Pédagogique](#2-orchestrateur--gestion-du-périmètre-pédagogique)
3. [Moteur Socratique & Prompt Builder](#3-moteur-socratique--prompt-builder)
4. [RAG Curriculaire Malien (Base de Connaissances)](#4-rag-curriculaire-malien-base-de-connaissances)
5. [Traitement Vocal : STT, TTS Streaming & Barge-In](#5-traitement-vocal--stt-tts-streaming--barge-in)
6. [Moteurs LLM (Local Edge & Cloud)](#6-moteurs-llm-local-edge--cloud)
7. [Structure du Répertoire](#7-structure-du-répertoire)
8. [Lancement & Tests](#8-lancement--tests)

---

## 1. Architecture & Pipeline d'Inférence

Le flux complet d'une interaction apprenant suit une chaîne rigoureuse en 8 étapes :

```text
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                           QUESTION DE L'ÉLÈVE                               │
 │                  (Voix I2S / Texte Kiosk / Photo OCR)                       │
 └──────────────────────────────────────┬──────────────────────────────────────┘
                                        │
                                        ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                    1. RECONNAISSANCE VOCALE (STT)                           │
 │      Faster-Whisper (quantifié int8/float16) avec normalisation audio       │
 └──────────────────────────────────────┬──────────────────────────────────────┘
                                        │
                                        ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                      2. ORCHESTRATEUR CENTRAL                               │
 │   • Classification d'intention (cours, exercice, méta-tuteur, hors-sujet)   │
 │   • Vérification du niveau : Fondamental (DEF) ou Secondaire (10e-12e)      │
 │   • Filtrage bienveillant (autorise les questions sur le rôle du tuteur)   │
 └──────────────────────────────────────┬──────────────────────────────────────┘
                                        │
                                        ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                   3. RECHERCHE VECTORIELLE RAG                              │
 │   • Embeddings denses BGE / MiniLM                                          │
 │   • Récupération des extraits de manuels maliens officiels (Qdrant / Local) │
 └──────────────────────────────────────┬──────────────────────────────────────┘
                                        │
                                        ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                    4. PROMPT BUILDER SOCRATIQUE                             │
 │   • Injection de la pédagogie active (ne jamais donner la réponse brute)    │
 │   • Guidage pas-à-pas avec questions de relance et indices progressifs      │
 └──────────────────────────────────────┬──────────────────────────────────────┘
                                        │
                                        ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                     5. INFÉRENCE DU MODÈLE LLM                              │
 │      Qwen 2.5 (1.5B/3B GGUF en Edge local) ou Cloud (Groq / Gemini)         │
 └──────────────────────────────────────┬──────────────────────────────────────┘
                                        │
                                        ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                  6. STREAMING PAR PHRASE (~2s LATENCE)                      │
 │   • Découpage à chaud du texte aux ponctuations (. ! ? ;)                   │
 │   • Envoi immédiat de la phrase 1 au TTS pendant que la suite s'infère      │
 └──────────────────────────────────────┬──────────────────────────────────────┘
                                        │
                                        ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │               7. SYNTHÈSE VOCALE NEURONALE & AFFICHAGE                      │
 │   • Diffusion audio I2S (MAX98357A) avec en-têtes non bufferisés            │
 │   • Rendu mathématique KaTeX et étapes visuelles sur le Kiosk TV HDMI       │
 └──────────────────────────────────────┬──────────────────────────────────────┘
                                        │
                                        ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                8. GESTION DU BARGE-IN (INTERRUPTION)                        │
 │      Si l'élève appuie sur le micro ➔ Coupure audio immédiate & réécoute    │
 └─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Orchestrateur & Gestion du Périmètre Pédagogique

Le module [`src/alternia/orchestration/orchestrator.py`](file:///Users/ibrahimsorydiallo/Desktop/OSC/AlternIA/ai-engine/src/alternia/orchestration/orchestrator.py) joue le rôle d'aiguilleur intelligent :
- **Autorisation méta-pédagogique** : L'élève peut demander librement : *"Que peux-tu faire ?"*, *"Qui es-tu ?"*, *"Aide-moi à réviser"* sans déclencher de refus de périmètre.
- **Filtrage hors-programme** : Si la question est totalement étrangère aux apprentissages scolaires (politique partisane, divertissement hors-sujet), l'orchestrateur recentre l'élève poliment sur ses cours.
- **Gestion des sessions** : Préservation du contexte conversationnel immédiat pour permettre à l'élève de répondre par un simple *"Oui"*, *"Je ne comprends pas"* ou *"C'est égal à 4"*.

---

## 3. Moteur Socratique & Prompt Builder

Le dossier [`src/alternia/pedagogical/`](file:///Users/ibrahimsorydiallo/Desktop/OSC/AlternIA/ai-engine/src/alternia/pedagogical/) incarne la philosophie d'apprentissage d'AlternIA :

### Règle d'Or Pédagogique
> **Un tuteur ne donne JAMAIS la solution finale d'un exercice.**
> Il pose des questions ciblées, décompose le problème en sous-étapes logiques, valorise les efforts de l'élève et l'amène à trouver lui-même la réponse.

### Composants Clés
- `prompt_builder.py` : Assemble dynamiquement les consignes pédagogiques, le niveau de l'apprenant (ex: `11ème Sciences`), la matière détectée et les sources officielles RAG.
- `curriculum_scope.py` : Contrôle les limites du programme pour chaque niveau selon le référentiel malien.
- `response_validator.py` : Analyse la sortie du LLM pour vérifier qu'aucune réponse brute prématurée n'est divulguée.

---

## 4. RAG Curriculaire Malien (Base de Connaissances)

Le sous-système [`src/alternia/rag/`](file:///Users/ibrahimsorydiallo/Desktop/OSC/AlternIA/ai-engine/src/alternia/rag/) indexe l'intégralité des manuels scolaires officiels du Mali :
- **Niveaux indexés** :
  - **DEF (7ème, 8ème, 9ème Année)** : Français, Mathématiques, Sciences Physiques, Histoire-Géographie, Biologie.
  - **Lycée 10ème Année** : Tronc Commun Général & Technique.
  - **Lycée 11ème Année** : Séries Sciences, Lettres, Économie.
  - **Lycée 12ème Année (Terminale)** : Séries TSE, TSExp, TSS, TSEco, TLL.
- **Vector Store** : Déploiement hybride avec **Qdrant** en cloud ou index vectoriel local sérialisé pour le fonctionnement autonome sur Raspberry Pi.
- **Contextualizer** : Sélectionne les 2 à 3 fragments les plus pertinents et génère les métadonnées de source affichées sur l'écran Kiosk (**RAG Source Badge**).

---

## 5. Traitement Vocal : STT, TTS Streaming & Barge-In

### 🎙️ Reconnaissance Vocale (STT) — [`src/alternia/stt/`](file:///Users/ibrahimsorydiallo/Desktop/OSC/AlternIA/ai-engine/src/alternia/stt/)
- Modèle **Faster-Whisper** avec VAD (*Voice Activity Detection*) intégré.
- Capable de transcrire avec précision la voix de l'élève, y compris avec le débit et les intonations d'Afrique de l'Ouest.

### 🗣️ Synthèse Vocale (TTS) avec Sentence Streaming — [`src/alternia/tts/`](file:///Users/ibrahimsorydiallo/Desktop/OSC/AlternIA/ai-engine/src/alternia/tts/)
- Voix neuronale fluide haute fidélité (`fr-FR-VivienneMultilingualNeural` ou voix personnalisée).
- **Streaming par phrase** : Le texte est tronçonné dès qu'une ponctuation forte est détectée. Le premier morceau audio est généré en **~2 secondes** et envoyé immédiatement au Raspberry Pi, éliminant toute sensation de lenteur.
- **Normalisation scientifique** : Les formules mathématiques (fractions, racines carrées, puissances) sont oralisées phonétiquement de manière naturelle (ex: $x^2 + 3$ lu *"x au carré plus trois"*).

### 🛑 Microphone Barge-In (Interruption Immédiate)
Dès que l'élève appuie sur le bouton micro ou reprend la parole :
- Le signal d'interruption coupe instantanément le lecteur audio `mpv` sur le Raspberry Pi.
- La file d'attente TTS est purgée sans latence pour écouter la nouvelle intervention de l'élève.

---

## 6. Moteurs LLM (Local Edge & Cloud)

Le système supporte une exécution hybride :
1. **Mode Edge Local (Boîtier Déconnecté)** :
   - Modèle **Qwen 2.5 (1.5B ou 3B Instruct)** au format GGUF via `llama-cpp-python`.
   - Exécution directe sur le CPU Quad-Core et les 8 Go de RAM du Raspberry Pi 5.
2. **Mode Cloud Accéléré (Connecté)** :
   - Inférence GPU sur instance AWS via **Groq** (Llama 3.3 70B ultra-rapide) ou **Google Gemini**.

---

## 7. Structure du Répertoire

```text
ai-engine/src/alternia/
├── config/              # Configuration globale & variables d'environnement
├── conversation/        # Gestionnaire de mémoire conversationnelle
├── llm/                 # Adaptateurs d'inférence LLM (Local GGUF / Cloud APIs)
├── orchestration/       # Orchestrateur central et classification des intentions
├── pedagogical/         # Moteur socratique, prompts et règles de programme
├── rag/                 # Chunker, embeddings, indexation et recherche Qdrant
├── stt/                 # Transcription vocale Faster-Whisper
├── tts/                 # Synthèse vocale neuronale et découpage par phrases
└── validation/          # Garde-fous et conformité des réponses
```

---

## 8. Lancement & Tests

```bash
# 1. Activer l'environnement virtuel
source /Users/ibrahimsorydiallo/Desktop/OSC/AlternIA/.venv/bin/activate

# 2. Lancer les tests unitaires du moteur pédagogique
pytest ai-engine/tests/ -v

# 3. Tester une inférence vocale de bout en bout
python3 raspberry-pi/scripts/test_ia_voice.py "Explique-moi le théorème de Pythagore"
```
