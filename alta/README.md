# 🏫 Alta — Portail Web de Gestion Scolaire & Supervision de Parc

**Alta** est le portail web d'administration, de pilotage pédagogique et de supervision de l'écosystème **AlternIA**. Il est accessible en ligne via **`https://admin.alterniamali.com`**.

Développé en **Angular 18** avec une architecture orientée composants autonomes (*Standalone Components*) et un design system sombre et immersif (*Liquid Glass*), il offre des tableaux de bord sur-mesure pour les directeurs d'établissement, les enseignants et les parents d'élèves.

---

## 🌟 Espaces & Fonctionnalités

### 1. Espace Établissement & Enseignants (`src/app/features/etablissement/`)
- **Supervision en Temps Réel du Parc de Boîtiers Alta-Box** :
  - Visualisation des boîtiers déployés dans chaque salle de classe.
  - Suivi des battements de cœur (*heartbeat*), de la température CPU, de l'état du réseau Wi-Fi `Alta-box1` et du nombre d'élèves connectés.
- **Tableau de Bord Pédagogique des Classes** :
  - Statistiques de consultation par matière (Mathématiques, Physique, Biologie, Français).
  - Taux de complétion des exercices socratiques et points de blocage collectifs.
- **Résolution des Alertes Pédagogiques** :
  - Détection automatique des élèves en situation de décrochage sur des notions spécifiques du programme officiel malien.

### 2. Espace Parent (`src/app/features/parent/`)
- **Suivi Personnalisé de l'Enfant** :
  - Consultation des progrès réguliers, des fiches de cours révisées et des quiz réussis.
  - Temps d'interaction quotidien avec le tuteur vocal socratique.
- **Gestion du Boîtier Familial** :
  - Association et paramétrage du boîtier physique à la maison.

### 3. Authentification & Sécurité (`src/app/features/auth/`)
- Gestion des rôles : Administrateur Établissement, Enseignant, Parent.
- Sécurisation des sessions par jetons JWT et intercepteurs HTTP Angular.

---

## 🛠️ Stack Technique

- **Framework** : Angular 18 (Standalone Components, Signals, Reactive Forms)
- **Langage** : TypeScript 5.4
- **Styling** : SCSS modulaire & Design System *Liquid Glass*
- **Communication** : API REST FastAPI (`https://api.alterniamali.com`) et WebSockets de télémétrie

---

## 📦 Installation & Démarrage

```bash
# 1. Cloner et installer les dépendances
cd AlternIA/alta
npm install

# 2. Lancer le serveur de développement local
npm start
```

Le portail sera accessible sur `http://localhost:4200/`.

### Compilation de Production

```bash
npm run build
```

Les fichiers compilés et optimisés sont générés dans le dossier `dist/`.

---

## 📁 Structure du Projet

```text
src/app/
├── core/                # Services d'authentification, intercepteurs HTTP, gardes de route
├── data/                # DTOs, modèles de données et sources d'API
├── domain/              # Modèles métier et entités (Boîtier, Apprenant, Établissement)
├── features/
│   ├── auth/            # Connexion, inscription et gestion du profil
│   ├── etablissement/   # Tableau de bord directeur, supervision boîtiers, alertes
│   └── parent/          # Tableau de bord parent et suivi de l'enfant
└── layout/              # Barres de navigation, barres latérales et structure de page
```
