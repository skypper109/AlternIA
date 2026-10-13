# 🇲🇱 AlternIA Box — Guide d'Installation et Configuration sur Raspberry Pi 3

Ce dossier contient l'ensemble des modules logiciels, pilotes GPIO et scripts d'installation nécessaires pour transformer un **Raspberry Pi 3 (Model B / B+)** en boîtier éducatif physique **AlternIA Box**.

Le boîtier permet aux élèves des cycles **Fondamental** (6ème, 7ème, 8ème, 9ème DEF) et **Lycée** (10ème, 11ème, Terminale BAC) d'interagir vocalement avec **ALTA**, leur tuteur pédagogique intelligent, grâce à des boutons physiques, un microphone et des voyants LEDs interactifs.

---

## 📋 Table des Matières

1. [Architecture & Spécificités du Raspberry Pi 3](#1-architecture--spécificités-du-raspberry-pi-3)
2. [Matériel Requis](#2-matériel-requis)
3. [Schéma de Câblage GPIO & Table des Broches](#3-schéma-de-câblage-gpio--table-des-broches)
4. [Installation du Système (Raspberry Pi OS)](#4-installation-du-système-raspberry-pi-os)
5. [Configuration Audio ALSA (Microphone & Haut-Parleur)](#5-configuration-audio-alsa)
6. [Installation des Dépendances (Pas à Pas)](#6-installation-des-dépendances)
7. [Configuration de l'Appareil (`config.py`)](#7-configuration-de-lappareil)
8. [Tests & Diagnostics Matériels](#8-tests--diagnostics-matériels)
9. [Lancement & Utilisation](#9-lancement--utilisation)
10. [Démarrage Automatique au Boot (Service systemd)](#10-démarrage-automatique-au-boot)
11. [Mode Kiosk Écran Tactile (Optionnel)](#11-mode-kiosk-écran-tactile)
12. [Dépannage & FAQ](#12-dépannage--faq)

---

## 1. Architecture & Spécificités du Raspberry Pi 3

Le **Raspberry Pi 3** dispose d'un processeur **Quad-Core ARM Cortex-A53 (1.2 GHz)** et d'une mémoire vive de **1 Go de RAM LPDDR2**.

En raison de la limite de 1 Go de RAM :
* **Architecture Client Connecté (Recommandée)** : Le Raspberry Pi 3 pilote le matériel (GPIO, LEDs, capture micro ALSA, haut-parleurs) et communique en temps réel via API REST / WebSocket avec le serveur AlternIA (exécuté sur un PC local, un serveur d'école, ou dans le Cloud).
* **Traitement Audio Léger** : La capture se fait nativement via `arecord` (sans surcharge CPU/RAM) et la synthèse locale peut utiliser `espeak-ng` ou le flux audio haute définition retourné par le serveur AlternIA.

---

## 2. Matériel Requis

| Composant | Quantité | Description / Recommandation |
| :--- | :---: | :--- |
| **Raspberry Pi 3** | 1 | Modèle 3B ou 3B+ avec carte micro-SD (16 Go ou 32 Go classe 10). |
| **Alimentation** | 1 | Alimentation micro-USB 5V / 2.5A stable (indispensable pour éviter le sous-voltage). |
| **Microphone USB** | 1 | Micro cravate USB ou micro de conférence USB (Plug & Play UAC). |
| **Haut-parleur** | 1 | Enceinte branchée sur la prise Jack 3.5mm ou haut-parleur USB amplifié. |
| **Boutons Poussoirs** | 4 à 6 | Boutons poussoirs momentanés normalement ouverts (NO). |
| **LEDs d'état (5mm)** | 3 | 1 Verte (Prêt), 1 Bleue (Micro), 1 Rouge (Erreur). |
| **Résistances** | 3 | 220 Ω ou 330 Ω (protection des LEDs). |
| **Fils de prototypage** | ~15 | Fils de liaison Dupont femelle-femelle / mâle-femelle. |
| **Écran (Optionnel)** | 1 | Écran officiel tactile Raspberry Pi 7" ou écran HDMI (pour mode Kiosk). |

---

## 3. Schéma de Câblage GPIO & Table des Broches

Toutes les entrées boutons utilisent les **résistances de tirage PULL-UP internes** du microcontrôleur BCM2837.  
Chaque bouton a simplement une broche connectée au **GPIO** et l'autre reliée à la **Masse (GND)**. Aucun composant externe supplémentaire n'est requis pour les boutons !

### Table d'Assignation des Broches (Schéma BCM)

| Fonction | Nom du Signal | Broche Physique (Pin #) | Broche BCM (Code) | Connexion Électrique |
| :--- | :--- | :---: | :---: | :--- |
| **Bouton 1** | Classe 1 (6e Fond. / 10e Lycée) | **Pin 11** | `GPIO 17` | Vers Bouton -> Vers GND (Pin 9) |
| **Bouton 2** | Classe 2 (7e/8e Fond. / 11e Lycée) | **Pin 13** | `GPIO 27` | Vers Bouton -> Vers GND (Pin 14) |
| **Bouton 3** | Classe 3 (9e DEF / Terminale BAC) | **Pin 15** | `GPIO 22` | Vers Bouton -> Vers GND (Pin 20) |
| **Bouton 4 (Micro)** | Push-To-Talk (Parler avec ALTA) | **Pin 16** | `GPIO 23` | Vers Bouton -> Vers GND (Pin 25) |
| **Bouton Cycle** *(Option)* | Bascule Fondamental <-> Lycée | **Pin 32** | `GPIO 12` | Vers Bouton -> Vers GND (Pin 30) |
| **Bouton Extinction** | Arrêt Sécurisé (3 secondes) | **Pin 37** | `GPIO 26` | Vers Bouton -> Vers GND (Pin 39) |
| **LED Verte** | Voyant "Prêt / Veille" | **Pin 18** | `GPIO 24` | Anode (+) -> Résistance 220Ω -> GND |
| **LED Bleue** | Voyant "Micro Ouvert / Écoute" | **Pin 22** | `GPIO 25` | Anode (+) -> Résistance 220Ω -> GND |
| **LED Rouge** | Voyant "Erreur / Extinction" | **Pin 12** | `GPIO 18` | Anode (+) -> Résistance 220Ω -> GND |
| **Masse Commune** | Ground | **Pin 6, 9, 14, 20, 25, 30, 34, 39** | `GND` | Masse pour boutons et LEDs |

> **Logique des Boutons selon le Cycle sélectionné :**
> * En **Cycle Fondamental** :
>   * Bouton 1 = **6ème Année** (1er Cycle)
>   * Bouton 2 = **8ème Année** (2ème Cycle)
>   * Bouton 3 = **9ème Année (DEF)** (Examen National)
> * En **Cycle Lycée** :
>   * Bouton 1 = **10ème Année** (Tronc Commun)
>   * Bouton 2 = **11ème Année** (Sciences / Lettres)
>   * Bouton 3 = **12ème Année (Terminale)** (Baccalauréat)
> * Le Bouton Micro (GPIO 23) active l'enregistrement vocal dans les deux modes.

---

## 4. Installation du Système (Raspberry Pi OS)

1. Téléchargez et installez **[Raspberry Pi Imager](https://www.raspberrypi.com/software/)** sur votre ordinateur.
2. Insérez votre carte micro-SD.
3. Choisissez l'OS :
   * **Recommandé (Mode Boîtier Audio / Léger)** : `Raspberry Pi OS (Legacy, 32-bit ou 64-bit) Lite`.
   * **Recommandé (Mode Écran Kiosk Tactile)** : `Raspberry Pi OS with Desktop`.
4. Cliquez sur la roue crantée (Paramètres avancés) :
   * Activez **SSH** (avec mot de passe ou clé publique).
   * Nom d'utilisateur : `pi` (ou votre choix).
   * Configurez le Wi-Fi local et le fuseau horaire.
5. Gravez la carte et insérez-la dans le Raspberry Pi 3.
6. Connectez-vous en SSH depuis votre terminal :
   ```bash
   ssh pi@raspberrypi.local
   ```

---

## 5. Configuration Audio ALSA

### Vérification du Microphone USB
Connectez votre microphone USB sur l'un des ports du Pi 3 et vérifiez qu'il est reconnu :
```bash
arecord -l
```
Vous devriez voir une ligne du type :
```text
card 1: Device [USB PnP Audio Device], device 0: USB Audio [USB Audio]
```

### Vérification de la Sortie Audio (Haut-parleur)
```bash
aplay -l
```

### Réglage du Volume et du Gain Micro
Si le son enregistré est trop faible, lancez l'utilitaire de mixage :
```bash
alsamixer
```
* Appuyez sur `F6` pour choisir votre carte son USB.
* Appuyez sur `F4` pour régler le niveau de capture du micro (mettez-le à ~80-90%).
* Appuyez sur `Échap` pour quitter, puis sauvegardez les niveaux :
```bash
sudo alsactl store
```

---

## 6. Installation des Dépendances

Transférez ce dossier sur votre Raspberry Pi (par exemple dans `/home/pi/alternia-rpi`) via `scp` ou `git clone` :
```bash
scp -r AlternIA/raspberry-pi pi@raspberrypi.local:/home/pi/alternia-rpi
```

Connectez-vous sur le Raspberry Pi :
```bash
cd /home/pi/alternia-rpi
```

### Méthode 1 : Installation Automatique (Recommandée)
Lancez simplement le script tout-en-un :
```bash
chmod +x install.sh
./install.sh
```
Ce script installe les paquets APT nécessaires (`alsa-utils`, `python3-rpi.gpio`, `portaudio`, `mpg123`, `espeak-ng`), crée l'environnement virtuel Python (`venv`), installe les dépendances pip et vous propose d'activer le démarrage automatique.

---

### Méthode 2 : Installation Manuelle Étape par Étape

Si vous préférez installer manuellement :

1. **Mise à jour des dépôts et paquets système** :
   ```bash
   sudo apt update && sudo apt install -y \
       python3 python3-pip python3-venv python3-dev python3-rpi.gpio \
       alsa-utils libasound2-dev portaudio19-dev libportaudio2 \
       mpg123 espeak-ng curl git
   ```

2. **Ajout de l'utilisateur aux groupes matériels** :
   ```bash
   sudo usermod -a -G audio,gpio $USER
   ```

3. **Création de l'environnement virtuel Python** :
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

4. **Installation des bibliothèques Python** :
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

## 7. Configuration de l'Appareil (`config.py`)

Éditez le fichier `config.py` ou définissez les variables d'environnement correspondantes :
```bash
nano config.py
```

* **`SERVER_URL`** : Adresse IP ou nom de domaine de votre serveur AlternIA.
  * Si le serveur tourne sur un PC du même réseau Wi-Fi :  
    `SERVER_URL = "http://192.168.1.50:8000"`
  * Si le serveur tourne en local sur le Pi :  
    `SERVER_URL = "http://127.0.0.1:8000"`
* **`DEFAULT_CYCLE`** : `"fondamental"` ou `"lycee"`.
* **`DEFAULT_CLASS`** : `"6eme"`, `"7eme"`, `"8eme"`, `"9eme"`, `"10eme"`, `"11eme"`, `"12eme"`.
* **`DEFAULT_SCHOOL`** : Nom de votre école ou établissement scolaire malien (ex : `"École Fondamentale Mamadou Konaté (Bamako)"`).

---

## 8. Tests & Diagnostics Matériels

Avant de fixer le Raspberry Pi dans son boîtier définitif, validez le bon fonctionnement avec les deux outils de diagnostic fournis :

### 1. Test des Boutons et des LEDs
```bash
./venv/bin/python3 test_gpio.py
```
* Les 3 LEDs vont clignoter tour à tour (Verte, Bleue, Rouge).
* Appuyez ensuite sur chaque bouton physique : le terminal affichera instantanément quel bouton a été déclenché.

### 2. Test du Micro et des Haut-Parleurs
```bash
./venv/bin/python3 test_audio.py
```
* Parlez pendant 3 secondes dans le micro USB.
* Le script réécoute immédiatement votre enregistrement sur le haut-parleur pour vérifier la clarté et le volume.

---

## 9. Lancement & Utilisation

Pour lancer l'application en mode console :
```bash
./venv/bin/python3 rpi_client.py
```

### Commandes Physiques :
1. **Sélection de classe** : Cliquez sur les Boutons 1, 2 ou 3. Le boîtier annonce vocalement la classe sélectionnée et synchronise l'état avec le serveur.
2. **Bascule de cycle** : Appuyez sur le Bouton Cycle (GPIO 12) pour basculer instantanément entre le cycle Fondamental et le cycle Lycée.
3. **Poser une question** : 
   * Maintenez le **Bouton Micro (Bouton 4)** enfoncé. La LED bleue s'allume.
   * Posez votre question au tuteur (*« ALTA, explique-moi le théorème de Thalès »*, *« Comment équilibrer cette réaction chimique ? »*).
   * Relâchez le bouton. La LED cyan s'allume (analyse RAG).
   * ALTA répond vocalement sur les haut-parleurs !
4. **Arrêt sécurisé** : Maintenez le Bouton d'Extinction (GPIO 26) pendant 3 secondes pour éteindre proprement le système.

---

## 10. Démarrage Automatique au Boot (Service systemd)

Pour que l'AlternIA Box démarre automatiquement à chaque mise sous tension du Raspberry Pi sans nécessiter de clavier ni d'écran :

1. Copiez le fichier de service :
   ```bash
   sudo cp alternia-box.service /etc/systemd/system/
   ```
2. Rechargez systemd et activez le service :
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable alternia-box.service
   sudo systemctl start alternia-box.service
   ```
3. Vérifiez l'état du service :
   ```bash
   sudo systemctl status alternia-box.service
   ```
4. Pour consulter les logs en temps réel :
   ```bash
   journalctl -u alternia-box.service -f
   ```

---

## 11. Mode Kiosk Écran Tactile (Optionnel)

Si vous avez connecté un écran HDMI ou l'écran tactile officiel 7" au Raspberry Pi 3, vous pouvez lancer l'interface Kiosk en plein écran :

1. Démarrez le bureau graphique X11.
2. Lancez le script Kiosk :
   ```bash
   chmod +x start_kiosk.sh
   ./start_kiosk.sh
   ```
3. Pour le lancer automatiquement au démarrage du bureau, ajoutez la ligne suivante à `~/.config/lxsession/LXDE-pi/autostart` :
   ```bash
   @/home/pi/alternia-rpi/start_kiosk.sh
   ```

---

## 12. Dépannage & FAQ

### Le son est inaudible ou le micro ne capte rien
* Tapez `alsamixer`, choisissez la carte son avec `F6`, puis appuyez sur `F4` pour monter la sensibilité de capture du microphone.
* Testez l'enregistrement avec `./venv/bin/python3 test_audio.py`.

### Erreur `RPi.GPIO: No access to /dev/mem`
* Ajoutez votre utilisateur au groupe `gpio` :
  ```bash
  sudo usermod -a -G gpio $USER
  ```
* Redémarrez la session ou le Raspberry Pi.

### Le Raspberry Pi 3 redémarre tout seul lors de l'enregistrement
* C'est le signe d'une **alimentation insuffisante** (symbole d'éclair jaune à l'écran). Utilisez une alimentation 5V certifiée d'au moins 2.5A.

### Comment changer le nom de l'école ?
* Modifiez `DEFAULT_SCHOOL` dans `config.py` ou exportez la variable d'environnement :
  ```bash
  export ALTERNIA_DEFAULT_SCHOOL="Lycée Askia Mohamed (Bamako)"
  ```
