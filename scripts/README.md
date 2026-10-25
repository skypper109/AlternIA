# 🛠️ AlternIA Scripts — Automatisation, Synchronisation & Amorçage

Ce répertoire regroupe les scripts utilitaires d'automatisation, de synchronisation entre plateformes (Backend / Mobile Flutter) et d'amorçage de données pour l'écosystème AlternIA.

---

## 📋 Inventaire des Scripts

### 1. Synchronisation Mobile / Backend (`sync_mobile_backend.py`)
Ce script Python de synchronisation bidirectionnelle garantit la cohérence stricte entre les modèles Pydantic / routes FastAPI du backend et le code Dart de l'application mobile Flutter (`det-mobile`) :
- Analyse des DTOs Python et conversion automatique en classes Dart avec méthodes `fromJson()` et `toJson()`.
- Synchronisation des routes d'API, des clés de payload et des structures de données (exercices, étapes socratiques, culture, podcasts).
- Élimine les régressions d'incompatibilité de schéma lors des montées de version.

**Utilisation :**
```bash
python3 scripts/sync_mobile_backend.py
```

---

### 2. Amorçage de la Base de Données (`seed_db.py`)
Initialise une base de données vierge avec le référentiel curriculaire complet du Mali et des données de démonstration :
- **Cycles & Niveaux** : Fondamental (6ème, 7ème, 8ème, 9ème DEF) et Secondaire (10ème CG/CT, 11ème SC/LL/SECO/STI, 12ème Terminales).
- **Matières officielles** : Mathématiques, Sciences Physiques, Chimie, Biologie, Français, Histoire-Géographie, Philosophie, Anglais.
- **Comptes par défaut** : Administrateur d'établissement, enseignant tuteur, profil élève de test.
- **Enregistrement de boîtier** : Initialisation du boîtier physique par défaut `alta-box1`.

**Utilisation :**
```bash
python3 scripts/seed_db.py
```

---

### 3. Mise à Jour des Constantes Mobiles (`update_mobile.py`)
Met à jour les URLs de production, les clés d'API et les adresses de passerelle du boîtier (`10.42.0.1` ou `https://api.alterniamali.com`) au sein du projet Flutter `det-mobile`.

**Utilisation :**
```bash
python3 scripts/update_mobile.py
```

---

## 🚀 Scripts de Démarrage Rapide (Racine du Projet)

À la racine du projet `AlternIA/`, des scripts facilitent le lancement complet de la pile selon votre environnement :

- **`./start_cpu.sh`** : Lance le backend FastAPI et le moteur d'inférence en mode CPU (idéal pour MacBook ou serveur standard).
- **`./start_gpu.sh`** : Active l'accélération matérielle CUDA (NVIDIA) pour l'inférence des embeddings et du LLM sur serveur GPU (AWS `g4dn.xlarge`).
- **`python3 run_alternia.py`** : Lanceur tout-en-un avec surveillance des processus en temps réel.
