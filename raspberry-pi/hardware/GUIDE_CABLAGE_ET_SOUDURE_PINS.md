# 🇲🇱 Guide Officiel de Câblage, Broches (Pins) & Soudure — AlternIA Box (Raspberry Pi 5)

Ce document récapitule l'intégralité du plan de câblage électronique et de soudure pour l'assemblage physique du boîtier **ALTA (Cyber-Bloc v2)**. Conservez ce guide à portée de main lors de vos séances de soudure.

---

## 📌 1. Schéma Complet du Connecteur GPIO 40 Broches (Raspberry Pi 5)

```text
                             CONNECTEUR 40 BROCHES (VUE DE DESSUS)
                                (Broche 1 = En haut à gauche)

         Alimentation 3.3V  [  1 ] [  2 ]  Alimentation 5V (Alim MAX98357A)
          SDA (I2C Option)  [  3 ] [  4 ]  Alimentation 5V
          SCL (I2C Option)  [  5 ] [  6 ]  MASSE GND (Masse MAX98357A)
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

| Composant | Broche Composant | Broche Physique Pi 5 | Nom GPIO (BCM) | Type / Signal | Remarques de soudure |
| :--- | :--- | :---: | :---: | :--- | :--- |
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
