# Guide de Modélisation SolidWorks — ALTA Cyber-Bloc v2 (Spécifications Réelles)

Ce guide détaille la modélisation sous **SolidWorks** de l'ensemble des pièces réelles du **Cyber-Bloc v2** telles que présentées sur votre planche d'atelier (*« Détail des pièces d'impression 3D (Cyber-Bloc v2) »*).

Il intègre rigoureusement :
1. **Tous vos composants électroniques réels :**
   * Raspberry Pi 5 (avec dissipateur actif Active Cooler).
   * Pack Batterie 2× 18650 sous gaine.
   * Module Haut-Parleur ovale noir (4Ω 3W/5W).
   * Carte Ampli DAC I2S verte avec bornier et potentiomètre.
   * Visserie CHC M3 (4 vis d'angle + 1 vis d'étrier) et 4 inserts filetés en laiton M3.
   * Sangle textile tissée bleue.
2. **Le mapping logiciel exact configuré dans `buttons_audio_controller.py` :**
   * **Bouton N1** (GPIO 5, Pin 29) : Niveau 1 — Fondamental (6e -> 7e -> 8e -> 9e DEF)
   * **Bouton N2** (GPIO 6, Pin 31) : Niveau 2 — Secondaire (10e <-> 11e Lycée)
   * **Bouton N3** (GPIO 13, Pin 33) : Niveau 3 — Terminale (BAC)
   * **Bouton N4** (GPIO 26, Pin 37) : Micro Toggle PTT (Enregistrement vocal)
   * **LED RVB d'état** : GPIO 17 (Rouge), 27 (Vert), 22 (Bleu)
   * **Bouton Power (⏻)** : Interrupteur d'allumage général
   * **Audio I2S** : GPIO 18 (BCLK), 19 (LRCLK), 21 (DIN) vers l'ampli MAX98357A
   * **Micro I2S** : GPIO 20 (SD) vers l'INMP441

---

## 📦 1. Nomenclature des Fichiers Pièces SolidWorks

| N° Pièce | Nom du Fichier SolidWorks | Filament / Matériau | Description selon la planche d'atelier |
| :--- | :--- | :--- | :--- |
| **P01** | `ALTA_Capot_Superieur.SLDPRT` | **Filament Blanc** | Capot supérieur biseauté avec grille HP, logo ALTA, fenêtres N1, N2, N3, N4 et deux touches basses. |
| **P02** | `ALTA_Chassis_Inferieur.SLDPRT` | **Filament Bleu Roi** | Cuve inférieure octogonale avec baie des connecteurs Pi 5, bouton Power et berceaux internes. |
| **P03** | `ALTA_Entourage_Sangle.SLDPRT` | **Filament Blanc** | Étrier et passant latéral gauche de sangle (2 éléments d'assemblage). |
| **P04** | `ALTA_Angle_Protection.SLDPRT` | **Filament Blanc** | Bumper / étrier de protection pour le flanc droit. |
| **P05** | `ALTA_Touches_Boutons.SLDPRT` | **Filament Bleu Roi** | Touches carrées gravées N1, N2, N3, N4 et les 2 touches inférieures. |
| **P06** | `ALTA_Bouton_Power.SLDPRT` | **Filament Blanc** | Bouton poussoir d'allumage gravé avec le symbole Power (⏻). |
| **P07** | `ALTA_Grips_Lateraux.SLDPRT` | **Filament Bleu Roi** | 2 patins texturés avec rainures de préhension inclinées à 45°. |
| **ASM** | `ALTA_CyberBloc_v2.SLDASM` | **Assemblage** | Assemblage général complet avec quincaillerie et composants virtuels. |

---

## 🛠️ PARTIE 1 : Le Châssis Inférieur Bleu (`P02_Chassis_Inferieur.SLDPRT`)

### Étape 1.1 : L'enveloppe extérieure octogonale
1. Ouvrir SolidWorks ➔ **Nouveau** ➔ **Pièce**.
2. **Plan de dessus** ➔ Créer une **Esquisse** :
   * Tracer un rectangle par son centre de **208.00 mm (X)** × **114.00 mm (Y)**.
   * Tracer 4 chanfreins d'angle de **18.00 mm × 45°** aux 4 coins (donne la forme biseautée octogonale caractéristique du Cyber-Bloc).
3. Menu **Fonctions** ➔ **Bossage/Base extrudé** :
   * Hauteur : **16.00 mm** vers le haut.
4. Menu **Fonctions** ➔ **Coque (Shell)** :
   * Épaisseur de paroi : **2.50 mm**.
   * Sélectionner la face supérieure pour vider la pièce ➔ Profondeur utile intérieure : **13.50 mm**.

### Étape 1.2 : Les découpes de la Façade Avant (Connecteurs Pi 5 & Bouton Power)
1. Sélectionner la **face extérieure avant** ($Y = 0$) ➔ Créer une **Esquisse** (`Ctrl + 8`).
2. Tracer une ligne de référence à **3.00 mm** du fond intérieur (hauteur des plots du Pi 5).
3. Dessiner de gauche à droite :
   * **Orifice LED RVB Tricolore :** Cercle de **Ø3.20 mm** à $X = 22.00\text{ mm}$, $Z = 7.00\text{ mm}$ (reliée aux GPIO 17, 27, 22).
   * **Port USB-C Alimentation Pi 5 :** Rectangle de **11.00 mm × 6.50 mm** (congés R1.5) à $X = 40.00\text{ mm}$.
   * **Port RJ45 Gigabit Ethernet :** Rectangle de **16.50 mm × 14.00 mm** à $X = 72.00\text{ mm}$.
   * **Ports USB Doubles (USB 3.0 / 2.0) :** Rectangle de **15.00 mm × 16.50 mm** à $X = 104.00\text{ mm}$.
   * **Port Micro-HDMI :** Rectangle de **8.50 mm × 5.00 mm** à $X = 136.00\text{ mm}$.
   * **Glissière Bouton d'Allumage Power (⏻) :** Rectangle de **12.00 mm × 8.00 mm** à $X = 175.00\text{ mm}$.
4. **Enlèvement de matière extrudé** ➔ Condition : **À travers tout**.

### Étape 1.3 : Aménagements Intérieurs (Bossages Pi 5, Berceau Batterie & HP)
1. Sélectionner le **fond intérieur plat** de la cuve ➔ Nouvelle **Esquisse**.
2. **Zone Gauche — Raspberry Pi 5 :**
   * 4 bossages circulaires de **Ø6.00 mm ext.** avec avant-trou de **Ø2.20 mm** (pour vis auto-taraudeuses M2.5) :
     * Plot 1 : $X = 18.00\text{ mm}, Y = 16.00\text{ mm}$
     * Plot 2 : $X = 18.00 + 58.00 = 76.00\text{ mm}, Y = 16.00\text{ mm}$
     * Plot 3 : $X = 18.00\text{ mm}, Y = 16.00 + 49.00 = 65.00\text{ mm}$
     * Plot 4 : $X = 76.00\text{ mm}, Y = 65.00\text{ mm}$
   * Bossage extrudé de **3.00 mm** de hauteur.
3. **Zone Centrale — Berceau Batterie 2× 18650 :**
   * Dessiner un cadre de cloisonnement de **69.00 mm × 38.50 mm**, épaisseur de paroi 1.8 mm, centré entre $X = 85\text{ mm}$ et $X = 125\text{ mm}$.
   * Bossage extrudé de **8.00 mm** de hauteur (cale parfaitement les 2 cellules sans jeu).
4. **Zone Droite — Logement Haut-Parleur & Carte Ampli I2S :**
   * Cadre rectangulaire pour le module HP ovale noir : **71.00 mm × 32.00 mm**, hauteur **10.00 mm**.
   * Emplacement contigu pour la carte ampli MAX98357A (carte verte avec bornier à vis) : **20.00 mm × 18.00 mm**.
5. **Puits d'angle pour inserts filetés M3 :**
   * Aux 4 coins intérieurs : 4 bossages de **Ø7.00 mm** avec trou borgne de **Ø4.00 mm × 5.50 mm de profondeur** pour enfoncer à chaud les 4 inserts en laiton M3.

---

## 🛠️ PARTIE 2 : Le Capot Supérieur Blanc (`P01_Capot_Superieur.SLDPRT`)

### Étape 2.1 : Forme extérieure biseautée
1. Nouveau document **Pièce**.
2. **Plan de dessus** ➔ Rectangle centré de **208.00 mm × 114.00 mm** avec les 4 chanfreins de coin de **18.00 mm × 45°**.
3. **Bossage extrudé** de **10.00 mm** vers le haut.
4. Sur la face supérieure, appliquer un **Chanfrein d'arête périphérique** de **3.00 mm × 45°**.
5. **Fonction Coque (Shell)** par le dessous : Épaisseur **2.50 mm**.

### Étape 2.2 : Les Ouvertures des Boutons & Grille
1. Sélectionner la **face supérieure plane** ➔ Créer une **Esquisse** (`Ctrl + 8`).
2. **Bouton N1 (Niveau 1 Fondamental — GPIO 5) :**
   * Orifice carré de **14.20 mm × 14.20 mm** (congés R1) situé en haut à gauche à $X = 36.00\text{ mm}, Y = 82.00\text{ mm}$.
3. **Barrette des Boutons N2, N3, N4 :**
   * 3 fenêtres carrées de **14.20 mm × 14.20 mm** situées en bas à droite sous la grille :
     * Touche N2 (Niveau 2 Lycée — GPIO 6) : $X = 145.00\text{ mm}, Y = 46.00\text{ mm}$
     * Touche N3 (Niveau 3 Terminale — GPIO 13) : $X = 163.00\text{ mm}, Y = 46.00\text{ mm}$
     * Touche N4 (Micro PTT — GPIO 26) : $X = 181.00\text{ mm}, Y = 46.00\text{ mm}$
4. **Les 2 Touches Inférieures Centrales :**
   * 2 fenêtres carrées de **12.50 mm × 12.50 mm** situées en bas au centre ($X = 75\text{ mm}$ et $X = 90\text{ mm}, Y = 24\text{ mm}$).
5. **Grille Acoustique du Haut-Parleur :**
   * Située en haut à droite (au-dessus des boutons N2-N4) :
   * Matrice de micro-trous de **Ø2.20 mm** disposés en quinconce sur un rectangle de **50.00 mm × 25.00 mm** (entraxe 3.50 mm).
6. **Trou du Microphone MEMS (INMP441) :**
   * Perçage unique de **Ø2.00 mm** à $X = 110.00\text{ mm}, Y = 95.00\text{ mm}$ (chanfreiné en entonnoir sur la face externe).
7. **Logo ALTA :**
   * Esquisse du logo au centre ($X = 105.00\text{ mm}, Y = 62.00\text{ mm}$) ➔ Enlèvement de matière en creux de **0.80 mm** de profondeur.
8. **Ouïes de ventilation d'angle (Avant-Gauche) :**
   * 6 fentes inclinées à 45° sur le biseau avant-gauche (permettent d'aspirer l'air frais directement au-dessus du ventilateur Pi 5).
9. **4 Trous de vis d'assemblage M3 :**
   * Perçages fraisés de **Ø3.20 mm** (fraisage tête conique 90° de Ø6.5 mm) coïncidant avec les inserts laiton du châssis bleu.

---

## 🛠️ PARTIE 3 : Les Accessoires Latéraux (Sangle & Protection)

### 3.1. L'Entourage de la Sangle Latérale (`P03_Entourage_Sangle.SLDPRT`)
* **Pièce en deux sous-éléments imprimés en blanc :**
  1. **L'étrier d'ancrage :** Se visse sur le flanc gauche du châssis bleu avec 2 vis M3.
  2. **Le passant ovale :** Anneau allongé de **28.00 mm × 12.00 mm** avec fente intérieure de **22.00 mm × 3.50 mm** permettant de glisser la sangle textile bleue en nylon.

### 3.2. L'Angle de Protection Droit (`P04_Angle_Protection.SLDPRT`)
* Bumper en équerre biseautée imprimé en blanc qui vient épouser le chanfrein arrière-droit pour équilibrer l'esthétique bicolore et protéger le boîtier des chocs scolaires.

---

## 🖲️ PARTIE 4 : Les Touches de Boutons & Grips (`P05` et `P06`)

1. **Touches N1, N2, N3, N4 (Bleu Roi) :**
   * Collerette inférieure anti-dégagement de **16.00 mm × 16.00 mm × 1.20 mm**.
   * Corps supérieur carré de **13.50 mm × 13.50 mm × 3.00 mm** avec texte en creux (N1, N2, N3, N4).
   * Picot central de contact de **Ø3.00 mm × 2.50 mm**.
2. **Touche Power ⏻ (Blanc Pur) :**
   * Corps rectangulaire de **11.50 mm × 7.50 mm × 3.00 mm** avec symbole Power en creux.
3. **Grips Latéraux (Bleu Roi) :**
   * 2 plaquettes rectangulaires avec 8 nervures inclinées à 45° de 1.0 mm de relief pour une préhension antidérapante.

---

## 🔌 5. Schéma de Câblage Interne & Pins Raspberry Pi 5

Pour connecter l'électronique réelle aux boutons dès l'assemblage :

```
┌────────────────────────────────────────────────────────────────────────┐
│               MAPPING CONNECTEUR GPIO 40 BROCHES (PI 5)                 │
├───────────────────────┬────────────┬─────────────┬─────────────────────┤
│ Fonction Électronique │ Broche BCM │ Pin Physique│ Connexion Matérielle│
├───────────────────────┼────────────┼─────────────┼─────────────────────┤
│ Bouton N1 (Fondam.)   │ GPIO 5     │ Pin 29      │ Switch N1 vers GND  │
│ Bouton N2 (Second.)   │ GPIO 6     │ Pin 31      │ Switch N2 vers GND  │
│ Bouton N3 (Terminale) │ GPIO 13    │ Pin 33      │ Switch N3 vers GND  │
│ Bouton N4 (Micro PTT) │ GPIO 26    │ Pin 37      │ Switch N4 vers GND  │
│ LED Rouge             │ GPIO 17    │ Pin 11      │ Anode R (via 220Ω)  │
│ LED Verte             │ GPIO 27    │ Pin 13      │ Anode V (via 220Ω)  │
│ LED Bleue             │ GPIO 22    │ Pin 15      │ Anode B (via 220Ω)  │
│ Audio I2S Bit Clock   │ GPIO 18    │ Pin 12      │ MAX98357A BCLK      │
│ Audio I2S Word Select │ GPIO 19    │ Pin 35      │ MAX98357A LRC       │
│ Audio I2S Data Out    │ GPIO 21    │ Pin 40      │ MAX98357A DIN       │
│ Micro I2S Data In     │ GPIO 20    │ Pin 38      │ INMP441 SD          │
│ Masse Commune         │ GND        │ Pin 6, 9, 39│ Masses communes     │
│ Alimentation 5V       │ 5V         │ Pin 2, 4    │ VCC Ampli & Micro   │
└───────────────────────┴────────────┴─────────────┴─────────────────────┘
```

---

## 🔩 6. Instructions d'Assemblage Physique

1. Insérer à chaud (à l'aide de la panne d'un fer à souder à 220°C) les **4 inserts filetés en laiton M3** dans les 4 puits d'angle du châssis bleu.
2. Visser la carte **Raspberry Pi 5** sur ses 4 plots avec 4 vis M2.5 × 6 mm.
3. Insérer le **pack 2× 18650** dans son berceau central avec une bande adhésive double-face ou sangle velcro.
4. Positionner le **module haut-parleur noir** dans son logement droit avec son joint mousse et brancher ses 2 fils sur le bornier à vis vert de l'ampli.
5. Placer les **touches N1, N2, N3, N4 et Power** dans leurs glissières sous le capot blanc.
6. Emboîter le capot blanc sur le châssis bleu et serrer les **4 vis CHC M3** par le dessus.
7. Glisser la **sangle bleue** dans le passant d'entourage latéral gauche.
