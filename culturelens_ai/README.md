# 🏛️ CultureLens AI — Moteur de Reconnaissance Visuelle des Monuments

Module d'intelligence artificielle de vision par ordinateur pour la reconnaissance des monuments historiques de **Bamako** et du **Mali**.

Conçu pour fonctionner sur **ordinateur**, sur **serveur FastAPI**, sur l'**ALTA Box (Edge AI)** et intégrable sur smartphone.

---

## 🚀 Fonctionnalités Clés

1. **Reconnaissance Visuelle Profonde (Deep Embeddings)** :
   * Backbone neuronal basé sur **MobileNetV3** pré-entraîné, projetant chaque image dans un espace d'embeddings L2 de **576 dimensions**.
   * Indexation par **centroïdes prototypes** et similarité cosinus avec calibrage de température.
   * Capable d'identifier un monument même à partir de **1 à 5 photos de référence** (*Few-Shot Landmark Recognition*).

2. **Augmentation de Données Réaliste (Bamako / Sahel)** :
   * Variations de luminosité simulant le soleil sahélien direct et les zones ombragées.
   * Angles de contre-plongée simulant la perspective des piétons au pied des édifices.
   * Légères rotations et recadrages aléatoires simulant les photos de smartphones.

3. **Multi-Critères (Vision + Géolocalisation GPS)** :
   * Si les coordonnées GPS sont fournies, le système combine le score visuel avec la proximité géographique pour éliminer toute ambiguïté.

4. **100% Fonctionnel & Extensible** :
   * Pas de faux mocks : un véritable réseau de neurones PyTorch extrait les caractéristiques et compare les vecteurs.

---

## 📂 Structure du Répertoire

```text
culturelens_ai/
├── dataset/
│   ├── reference_images/            <-- DÉPOSEZ VOS IMAGES ICI
│   │   ├── monument_independance_bamako/
│   │   ├── monument_tour_afrique_bamako/
│   │   ├── monument_paix_bamako/
│   │   ├── monument_armee_noire_bamako/
│   │   ├── monument_ciwara_senou_bamako/
│   │   ├── monument_musee_national_bamako/
│   │   ├── monument_mosquee_djenne/
│   │   └── ...
│   └── test_images/                 <-- Photos pour tester l'inférence
│       ├── test_independance.jpg
│       ├── test_tour_afrique.jpg
│       └── ...
├── models/                          <-- Modèle entraîné et index vectoriel
│   ├── culturelens_v1.pt            <-- Poids PyTorch
│   ├── monument_index.pt            <-- Matrice de centroïdes
│   └── labels.json                  <-- Métadonnées des monuments
├── src/
│   ├── config.py                    <-- Configuration & métadonnées
│   ├── dataset_loader.py            <-- Prétraitement et augmentations
│   ├── model.py                     <-- Architecture MobileNetV3 + Projection
│   ├── trainer.py                   <-- Entraînement et calcul des centroïdes
│   └── recognizer.py                <-- Moteur d'inférence en direct
├── train.py                         <-- Script CLI pour lancer l'entraînement
├── infer.py                         <-- Script CLI pour tester une photo
└── README.md
```

---

## 📸 Comment Ajouter des Images et Ré-entraîner

### Étape 1 : Déposer vos photos
Pour ajouter ou enrichir un monument, déposez simplement vos photos (formats `.jpg`, `.png`, `.webp`) dans le sous-dossier correspondant dans `dataset/reference_images/` :

Exemple :
```bash
# Pour le Monument de l'Indépendance
cp mes_photos/*.jpg AlternIA/culturelens_ai/dataset/reference_images/monument_independance_bamako/

# Pour la Tour de l'Afrique
cp mes_photos/*.jpg AlternIA/culturelens_ai/dataset/reference_images/monument_tour_afrique_bamako/
```

> **Note :** Même avec 1 seule image par monument, le moteur génère automatiquement 20 variations géométriques et photométriques pour apprendre à reconnaître l'édifice sous tous les angles !

### Étape 2 : Lancer l'entraînement
Exécutez la commande suivante :
```bash
cd /Users/ibrahimsorydiallo/Desktop/OSC/AlternIA
./.venv/bin/python culturelens_ai/train.py --augmentations 20
```
Le script affiche le nombre de monuments détectés, génère les prototypes, et sauvegarde `models/culturelens_v1.pt` et `models/monument_index.pt`.

---

## 🔍 Comment Tester une Image en Ligne de Commande

Pour tester la reconnaissance sur n'importe quelle photo :
```bash
cd /Users/ibrahimsorydiallo/Desktop/OSC/AlternIA
./.venv/bin/python culturelens_ai/infer.py culturelens_ai/dataset/test_images/test_independance.jpg
```

Exemple de sortie :
```text
==============================================================
       RÉSULTAT DE L'IDENTIFICATION CULTURELENS (AI VISION)    
==============================================================
📸 Image analysée      : test_independance.jpg
⏱️  Temps d'inférence  : 24.3 ms

🏛️  MONUMENT CERTIFIÉ  : MONUMENT DE L'INDÉPENDANCE
📍 Localisation         : Bamako
🏷️  Catégorie           : Symbole National (1960)
📊 Certitude IA         : [████████████████████████████] 98.4%
🔍 Similarité cosinus   : 0.9412
✅ Statut               : Vérifié & Certifié

🎨 Indices visuels identifiés :
   ✓ Obélisque étagé soudanais
   ✓ Frises géométriques mandingues
   ✓ Place circulaire
   ✓ Palmiers

📜 Explication : Correspondance visuelle forte (98.4%) avec Monument de l'Indépendance.
==============================================================
```

---

## 🌐 Intégration avec AlterniA Backend & Flutter

Le moteur `CultureLensRecognizer` est directement importé par le service backend :
* `POST /api/v1/culture/identify` : Reçoit la photo envoyée par l'application Flutter `det-mobile`, appelle le modèle neuronal, et renvoie le monument identifié avec son score de confiance certifié.
