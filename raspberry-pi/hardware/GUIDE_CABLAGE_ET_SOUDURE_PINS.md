# 🇲🇱 Guide Officiel de Câblage, Broches (Pins) & Soudure — AlternIA Box (Raspberry Pi 5)

Ce document récapitule l'intégralité du plan de câblage électronique et de soudure pour l'assemblage physique du boîtier **ALTA (Cyber-Bloc v2)**. Conservez ce guide à portée de main lors de vos séances de soudure.

---

## 📌 1. Schéma Complet du Connecteur GPIO 40 Broches (Raspberry Pi 5)

```text
                             CONNECTEUR 40 BROCHES (VUE DE DESSUS)
                                 (Broche 1 = En haut à gauche)

         Alimentation 3.3V  [  1 ] [  2 ]  Alimentation +5V (Alim MAX98357A / Entrée Alim Batterie Pi 5)
          SDA (I2C Option)  [  3 ] [  4 ]  Alimentation +5V (Optionnelle)
          SCL (I2C Option)  [  5 ] [  6 ]  MASSE GND (Masse MAX98357A / Masse Batterie Pi 5)
                GPIO 4      [  7 ] [  8 ]  GPIO 14 (TX UART)
             MASSE GND      [  9 ] [ 10 ]  GPIO 15 (RX UART)
LED Rouge R (GPIO 17)       [ 11 ] [ 12 ]  I2S BCLK Clock (GPIO 18) ── Vers MAX98357A & INMP441
LED Vert G  (GPIO 27)       [ 13 ] [ 14 ]  MASSE GND (Cathode LED RGB)
LED Bleu B  (GPIO 22)       [ 15 ] [ 16 ]  GPIO 23
         Alimentation 3.3V  [ 17 ] [ 18 ]  GPIO 24
                GPIO 10     [ 19 ] [ 20 ]  MASSE GND
                GPIO 9      [ 21 ] [ 22 ]  GPIO 25
                GPIO 11     [ 23 ] [ 24 ]  GPIO 8
             MASSE GND      [ 25 ] [ 26 ]  GPIO 7
             ID_SD (EEPROM) [ 27 ] [ 28 ]  ID_SC (EEPROM)
Bouton 1 Niv 1 (GPIO 5)     [ 29 ] [ 30 ]  MASSE GND (Masse Bouton 1 & INMP441)
Bouton 2 Niv 2 (GPIO 6)     [ 31 ] [ 32 ]  GPIO 12
Bouton 3 Niv 3 (GPIO 13)    [ 33 ] [ 34 ]  MASSE GND (Masse Bouton 2)
I2S LRCLK Word (GPIO 19)    [ 35 ] [ 36 ]  GPIO 16
Bouton 4 Micro (GPIO 26)    [ 37 ] [ 38 ]  I2S Micro Data IN (GPIO 20) ── Vers INMP441 SD
             MASSE GND      [ 39 ] [ 40 ]  I2S DAC Data OUT (GPIO 21) ── Vers MAX98357A DIN
```

---

## 📋 2. Tableau Général des Connexions

