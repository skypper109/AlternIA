# 🇲🇱 AlternIA Box — Configuration & Guide Raspberry Pi 5 (8 Go RAM)

Ce dossier contient l'infrastructure matérielle, logicielle, audio, réseau et mécanique pour transformer un **Raspberry Pi 5 (8 Go de RAM)** en boîtier éducatif autonome (**Alta-Box**).

Le boîtier assure simultanément :
1. **L'émission d'un point d'accès Wi-Fi autonome** (`Alta-box1`) avec portail captif et redirection automatique vers l'interface élève (`https://device.alterniamali.com` ou miroir local).
2. **L'affichage plein écran Kiosk HDMI TV** (Chromium 1080p) avec pilotage à distance en temps réel par les boutons physiques, le clavier ou la souris.
3. **Le pilotage matériel complet (GPIO)** : 4 boutons poussoirs physiques, une LED tricolore RGB interactive, un DAC amplificateur I2S **MAX98357A** et un microphone numérique I2S **INMP441**.
4. **Un pipeline audio haute performance en streaming par phrase** (~2s de latence au lieu de 20s) avec **interruption vocale immédiate (barge-in)**.
5. **Un cache audio local hors-ligne** pour le message de bienvenue et les annonces vocales de changement de niveau.
6. **L'intégration mécanique et électrique autonome** : alimentation sur pack batterie 2x 18650 avec module BMS Boost 5V, interrupteur bouton poussoir inox Ø16mm avec anneau LED et châssis 3D modélisé (*Cyber Bloc V2*).

---

## 📋 Table des Matières

