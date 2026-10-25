# 🖥️ AlternIA Device Frontend — Interface Kiosk & Portail Élève

Ce dossier contient l'interface utilisateur web monopage (**SPA**) du terminal AlternIA. Elle est exécutée en local sur le Raspberry Pi 5 en mode **Kiosk HDMI TV (Chromium plein écran)** et servie simultanément aux smartphones et tablettes connectés au réseau Wi-Fi local **`Alta-box1`** via le portail captif (**`https://device.alterniamali.com`**).

---

## 🌟 Fonctionnalités Principales

1. **Affichage Optimisé pour Télévision (Kiosk TV 1080p)** :
   - Interface plein écran à fort contraste, lisible à plusieurs mètres de distance dans une salle de classe.
   - Typographie soignée, composants visuels fluides et transitions animées.
   - Navigation compatible avec les boutons physiques du boîtier, une télécommande ou un clavier/souris standard.

2. **Affichage Responsive Mobile & Tablette** :
   - Adaptation automatique de la mise en page lors d'un accès depuis un smartphone d'élève (menu escamotable, interactions tactiles directes).

3. **Synchronisation Temps Réel avec le Matériel (`DeviceSyncService`)** :
   - Liaison bidirectionnelle WebSocket avec le boîtier physique (`/ws/remote` ou `/ws/device`).
   - Tout appui sur les boutons physiques du Raspberry Pi 5 (changement de classe, activation du micro) met à jour instantanément les éléments visuels à l'écran.

4. **Visualiseur d'Ondes Sonores & Vortex Hub (`VortexUI`)** :
   - Canvas audio-réactif affichant les modulations de la voix lors de l'enregistrement ou de la lecture du tuteur IA.
   - Indicateur visuel d'écoute, de réflexion et de parole synchronisé avec la LED tricolore physique.

5. **Moteur d'Affichage Pédagogique Socratique** :
   - Décomposition des explications en étapes claires et progressives.
   - Rendu haute fidélité des formules mathématiques, équations chimiques et symboles scientifiques via **KaTeX**.
   - Affichage de l'encart de référence officiel du programme malien (**RAG Source Badge** : manuel, niveau, chapitre).

6. **Arborescence Curriculaire Malienne Complète (`curriculum.js`)** :
   - **Fondamental (Second Cycle)** : 6ème, 7ème, 8ème, 9ème Année (DEF).
   - **Secondaire (Lycée)** : 10ème (CG/CT), 11ème (SC, LL, SECO, STI), 12ème Terminale (TSE, TSExp, TSS, TSEco, TLL).

---

## 📂 Structure des Fichiers

```text
device/frontend/
├── index.html                   # Structure HTML5 sémantique de l'interface Kiosk & mobile
├── app.js                       # Contrôleur principal de l'application (AlternIAApp)
├── styles.css                   # Feuilles de styles CSS modernes (variables, thèmes, Kiosk TV)
├── vite.config.js               # Configuration du bundler Vite pour le build de production
├── package.json                 # Dépendances (KaTeX, Vite)
├── js/
│   ├── config/
│   │   └── curriculum.js        # Données officielles des cycles, classes, séries et matières du Mali
│   ├── services/
│   │   ├── api.js               # Communication REST avec le backend (/api/device, /api/chat)
│   │   ├── audio.js             # Moteur audio Web Audio API et synthèse vocale
│   │   ├── speech.js            # Capture du flux microphone et gestion du streaming vocal
│   │   ├── did.js               # Intégration vidéo d'avatar animé
│   │   └── device-sync.js       # Client WebSocket temps réel pour la synchronisation matérielle
│   └── ui/
│       ├── vortex.js            # Visualiseur graphique circulaire interactif / onde sonore
│       └── katex-renderer.js    # Moteur de rendu LaTeX pour formules mathématiques et scientifiques
├── public/                      # Assets statiques (icônes, sons, logos)
└── dist/                        # Bundle de production compilé et optimisé pour le Kiosk
```

---

## 🛠️ Installation & Développement Local

Le projet utilise **Vite** comme serveur de développement et outil de compilation.

```bash
# 1. Se positionner dans le dossier
cd AlternIA/device/frontend

# 2. Installer les dépendances
npm install

# 3. Lancer le serveur de développement local avec rechargement à chaud
npm run dev
```

L'application sera accessible sur `http://localhost:5173/` (ou port indiqué).

### 📦 Compilation pour Production (Build Kiosk)

```bash
npm run build
```

Le résultat est généré dans le dossier `dist/`. C'est ce dossier qui est servi par Nginx sur le Raspberry Pi 5 sous l'URL locale `http://127.0.0.1:8080` et accessible en ligne via `https://device.alterniamali.com`.

---

## 🔗 Événements WebSocket Supportés (`DeviceSyncService`)

Le frontend écoute les événements JSON émis par le contrôleur matériel ou le serveur :

| Type d'événement | Charge utile (Payload) | Action sur l'interface |
| :--- | :--- | :--- |
| `class_changed` | `{"class": "10eme", "cycle": "secondaire"}` | Sélectionne la carte de classe correspondante et charge le programme |
| `mic_state` | `{"state": "recording"}` | Active l'animation de prise de parole et l'écoute du micro |
| `mic_state` | `{"state": "thinking"}` | Affiche l'indicateur de réflexion de l'IA |
| `mic_state` | `{"state": "speaking"}` | Lance l'animation du visualiseur d'ondes audio et active le texte |
| `barge_in` | `{}` | Coupe immédiatement l'audio en cours et réinitialise l'affichage |
| `remote_key` | `{"key": "ArrowDown" / "Enter"}` | Simule la navigation au clavier pour la télécommande |