| Composant | Broche Composant | Destination (Pi 5 ou Module) | Nom GPIO / Signal | Type / Rôle | Remarques de soudure |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **🔋 Pack 2x 18650** | **Fil Rouge (+)** | **Pastille B+ (Module Boost)** | BAT+ (7.4V ou 3.7V)| Alimentation brute | **Ne PAS brancher sur le Pi 5 !** Se soude sur le module régulateur. |
| | **Fil Noir (-)** | **Pastille B- (Module Boost)** | BAT- (Masse Accus) | Masse batterie | Se soude sur la pastille négative du module BMS/Boost. |
| **⚡ Module Boost 5V** | Entrée B+ / B- | Sortie du pack 18650 | Entrée Accus | Charge & Régulation | Convertit la tension des accus en **5.0V stable (3A-5A)** |
| | Sortie VOUT+ (+5V)| **Borne C (Bouton Power)** | +5V régulé | Ligne d'alim commutée | Fil rouge vers l'interrupteur On/Off |
| | Sortie VOUT- (GND)| **Pin 6 (GND)** ou Masse USB-C | GND (Masse générale)| Masse continue | Relié à la masse commune du Raspberry Pi 5 |
| | Port USB-C recharge| Flanc externe boîtier | Entrée 5V chargeur | Port de charge | Permet de recharger la batterie sans ouvrir le boîtier |
| **🔘 Bouton Power Ø16mm**| Borne C (Commun) | Sortie VOUT+ du module | Entrée +5V continu | Commutateur | Arrivée du 5V régulé |
| | Borne NO (Travail) | **Pin 2 (+5V)** ou USB-C Pi 5| Sortie +5V commuté | Alimentation ON | Envoie le +5V au Pi 5 uniquement quand le bouton est enfoncé |
| | Borne + (LED Anneau)| Pont vers Borne NO | Témoin ON/OFF | Allumage anneau LED | L'anneau bleu/blanc s'allume quand la box démarre |
| | Borne - (LED Anneau)| **Pin 6 (GND)** ou VOUT- | Masse LED | Masse anneau LED | Retour à la masse commune |
| **Bouton 1** (Niveau 1) | Patte Signal | **Pin 29** | **GPIO 5** | Entrée PULL-UP | Pull-up interne active (pas de résistance externe requise) |
| | Patte Masse | **Pin 30** | GND | Masse | Relier à GND |
| **Bouton 2** (Niveau 2) | Patte Signal | **Pin 31** | **GPIO 6** | Entrée PULL-UP | Pull-up interne active |
| | Patte Masse | **Pin 34** | GND | Masse | Relier à GND |
| **Bouton 3** (Niveau 3) | Patte Signal | **Pin 33** | **GPIO 13** | Entrée PULL-UP | Pull-up interne active |
| | Patte Masse | **Pin 39** | GND | Masse | Relier à GND |
| **Bouton 4** (Micro Toggle)| Patte Signal | **Pin 37** | **GPIO 26** | Entrée PULL-UP | Pull-up interne active |
| | Patte Masse | **Pin 39** | GND | Masse | Partage la masse avec Pin 39 |
| **LED Tricolore** | Canal Rouge (R) | **Pin 11** | **GPIO 17** | Sortie PWM | **Résistance 220Ω ou 330Ω obligatoire en série** |
| | Canal Vert (G) | **Pin 13** | **GPIO 27** | Sortie PWM | **Résistance 220Ω ou 330Ω obligatoire en série** |
| | Canal Bleu (B) | **Pin 15** | **GPIO 22** | Sortie PWM | **Résistance 220Ω ou 330Ω obligatoire en série** |
| | Cathode Commune (-) | **Pin 9 ou 14**| GND | Masse Commune | Patte la plus longue de la LED |
| **Ampli MAX98357A** | VIN (+) | **Pin 2 ou 4** | +5V | Alimentation 5V | Fournit la puissance audio |
| | GND (-) | **Pin 6** | GND | Masse Audio | |
| | BCLK (Bit Clock) | **Pin 12** | **GPIO 18** | Horloge I2S | Fil commun partagé avec INMP441 SCK |
| | LRC (LRCLK / WS) | **Pin 35** | **GPIO 19** | Synchro I2S | Fil commun partagé avec INMP441 WS |
| | DIN (Data In) | **Pin 40** | **GPIO 21** | Données Audio Out| Signal numérique envoyé au haut-parleur |
| | GAIN | — | GND ou Libre | Réglage gain | Non relié = 12dB (recommandé), à GND = 9dB |
| **Haut-Parleur (4Ω 3W)**| Borne + | Bornier MAX + | Audio Out + | Sortie amplifiée | Relié au fil rouge du baffle 70×31 mm |
| | Borne - | Bornier MAX - | Audio Out - | Sortie amplifiée | Relié au fil noir du baffle 70×31 mm |
| **Micro I2S INMP441** | VDD (+) | **Pin 1 ou 17**| **+3.3V** | Alimentation 3.3V | **Attention : Ne JAMAIS brancher sur 5V !** |
| | GND (-) | **Pin 25 ou 30**| GND | Masse | |
| | SCK (Serial Clock) | **Pin 12** | **GPIO 18** | Horloge I2S | Soudé en parallèle avec BCLK du MAX98357A |
| | WS (Word Select) | **Pin 35** | **GPIO 19** | Synchro I2S | Soudé en parallèle avec LRC du MAX98357A |
| | SD (Serial Data) | **Pin 38** | **GPIO 20** | Données Audio In | Signal voix capté par le micro |
| | L/R (Canal) | Patte GND micro | GND | Sélection canal | À souder sur GND pour le canal gauche |

