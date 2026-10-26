# 📱 Dispositif AlternIA — Module Device (Interface & Matériel)

Le dossier **`device`** regroupe l'ensemble des composants logiciels et matériels formant le terminal interactif d'AlternIA mis entre les mains de l'élève ou projeté en classe.

Il fait le pont temps réel entre :
- **L'élève** (interactions vocales, tactiles ou boutons physiques).
- **L'interface utilisateur** (affichage Kiosk HDMI TV et portail Web sur smartphone).
- **Le matériel physique** (Raspberry Pi 5, micro numérique I2S, ampli I2S, boutons poussoirs, LED tricolore).
- **Le moteur d'intelligence artificielle** (Backend FastAPI & AI-Engine RAG/Socratique).

---

## 🏗️ Architecture Globale du Dispositif

```text
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                           EXPÉRIENCE APPRENANT                              │
 │                                                                             │
 │     [ Grand Écran TV HDMI ]               [ Smartphone Élève (Wi-Fi) ]      │
 │   Chromium Kiosk Plein Écran             Portail Web captif Alta-box1       │
 │   Affichage socratique & Ondes           Interface tactile responsive       │
 └───────────────────────▲───────────────────────────────▲─────────────────────┘
                         │                               │
                         │ HTTP / WebSocket (/ws/device) │
                         ▼                               ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                         FRONTEND DU DISPOSITIF                              │
 │                       (dossier: device/frontend)                            │
 │                                                                             │
 │   • app.js : Orchestrateur Kiosk, cycle de vie & navigation                 │
 │   • device-sync.js : Synchronisation temps réel des boutons & micro         │
 │   • vortex.js & audio.js : Visualiseur d'ondes audio et Hub interactif      │
 │   • katex-renderer.js : Rendu des formules mathématiques et scientifiques   │
 │   • curriculum.js : Arborescence officielle du programme scolaire malien    │
 └───────────────────────────────────────▲─────────────────────────────────────┘
                                         │
                                         │ WebSocket / Événements matériels
                                         ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                     COUCHE MATÉRIELLE & CONTRÔLEUR                          │
 │              (dossier: device/hardware & raspberry-pi/hardware)             │
 │                                                                             │
 │   • 4 Boutons Physiques : Cycles, niveaux et micro Push-to-Talk             │
 │   • LED Tricolore RGB : Signalétique d'état (vert, bleu, rouge, violet...)  │
 │   • Audio I2S Duplex : Micro INMP441 & DAC Ampli MAX98357A                  │
 │   • Streaming audio phrase par phrase & interruption instantanée (barge-in) │
 └─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 Organisation des Sous-Dossiers

### 1. [`frontend/`](file:///Users/ibrahimsorydiallo/Desktop/OSC/AlternIA/device/frontend/)
Application web monopage (SPA) ultra-rapide et légère conçue en Vanilla JavaScript, HTML5 et CSS moderne.
- **Double mode automatique** : Mode TV Kiosk grand écran (adapté aux télévisions 1080p en classe) et Mode Mobile / Tablette (pour les smartphones connectés au Wi-Fi `Alta-box1`).
- **Synchronisation matérielle** : L'interface reflète instantanément tout appui sur les boutons physiques du boîtier (changement de niveau visuel, pulsation micro lors de l'enregistrement, badge de source du manuel RAG).
- **Rendu scientifique** : Support des expressions mathématiques et physiques grâce à KaTeX.

👉 *Voir la documentation complète dans [`frontend/README.md`](file:///Users/ibrahimsorydiallo/Desktop/OSC/AlternIA/device/frontend/README.md).*

### 2. [`hardware/`](file:///Users/ibrahimsorydiallo/Desktop/OSC/AlternIA/device/hardware/)
Spécifications, contrats d'interface et abstraction du matériel physique.
- Découplage strict : le code matériel ne prend aucune décision pédagogique. Il capte les signaux (boutons, microphone), pilote les actionneurs (haut-parleur, LED) et transmet des événements JSON structurés.
- L'implémentation opérationnelle sur Raspberry Pi 5 se situe dans [`raspberry-pi/hardware`](file:///Users/ibrahimsorydiallo/Desktop/OSC/AlternIA/raspberry-pi/hardware).

👉 *Voir la documentation complète dans [`hardware/README.md`](file:///Users/ibrahimsorydiallo/Desktop/OSC/AlternIA/device/hardware/README.md).*

---

## ⚡ Flux de Fonctionnement Nominal

1. **Démarrage** : Le boîtier démarre, le Kiosk Chromium s'ouvre sur la télévision en affichant l'écran d'accueil avec l'horloge et la sélection de niveau.
2. **Choix du niveau** : L'élève appuie sur un bouton physique (ex: Bouton 2 pour la 10ème année) ou touche l'écran tactile ➔ L'interface TV s'anime, la LED passe en bleu royal et une annonce vocale confirme le choix.
3. **Prise de parole** : L'élève appuie sur le bouton micro (Bouton 4) ➔ La LED clignote en rouge vif, le visualiseur d'ondes s'active sur la TV et le microphone I2S enregistre la question.
4. **Réflexion & Streaming** : L'élève relâche le bouton ➔ La LED pulse en violet. Dès que la 1ère phrase de réponse est générée (~2s), la voix commence à sortir sur le haut-parleur (LED en cyan scintillant) et le texte socratique s'affiche étape par étape sur la TV.
5. **Barge-in** : Si l'élève réappuie sur le bouton micro pendant la réponse, la synthèse vocale s'arrête net et le système se remet immédiatement à l'écoute.