1. [Architecture Matérielle & Schéma de Câblage GPIO](#1-architecture-matérielle--schéma-de-câblage-gpio)
2. [Sous-Système Audio I2S & Pipeline Streaming](#2-sous-système-audio-i2s--pipeline-streaming)
3. [Affichage HDMI TV & Mode Kiosk Télécommandé](#3-affichage-hdmi-tv--mode-kiosk-télécommandé)
4. [Alimentation Autonome (Batterie 18650 & Bouton Power)](#4-alimentation-autonome-batterie-18650--bouton-power)
5. [Modélisation & Impression 3D (Boîtier Cyber Bloc V2)](#5-modélisation--impression-3d-boîtier-cyber-bloc-v2)
6. [Système d'Exploitation & Flashage MicroSD](#6-système-dexploitation--flashage-microsd)
7. [Installation & Déploiement Automatisé](#7-installation--déploiement-automatisé)
8. [Réseau Wi-Fi Autonome & Portail Captif](#8-réseau-wi-fi-autonome--portail-captif)
9. [Services Systemd & Commandes de Diagnostic](#9-services-systemd--commandes-de-diagnostic)

---

## 1. Architecture Matérielle & Schéma de Câblage GPIO

Le contrôleur matériel [`hardware/buttons_audio_controller.py`](file:///Users/ibrahimsorydiallo/Desktop/OSC/AlternIA/raspberry-pi/hardware/buttons_audio_controller.py) pilote tous les capteurs, actionneurs et périphériques physiques du boîtier via la bibliothèque `gpiozero` / `libgpiod`.

### 📌 Tableau Récapitulatif des Broches GPIO (Connecteur 40 broches)

| Composant | Signal Composant | Broche Physique Pi 5 | Broche BCM | Description & Rôle |
| :--- | :--- | :---: | :---: | :--- |
| **Bouton 1** | Contact Travail | **Pin 29** | **GPIO 5** | Cycle Niveau 1 (Fondamental : 6e ➔ 7e ➔ 8e ➔ 9e DEF) |
| **Bouton 2** | Contact Travail | **Pin 31** | **GPIO 6** | Cycle Niveau 2 (Secondaire : 10e ➔ 11e) |
| **Bouton 3** | Contact Travail | **Pin 33** | **GPIO 13** | Niveau 3 (Terminale / Baccalauréat) |
| **Bouton 4** | Contact Travail | **Pin 37** | **GPIO 26** | Micro Push-to-Talk / Toggle bistable + Interruption barge-in |
| **Masse Boutons**| Retour commun | **Pin 30, 34, 39** | **GND** | Masse commune raccordée aux boutons (Pull-Up interne actif) |
| **LED Tricolore (R)** | Anode Rouge (220Ω) | **Pin 11** | **GPIO 17** | Canal Rouge (Enregistrement micro / alertes) |
| **LED Tricolore (G)** | Anode Verte (220Ω) | **Pin 13** | **GPIO 27** | Canal Vert (Validation / Fondamental / Prêt) |
| **LED Tricolore (B)** | Anode Bleue (220Ω) | **Pin 15** | **GPIO 22** | Canal Bleu (Secondaire / Réflexion IA / Activité) |
| **LED Cathode** | Retour négatif | **Pin 9** ou **Pin 14** | **GND** | Cathode commune reliée à la masse GND |
| **I2S DAC (MAX98357A)**| **BCLK** (Bit Clock) | **Pin 12** | **GPIO 18** | Horloge partagée avec le micro INMP441 |
| **I2S DAC (MAX98357A)**| **LRC** (Left/Right) | **Pin 35** | **GPIO 19** | Horloge trame partagée avec le micro INMP441 |
| **I2S DAC (MAX98357A)**| **DIN** (Data Out) | **Pin 40** | **GPIO 21** | Données audio sortantes vers l'amplificateur HP 3W/5W |
| **I2S DAC (MAX98357A)**| **VIN / GND** | **Pin 2 / Pin 6** | **+5V / GND**| Alimentation de puissance du DAC |
| **I2S Mic (INMP441)** | **SCK** (Bit Clock) | **Pin 12** | **GPIO 18** | Relié au BCLK partagé |
| **I2S Mic (INMP441)** | **WS** (Word Select)| **Pin 35** | **GPIO 19** | Relié au LRCLK partagé |
| **I2S Mic (INMP441)** | **SD** (Data In) | **Pin 38** | **GPIO 20** | Données numériques captées par le microphone |
| **I2S Mic (INMP441)** | **VDD / GND / L/R** | **Pin 1 / Pin 9** | **3.3V / GND**| Alimentation 3.3V stable (L/R soudé à GND pour canal gauche) |

> 📖 **Guide complet illustré :** Consultez le guide pas à pas avec schémas ASCII et astuces de soudure dans [`hardware/GUIDE_CABLAGE_ET_SOUDURE_PINS.md`](file:///Users/ibrahimsorydiallo/Desktop/OSC/AlternIA/raspberry-pi/hardware/GUIDE_CABLAGE_ET_SOUDURE_PINS.md).

### 🌈 États Lumineux de la LED Tricolore

* 🟢 **Turquoise / Vert Émeraude** : Niveau 1 actif (Fondamental 6e-9e DEF).
* 🔵 **Bleu Royal** : Niveau 2 actif (Secondaire 10e-11e).
* 🟠 **Ambre / Orange Doré** : Niveau 3 actif (Terminale 12e BAC).
* 🔴 **Rouge Vif Pulsant** : Prise de son en cours (microphone ouvert, élève en train de parler).
* 🟣 **Violet Pulsant** : Réflexion IA en cours (STT terminé, inférence et RAG en cours).
* 🌊 **Cyan Scintillant** : Synthèse vocale TTS en cours d'élocution sur le haut-parleur.
* 🔄 **Restauration automatique** : Dès la fin de la parole ou en cas d'interruption, la LED revient à la couleur du niveau actif.

---

## 2. Sous-Système Audio I2S & Pipeline Streaming

### 🔊 Chaîne Matérielle & Horloges Partagées
Le Raspberry Pi 5 ne dispose que d'une seule interface I2S native. L'architecture AlternIA utilise un **bus I2S duplex synchrone** :
- Le signal **BCLK (GPIO 18)** et le signal **LRCLK/WS (GPIO 19)** sont pontés simultanément vers le DAC **MAX98357A** (sortie haut-parleur) et le microphone numérique **INMP441** (entrée vocale).
- Les données sortent sur **GPIO 21 (DIN)** et rentrent sur **GPIO 20 (SD)** sans aucun conflit.
- Le script [`hardware/setup_max98357a_audio.sh`](file:///Users/ibrahimsorydiallo/Desktop/OSC/AlternIA/raspberry-pi/hardware/setup_max98357a_audio.sh) configure automatiquement le driver kernel `dtoverlay=max98357a` dans `/boot/firmware/config.txt`.

### ⚡ Pipeline de Streaming Audio par Phrase (~2s de latence)
Pour éviter que l'élève n'attende 15 à 25 secondes qu'une longue explication pédagogique soit entièrement synthétisée :
1. La réponse textuelle du tuteur socratique est analysée en flux continu et découpée immédiatement à chaque fin de phrase (`.`, `!`, `?`, `;`).
2. Dès que la première phrase pédagogique est prête (~15-20 mots), le moteur génère son audio via le TTS distant haute fidélité (`device/stream-sentence`) et l'envoie au Raspberry Pi.
3. Pendant que le haut-parleur joue la phrase 1, la phrase 2 est générée en arrière-plan dans une file d'attente fluide.
4. **Résultat :** Première voix entendue en **moins de 2 secondes**, tout en conservant l'explication complète et détaillée.

### 🛑 Interruption Vocale Instantanée (Microphone Barge-In)
Si l'élève souhaite couper la parole de l'IA pour poser une nouvelle question ou rectifier son propos :
- Tout nouvel appui sur le **Bouton 4 (Micro)** ou détection vocale déclenche l'arrêt immédiat du processus de lecture (`mpv` / `aplay`).
- La file d'attente des phrases suivantes est vidée instantanément.
- Le micro passe en écoute immédiate avec la LED rouge.

### 💾 Cache Audio Local Hors-Ligne (`hardware/audio_cache/`)
Le dossier [`hardware/audio_cache/`](file:///Users/ibrahimsorydiallo/Desktop/OSC/AlternIA/raspberry-pi/hardware/audio_cache/) contient des fichiers MP3 pré-générés pour une réactivité instantanée sans aucun appel réseau :
- `startup_greeting.mp3` : Annonce d'accueil chaleureuse au démarrage du boîtier.
- `select_class_6eme.mp3` à `select_class_12eme.mp3` : Annonce vocale immédiate lors de chaque appui sur les boutons de sélection de niveau.

---

## 3. Affichage HDMI TV & Mode Kiosk Télécommandé

L'Alta-Box peut être branchée directement sur un téléviseur ou vidéoprojecteur via son port micro-HDMI.

### 🖥️ Kiosk Chromium Plein Écran
Le script [`kiosk/launch_kiosk.sh`](file:///Users/ibrahimsorydiallo/Desktop/OSC/AlternIA/raspberry-pi/kiosk/launch_kiosk.sh) et le service systemd `alta-kiosk.service` lancent Chromium en mode Kiosk 1080p :
```bash
chromium-browser \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --autoplay-policy=no-user-gesture-required \
    --check-for-update-interval=31536000 \
    https://device.alterniamali.com
```
L'option `--autoplay-policy=no-user-gesture-required` assure la restitution vocale immédiate sans nécessiter de clic à la souris sur l'écran.

### 🎮 Contrôle à Distance Temps Réel (Remote Control)
Les boutons physiques du boîtier ne se contentent pas de changer l'état interne : ils pilotent l'interface graphique sur la télévision en temps réel via une liaison WebSocket locale (`/ws/remote`) :
- **Appui Bouton 1 / 2 / 3** : Met à jour visuellement les cartes de classe, les onglets et le programme sur la TV.
- **Appui Bouton 4 (Micro)** : Déclenche l'animation de pulsation et les ondes vocales (Audio Visualizer) à l'écran.
- **Support Clavier & Souris** : Un clavier ou une télécommande sans fil branché sur le Pi 5 permet également de naviguer dans les exercices et d'interagir avec les cartes socratiques.
- Le script [`scripts/setup_hdmi_kiosk.sh`](file:///Users/ibrahimsorydiallo/Desktop/OSC/AlternIA/raspberry-pi/scripts/setup_hdmi_kiosk.sh) configure la résolution HDMI forcée 1080p60 et désactive la mise en veille de l'écran.

---

## 4. Alimentation Autonome (Batterie 18650 & Bouton Power)

Le Raspberry Pi 5 ne disposant pas de chargeur interne, l'alimentation autonome repose sur un circuit sécurisé :

```text
 ┌──────────────────────────┐
 │   Pack 2x Accus 18650    │
 │ (3.7V - 7.4V avec BMS)   │
 └────────────┬─────────────┘
              │  Fil Rouge (+) ──────► Pastille [ B+ ]   ┌──────────────────────────────┐
              │  Fil Noir  (-) ──────► Pastille [ B- ]   │ Module Boost 5V (Charge/Alim)│
              │                                          │ (Entrée charge USB-C externe)│
              │                                          └──────────────┬───────────────┘
              │                                                         │
              │   ┌─────────────────────────────────────────────────────┘
              │   │
              │   ├─► Sortie [ VOUT+ ] (+5V continu)
              │   │         │
              │   │         ▼
              │   │   ┌───────────────────────────┐
              │   │   │  Bouton Power Inox Ø16mm  │  Borne [ C  ] : Entrée +5V continu
              │   │   │  (Interrupteur Marche)    │  Borne [ NO ] : Sortie +5V quand enfoncé
              │   │   └─────────────┬─────────────┘  Borne [ +  ] : Reliée par un pont sur [ NO ]
              │   │                 │                Borne [ -  ] : Reliée à la masse GND
              │   │                 ▼
              │   │          [ +5V COMMUTÉ ]
              │   │                 │
              │   │                 ▼
              │   │   ┌───────────────────────────┐
              │   │   │      Raspberry Pi 5       │
              │   └───┼──► Port USB-C (ou Pin 2)  │
              │       │                           │
              └───────┼──► Masse GND (ou Pin 6)   │
                      └───────────────────────────┘
```

- **Module Boost Step-Up 5V 3A à 5A** avec BMS intégré : recharge via USB-C externe, sortie 5V stabilisée.
- **Bouton Inox Ø16mm étanche avec anneau LED** : allumage de l'anneau lumineux dès que le système est sous tension.

---

## 5. Modélisation & Impression 3D (Boîtier Cyber Bloc V2)

Le dossier [`cad_3d/`](file:///Users/ibrahimsorydiallo/Desktop/OSC/AlternIA/raspberry-pi/cad_3d/) contient tous les fichiers de modélisation pour fabriquer le boîtier physique :
- `alta_cyber_bloc_v2.scad` : Code paramétrique complet OpenSCAD du boîtier modulaire bicolore.
- `generate_3d_stl.py` : Script Python automatisant la compilation des pièces en mesh STL.
- Fichiers STL prêts pour l'impression 3D :
  - `ALTA_Chassis_Inferieur_Bleu.stl` : Bac principal avec entretoises pour le Pi 5, le module Boost et le haut-parleur.
  - `ALTA_Capot_Superieur_Blanc.stl` : Façade supérieure avec découpes pour les 4 boutons, la LED RGB et la grille acoustique.
  - `ALTA_Touches_Boutons_Bleu.stl` : Touches tactiles ergonomiques pour les boutons poussoirs.
  - `ALTA_Bouton_Power_Blanc.stl` : Bague d'adaptation pour le bouton inox Ø16mm.
  - `ALTA_Entourage_Sangle_Blanc.stl` : Passants pour sangle de transport scolaire.
- `GUIDE_SOLIDWORKS_PAS_A_PAS.md` : Guide pas à pas pour importer, modifier et contraindre le modèle dans Dassault Systèmes SolidWorks.

---

## 6. Système d'Exploitation & Flashage MicroSD

Recommandation officielle pour le Raspberry Pi 5 (8 Go) :
* **Raspberry Pi OS (64-bit) with Desktop** *(Debian 12 Bookworm)* : gestion native de Wayland/Labwc pour le mode Kiosk HDMI et support complet des 8 Go de RAM.

Flashage avec **Raspberry Pi Imager** :
1. Sélectionner **Raspberry Pi 5** et **Raspberry Pi OS (64-bit)**.
2. Définir le nom d'hôte : `alta-box1`, utilisateur : `ubuntu`, activer **SSH**.
3. Écrire sur une carte MicroSD de 32 Go ou 64 Go (Classe A2 / U3).

---

## 7. Installation & Déploiement Automatisé

Sur le Raspberry Pi 5 :

```bash
# 1. Cloner le dépôt
cd ~
git clone https://github.com/votre-compte/AlternIA.git
cd AlternIA/raspberry-pi

# 2. Configurer le Hotspot Wi-Fi, Nginx et les services
sudo ./setup_pi5_hotspot.sh

# 3. Configurer l'audio I2S (MAX98357A & INMP441)
sudo ./hardware/setup_max98357a_audio.sh

# 4. Configurer l'affichage Kiosk HDMI TV
sudo ./scripts/setup_hdmi_kiosk.sh

# 5. Tester l'ensemble du matériel
python3 hardware/test_hardware.py
```

---

## 8. Réseau Wi-Fi Autonome & Portail Captif

* **Nom du réseau (SSID)** : `Alta-box1`
* **Mot de passe** : `Bamako+223`
* **Bande Wi-Fi** : `2.4 GHz` (canal 6, portée optimale en milieu scolaire)
* **Passerelle locale** : `10.42.0.1`

Dès qu'un smartphone se connecte :
- La détection de portail captif redirige automatiquement l'élève vers `https://device.alterniamali.com`.
- Le serveur Nginx Edge met en cache local les ressources statiques et retransmet les requêtes API vers le serveur central en contournant le buffering pour le streaming vocal (`X-Accel-Buffering: no`).

---

## 9. Services Systemd & Commandes de Diagnostic

Tous les démons sont monitorés et redémarrés automatiquement par systemd :

```bash
# Vérifier l'état des services
sudo systemctl status alta-hardware alta-kiosk alta-hotspot alta-agent alta-led

# Suivre les logs du contrôleur boutons et audio en temps réel
sudo journalctl -u alta-hardware -f

# Suivre les logs du Kiosk HDMI
sudo journalctl -u alta-kiosk -f

# Vérifier les périphériques audio ALSA
aplay -l
arecord -l

# Vérifier les élèves connectés au Wi-Fi
sudo iw dev wlan0 station dump | grep Station | wc -l
```