---

## 🔍 3. Détail Pas-à-Pas par Sous-Système

### A. Les 4 Boutons Poussoirs Tactiles (N1 à N4)
Les boutons se montent en contact sec direct entre le GPIO et la masse GND :
* **Aucune résistance externe nécessaire** : Le logiciel configure automatiquement les résistances de tirage vers le haut internes (*internal pull-up*) du processeur BCM2712 du Pi 5.
* **Fonctionnement :** 
  * Bouton relâché ➔ Entrée à 3.3V (Niveau HAUT / 1)
  * Bouton pressé ➔ Entrée à 0V (Niveau BAS / 0)

### B. La LED Tricolore RVB (Indicateur d'État)
* **Identification des 4 pattes de la LED (Cathode Commune) :**
  1. Patte 1 (à gauche de la patte la plus longue) : **Rouge (R)**
  2. Patte 2 (la plus longue) : **Masse GND (Cathode)**
  3. Patte 3 : **Vert (G)**
  4. Patte 4 : **Bleu (B)**
* **Résistances de protection indispensables :**  
  Soudez une résistance de **220 Ω** (ou 330 Ω) sur chacune des 3 pattes d'anode (R, G, B) pour ne pas griller les GPIOs du Pi 5.

### C. La Chaîne Audio Sortie : Amplificateur I2S MAX98357A & Haut-Parleur
* **Alimentation :** Reliez la broche `VIN` du MAX98357A sur le **+5V (Pin 2)** pour obtenir les 3.2W de puissance dans le haut-parleur.
* **Haut-Parleur :** Reliez les deux sorties du bornier à vis (`+` et `-`) aux deux fils du haut-parleur à cavité rectangulaire 4Ω 3W/5W (70 mm × 31 mm).
* **Gain audio :** Laissez la broche `GAIN` non connectée (en l'air) : le module active un gain par défaut de **12 dB**, parfait pour une voix claire et audible dans une salle de classe.

### D. Le Microphone MEMS INMP441 (Entrée Vocale)
* **Partage d'horloge I2S :**  
  Le microphone et l'amplificateur utilisent le même bus I2S matériel :
  * Le signal d'horloge **BCLK (Pin 12 / GPIO 18)** va à la fois sur `BCLK` du MAX98357A et sur `SCK` de l'INMP441.
  * Le signal de synchronisation **LRCLK (Pin 35 / GPIO 19)** va à la fois sur `LRC` du MAX98357A et sur `WS` de l'INMP441.
  * Seules les lignes de données sont séparées : **GPIO 21 (Pin 40)** pour la sortie HP (`DIN`), et **GPIO 20 (Pin 38)** pour l'entrée Micro (`SD`).
* **Broche L/R :** Soudez un petit pont entre `L/R` et la broche `GND` de la plaquette du micro pour sélectionner le canal audio gauche.

---

### E. Système d'Alimentation : Pack Batterie 2× 18650, Module Boost 5V & Bouton Power Ø16mm

> [!CAUTION]
> **⚠️ ATTENTION — PIÈGE DU CONNECTEUR "BAT" DU RASPBERRY PI 5 :**
> * Le Raspberry Pi 5 possède un minuscule connecteur blanc à 2 broches marqué **"BAT"** situé près de la prise HDMI / bouton d'allumage natif.
> * **CE CONNECTEUR N'EST PAS UNE ENTRÉE POUR VOTRE PACK BATTERIE !** Il est uniquement conçu pour une pile bouton RTC rechargeable 3V (horloge temps réel de veille).
> * **Ne branchez JAMAIS votre pack 18650 sur ce port**, cela détruirait instantanément la puce de gestion d'énergie (PMIC) du Pi 5 !

---

#### 1. Où se branchent EXACTEMENT les fils de la batterie ?

Le Raspberry Pi 5 **ne possède pas de circuit de charge de batterie intégré**. Vos accus 18650 ne se connectent donc **JAMAIS directement** au Pi 5.

Ils se branchent sur une carte intermédiaire indispensable : le **Module de Gestion & Charge BMS avec Convertisseur Élévateur 5V (Step-Up / Boost 5V 3A à 5A)** (ex: carte PowerBoost, module IP5310/IP5328 ou carte d'extension UPS HAT).

```text
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                    CARTE ÉLECTRONIQUE MODULE BOOST 5V / BMS                 │
 │                                                                             │
 │  [ Port USB-C Extérieur ]                                                   │
 │  (Pour recharger la batterie)                                               │
 │                                                                             │
 │  PASTILLES D'ENTRÉE BATTERIE :                                              │
 │  [  B+  ] ◄─── SOUDER ICI le FIL ROUGE (+) du Pack Batterie 18650           │
 │  [  B-  ] ◄─── SOUDER ICI le FIL NOIR  (-) du Pack Batterie 18650           │
 │                                                                             │
 │  PASTILLES DE SORTIE 5V RÉGULÉ :                                            │
 │  [ VOUT+ ] ────► Va vers la Borne C (Commun) du Bouton Power Inox Ø16mm     │
 │  [ VOUT- ] ────► Va vers la MASSE GND du Pi 5 (Pin 6 ou Masse USB-C)       │
 └─────────────────────────────────────────────────────────────────────────────┘
```

---

#### 2. Schéma de Câblage Complet : De la Batterie jusqu'au Pi 5

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
              │   │   │                           │
              │   └───┼──► ALIMENTATION +5V :     │
              │       │    • Option A : Fil Rouge sur prise USB-C dénudée
              │       │    • Option B : Fil Rouge soudé sur BROCHE 2 (Pin 2 du GPIO)
              │       │
              └───────┼──► MASSE COMMUNE GND :
                      │    • Option A : Fil Noir sur prise USB-C dénudée
                      │    • Option B : Fil Noir soudé sur BROCHE 6 (Pin 6 du GPIO)
                      └───────────────────────────┘
```

---

#### 3. Câblage Détaillé du Bouton Poussoir Métallique Ø16mm (Interrupteur Power avec Anneau LED)

Le bouton inox Ø16 mm possède **5 broches** sous son embase :
* `C` (Common / Entrée commune)
* `NO` (Normally Open / Contact travail)
* `NC` (Normally Closed / Contact repos — non utilisé, laisser libre)
* `+` (Anode de l'anneau LED du bouton)
* `-` (Cathode de l'anneau LED du bouton)

| Broche Bouton Ø16mm | Origine du fil | Destination du fil | Rôle |
| :--- | :--- | :--- | :--- |
| **Broche C** (Commun) | Sortie `VOUT+` du module Boost 5V | Borne `C` du bouton | Reçoit le +5V permanent de la batterie |
| **Broche NO** (Travail) | Borne `NO` du bouton | **Pin 2 (+5V)** du Pi 5 (ou fil rouge USB-C) | Envoie le 5V au Pi 5 uniquement quand le bouton est enclenché |
| **Broche + (LED Anneau)**| **Pont soudé directement sur Borne NO** | Borne `+` de la LED du bouton | L'anneau lumineux s'allume automatiquement quand la box démarre |
| **Broche - (LED Anneau)**| Sortie `VOUT-` du module ou Masse | **Pin 6 (GND)** du Pi 5 (ou fil noir USB-C) | Retour à la masse commune pour fermer le circuit LED |

---

#### 4. Raccordement Final sur le Raspberry Pi 5 (Où injecter le courant ?)

Vous avez **2 options au choix** pour injecter le 5V issu du bouton Power dans le Pi 5 :

* **Option A — Via un câble USB-C court (Recommandée)** :  
  Prenez un câble USB-C court de bonne qualité, coupez-le pour dénuder les fils internes :
  * Reliez le **fil Rouge (+5V / VBUS)** à la broche `NO` du bouton Power.
  * Reliez le **fil Noir (GND)** à la masse `VOUT-` du module d'alimentation.
  * Branchez la fiche USB-C directement sur le port d'alimentation USB-C natif du Pi 5.  
  *(Avantage : Cette méthode conserve la protection anti-surtension et le fusible électronique officiel du Pi 5).*

* **Option B — Soudure directe sur les broches GPIO du Pi 5** :  
  Si vous préférez un montage interne 100% compact sans prise USB-C encombrante :
  * Soudez le fil positif **+5V commuté** (venant de la broche `NO` du bouton Power) sur la **Broche 2 (Pin 2 — +5V)** du connecteur GPIO.
  * Soudez le fil négatif **GND** (venant de la masse `VOUT-` du module) sur la **Broche 6 (Pin 6 — GND)** du connecteur GPIO.

---

#### 5. Comment Recharger la Batterie ?
Le module Boost intègre une prise USB-C femelle qui s'aligne avec la découpe sur le flanc du boîtier.
* Pour recharger le boîtier : branchez un chargeur de smartphone standard (5V / 2A ou 3A) sur cette prise USB-C externe.
* La batterie se charge que la machine soit éteinte ou allumée.

---

## 🛠️ 4. Conseils Pratiques de Soudure

1. **Section de fil recommandée :**  
   Utilisez du fil souple en silicone multi-brins **AWG 26 ou AWG 28**. Il est flexible et ne risque pas de casser lors de l'assemblage dans le boîtier.
2. **Gaine thermorétractable :**  
   Isolez systématiquement chaque patte de la LED et des résistances avec un morceau de gaine thermorétractable de Ø1.5 mm ou Ø2 mm.
3. **Masse commune en étoile :**  
   Pour simplifier les câblages, vous pouvez relier ensemble les fils de masse des 4 boutons poussoirs sur un seul fil arrivant sur la broche GND (Pin 39).
4. **Précautions antistatiques :**  
   Effectuez les soudures avec le Raspberry Pi **éteint et débranché de toute source d'alimentation**.

---

## 🧪 5. Validation Matérielle Immédiate Après Soudure

Une fois vos soudures terminées, allumez votre Raspberry Pi 5 et lancez le script de validation intégré :

```bash
python3 /home/ubuntu/Alternia/raspberry-pi/hardware/test_hardware.py
```

Ce script interactif teste automatiquement :
1. 🔊 L'émission d'un bip sonore 440 Hz sur le **haut-parleur**.
2. 🎙️ L'enregistrement et la réécoute immédiate sur le **microphone**.
3. 🌈 Le défilement de toutes les couleurs (Rouge, Vert, Bleu, Turquoise, Violet, Cyan) sur la **LED Tricolore**.
4. 🔘 La détection en temps réel de chaque appui sur les **4 Boutons physiques**.
