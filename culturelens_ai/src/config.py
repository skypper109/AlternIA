"""Configuration du pipeline d'entraînement et d'inférence CultureLens AI."""

from pathlib import Path

# Chemins principaux
BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset"
REFERENCE_DIR = DATASET_DIR / "reference_images"
TEST_DIR = DATASET_DIR / "test_images"
MODELS_DIR = BASE_DIR / "models"

# Fichiers de modèles
MODEL_WEIGHTS_PATH = MODELS_DIR / "culturelens_v1.pt"
INDEX_PATH = MODELS_DIR / "monument_index.pt"
LABELS_PATH = MODELS_DIR / "labels.json"

# Métadonnées des monuments de Bamako (priorité absolue) et nationaux
BAMAKO_MONUMENTS = {
    "monument_independance_bamako": {
        "name": "Monument de l'Indépendance",
        "ville": "Bamako",
        "quartier": "Boulevard de l'Indépendance",
        "coords": (12.6469, -8.0028),
        "visual_features": ["Obélisque étagé soudanais", "Frises géométriques mandingues", "Place circulaire", "Palmiers"],
        "category": "Symbole National (1960)",
    },
    "monument_tour_afrique_bamako": {
        "name": "Tour de l'Afrique",
        "ville": "Bamako",
        "quartier": "Faladié",
        "coords": (12.5975, -7.9542),
        "visual_features": ["Tour cylindrique 46m", "Architecture baobab", "Flambeau sommet", "Grand rond-point vert"],
        "category": "Panafricanisme (2001)",
    },
    "monument_paix_bamako": {
        "name": "Monument de la Paix",
        "ville": "Bamako",
        "quartier": "Hamdallaye ACI 2000",
        "coords": (12.6311, -8.0267),
        "visual_features": ["Colombe métallique monumentale", "Ailes ajourées en acier", "Socle blanc géométrique", "Carrefour ACI"],
        "category": "Paix & Vivre-Ensemble (1996)",
    },
    "monument_armee_noire_bamako": {
        "name": "Monument des Héros de l'Armée Noire",
        "ville": "Bamako",
        "quartier": "Place de la Liberté",
        "coords": (12.6512, -7.9989),
        "visual_features": ["Statue de bronze tirailleurs", "Soldats africains en uniforme", "Piédestal en pierre sculptée", "Plinth commémoratif"],
        "category": "Mémoire Militaire (1924)",
    },
    "monument_ciwara_senou_bamako": {
        "name": "Masque Ciwara de Sénou",
        "ville": "Bamako",
        "quartier": "Sénou / Aéroport",
        "coords": (12.5510, -7.9548),
        "visual_features": ["Antilope sculptée Ciwara", "Grandes cornes recourbées", "Crinière ajourée en bois", "Entrée aéroportuaire"],
        "category": "Emblème Sacré Agricole",
    },
    "monument_musee_national_bamako": {
        "name": "Musée National du Mali",
        "ville": "Bamako",
        "quartier": "Parc National / Koulouba",
        "coords": (12.6601, -8.0019),
        "visual_features": ["Architecture banco ocre-rouge", "Colonnades et arcades sahéliennes", "Jardins botaniques", "Murs en terre cuite stabilisée"],
        "category": "Trésor Vivant & Archéologie",
    },
    "monument_samory_toure_bamako": {
        "name": "Monument Samory Touré",
        "ville": "Bamako",
        "quartier": "Sébénikoro",
        "coords": (12.6105, -8.0550),
        "visual_features": ["Statue équestre Samory Touré", "Résistant anticolonial", "Cheval cabré en bronze"],
        "category": "Résistance Anticoloniale",
    },
    "monument_martyrs_bamako": {
        "name": "Monument des Martyrs",
        "ville": "Bamako",
        "quartier": "Pont des Martyrs",
        "coords": (12.6358, -7.9942),
        "visual_features": ["Stèle commémorative mars 1991", "Flamme démocratique", "Abords du fleuve Niger"],
        "category": "Démocratie & Mémoire",
    },
    "monument_palais_culture_bamako": {
        "name": "Palais de la Culture Amadou Hampâté Bâ",
        "ville": "Bamako",
        "quartier": "Badalabougou",
        "coords": (12.6262, -7.9897),
        "visual_features": ["Amphithéâtre au bord du fleuve", "Grand complexe culturel", "Rive droite Djoliba"],
        "category": "Arts Vivants & Spectacle",
    },
    "monument_kwame_nkrumah_bamako": {
        "name": "Monument Kwamé Nkrumah",
        "ville": "Bamako",
        "quartier": "Avenue Nkrumah",
        "coords": (12.6380, -8.0120),
        "visual_features": ["Buste en bronze Nkrumah", "Père du panafricanisme", "Stèle noire gravée"],
        "category": "Panafricanisme",
    },
    "monument_cathedrale_bamako": {
        "name": "Cathédrale du Sacré-Cœur",
        "ville": "Bamako",
        "quartier": "Centre-ville",
        "coords": (12.6450, -7.9970),
        "visual_features": ["Façade en pierres de taille", "Style néo-roman africain", "Clocher en grès"],
        "category": "Patrimoine Religieux (1927)",
    },
    "monument_mosquee_bamako": {
        "name": "Grande Mosquée de Bamako",
        "ville": "Bamako",
        "quartier": "Dabanani",
        "coords": (12.6520, -7.9960),
        "visual_features": ["Minarets blancs élancés", "Dômes et arcades islamiques", "Cœur commercial Bamako"],
        "category": "Architecture Religieuse (1970)",
    },
    # Monuments Nationaux
    "monument_mosquee_djenne": {
        "name": "Grande Mosquée de Djenné",
        "ville": "Djenné",
        "quartier": "Mopti",
        "coords": (13.9056, -4.5550),
        "visual_features": ["Banco terre crue", "3 minarets soudanais", "Torons en bois de palmier", "Crépissage rituel"],
        "category": "Patrimoine Mondial UNESCO",
    },
    "monument_tata_sikasso": {
        "name": "Tata de Sikasso",
        "ville": "Sikasso",
        "quartier": "Kénédougou",
        "coords": (11.3176, -5.6664),
        "visual_features": ["Muraille de banco et pierres", "Colline du Mamelon", "Fortification militaire"],
        "category": "Monument Historique National",
    },
    "monument_tombeau_askia": {
        "name": "Tombeau des Askia",
        "ville": "Gao",
        "quartier": "Gao",
        "coords": (16.2994, -0.0450),
        "visual_features": ["Pyramide en terre banco", "Échafaudages de bois", "Nécropole Songhoï"],
        "category": "Patrimoine Mondial UNESCO",
    },
    "monument_djingareyber": {
        "name": "Mosquée Djingareyber",
        "ville": "Tombouctou",
        "quartier": "Tombouctou",
        "coords": (16.7711, -3.0094),
        "visual_features": ["Minaret tronconique sahélien", "Mansa Moussa 1327", "Architecture terre et pierre"],
        "category": "Patrimoine Mondial UNESCO",
    },
    "monument_sankore": {
        "name": "Université & Mosquée de Sankoré",
        "ville": "Tombouctou",
        "quartier": "Sankoré",
        "coords": (16.7758, -3.0031),
        "visual_features": ["Minaret en gradins", "Proportions Kaaba", "Cité des 700 000 manuscrits"],
        "category": "Patrimoine Mondial UNESCO",
    },
    "monument_fort_medine": {
        "name": "Fort de Médine",
        "ville": "Kayes",
        "quartier": "Médine",
        "coords": (14.3750, -11.3650),
        "visual_features": ["Bastion en pierre", "Chutes du Félou", "Récits El Hadj Oumar Tall"],
        "category": "Monument Historique National",
    },
    "segou": {
        "name": "Ségou-Koro & Cité des Balanzans",
        "ville": "Ségou",
        "quartier": "Ségou-Koro",
        "coords": (13.4333, -6.2667),
        "visual_features": ["Vestiges du Royaume Bambara", "Rives du Djoliba", "Balanzans sacrés", "Architecture banco"],
        "category": "Cité Historique & Royaume Bambara",
    },
    "monument_sogolon_bamako": {
        "name": "Statue de Sogolon Kolonkan",
        "ville": "Bamako",
        "quartier": "Hamdallaye / ACI 2000",
        "coords": (12.6340, -8.0200),
        "visual_features": ["Statue de Sogolon", "Mère de Soundiata Keïta", "Héroïne fondatrice du Mandé"],
        "category": "Matrimoine & Mémoire Mandingue",
    },
    "monument_al_quouds": {
        "name": "Monument Al-Qoods (Al-Qods)",
        "ville": "Bamako",
        "quartier": "Hamdallaye ACI 2000",
        "coords": (12.6360, -8.0250),
        "visual_features": ["Dôme doré Al-Quds", "Arcades orientales", "Croissant commémoratif"],
        "category": "Solidarité Internationale & Fraternité",
    },
    "monument_maliba_bamako": {
        "name": "Monument MaliBa (Grand Mali)",
        "ville": "Bamako",
        "quartier": "Centre-ville",
        "coords": (12.6480, -8.0010),
        "visual_features": ["Lettres monumentales MaliBa", "Emblème Vert Jaune Rouge", "Fierté civique"],
        "category": "Fierté Patriotique & Jeunesse",
    },
}

# Paramètres du modèle
IMAGE_SIZE = (224, 224)
BACKBONE_NAME = "mobilenet_v3_small"  # Ultraléger, ultra-rapide sur mobile et ALTA Box
EMBEDDING_DIM = 576
CONFIDENCE_THRESHOLD = 0.65
TEMPERATURE = 12.0  # Température de scaling pour les probabilités softmax
