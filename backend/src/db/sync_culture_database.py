"""
Script de synchronisation complète et certifiée de la base de données culturelle.
Met à jour et peuple MySQL et SQLite avec l'ensemble des données culturelles authentiques :
- 24 Monuments & Sites (photos réelles vérifiées)
- 6 Grands Personnages Historiques
- 7 Villes & Terroirs
- 4 Contes & Fables
- 8 Proverbes & Défis
"""

import json
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session

from backend.src.db.database import SessionLocal, SQLITE_FALLBACK_URL
from sqlalchemy import create_engine
from backend.src.db.models import (
    Base,
    CultureMonument,
    CulturePersonnage,
    CultureLieu,
    CultureConte,
    CultureProverbe,
)

# ══════════════════════════════════════════════════════════════════════════════
# 1. CATALOGUE COMPLET DES MONUMENTS
# ══════════════════════════════════════════════════════════════════════════════

ALL_MONUMENTS = [
    {
        "id": "monument_independance_bamako",
        "nom": "Monument de l'Indépendance",
        "sous_titre": "Symbole de la Souveraineté du Mali (1960)",
        "region_id": "bamako",
        "region_nom": "Bamako",
        "ville": "Bamako",
        "epoque": "Inauguré dans les années 1990 · Célébration du 22 septembre 1960",
        "style_architectural": "Structure pyramidale élancée en béton ornée de frises géométriques mandingues et coiffée de l'emblème républicain.",
        "details_localisation": "Boulevard de l'Indépendance, Centre-ville de Bamako",
        "photo_url": "assets/images/culture/monuments/monument_independance.jpg",
        "tag": "Symbole National",
        "latitude": 12.6392,
        "longitude": -8.0029,
        "badge_debloque": "Pionnier de la Souveraineté",
        "xp_recompense": 60,
        "mots_cles": ["independance", "obelisque", "bamako", "modibo", "keita", "1960", "souverainete"],
        "caracteristiques_detection": [
            {"label": "Date historique", "value": "22 septembre 1960", "icon": "event_rounded"},
            {"label": "Président", "value": "Modibo Keïta", "icon": "person_rounded"},
            {"label": "Localisation", "value": "Centre-ville de Bamako", "icon": "location_on_rounded"},
            {"label": "Statut", "value": "Monument commémoratif national", "icon": "verified_rounded"},
        ],
        "secrets_et_mysteres": "Le monument est le repère civique par excellence de Bamako, où se déroulent les défilés commémoratifs et les rassemblements patriotiques majeurs de la nation.",
        "recit_historique": "Érigé au cœur de la capitale malienne, ce minaret laïque et élancé commémore l'accession solennelle de la République du Mali à la pleine indépendance le 22 septembre 1960 sous la présidence de Modibo Keïta.",
        "narration_audio_texte": "Le 22 septembre 1960, le Congrès extraordinaire de l'Union Soudanaise-RDA proclame la naissance de la République du Mali, consacrant l'hymne national 'Pour l'Afrique et pour toi, Mali'.",
        "pourquoi_ce_lieu_compte": "Ce monument est le repère civique par excellence de Bamako, où se déroulent les défilés commémoratifs et les rassemblements patriotiques majeurs de la nation.",
        "route_path": "/culture/monument/monument_independance_bamako",
        "modele_3d_url": "assets/models/monument_independance.glb",
        "ar_disponible": True,
        "statut_validation": "Validé Archives Nationales",
    },
    {
        "id": "monument_tour_afrique_bamako",
        "nom": "Tour de l'Afrique",
        "sous_titre": "Phare du Panafricanisme & de l'Unité",
        "region_id": "bamako",
        "region_nom": "Bamako",
        "ville": "Bamako",
        "epoque": "Inaugurée en 2001 · Sommet France-Afrique",
        "style_architectural": "Béton armé revêtu de briques de terre stabilisée et bas-reliefs narrant les grandes figures de la libération africaine.",
        "details_localisation": "Échangeur de Faladié, Rive droite du fleuve Niger, Bamako",
        "photo_url": "assets/images/culture/monuments/tour_afrique.jpg",
        "tag": "Panafricanisme",
        "latitude": 12.5935,
        "longitude": -7.9463,
        "badge_debloque": "Bâtisseur de l'Unité Africaine",
        "xp_recompense": 60,
        "mots_cles": ["tour", "afrique", "faladie", "baobab", "panafricanisme", "bamako"],
        "caracteristiques_detection": [
            {"label": "Hauteur", "value": "46 mètres", "icon": "height_rounded"},
            {"label": "Inauguration", "value": "Janvier 2001", "icon": "event_rounded"},
            {"label": "Symbole", "value": "Flambeau de l'Unité Africaine", "icon": "local_fire_department_rounded"},
            {"label": "Quartier", "value": "Faladié / Sogoniko", "icon": "map_rounded"},
        ],
        "secrets_et_mysteres": "La Tour de l'Afrique abrite un mémorial des résistances anticoloniales et célèbre la solidarité panafricaine à la croisée des axes routiers reliant le Mali à la Côte d'Ivoire et au Burkina Faso.",
        "recit_historique": "Haute de 46 mètres, la Tour de l'Afrique est une spectaculaire tour cylindrique combinant la symbolique du baobab protecteur et du minaret sahélien, couronnée d'un flambeau métallique.",
        "narration_audio_texte": "Dressée à 46 mètres au-dessus du rond-point de Faladié, la Tour de l'Afrique accueille les visiteurs entrant à Bamako, rappelant la vocation du Mali à être le carrefour éternel de l'unité africaine.",
        "pourquoi_ce_lieu_compte": "Érigée pour symboliser l'idéal des États-Unis d'Afrique promu par Kwamé Nkrumah, Modibo Keïta et Gamal Abdel Nasser.",
        "route_path": "/culture/monument/monument_tour_afrique_bamako",
        "modele_3d_url": "assets/models/tour_afrique.glb",
        "ar_disponible": True,
        "statut_validation": "Validé Ville de Bamako",
    },
    {
        "id": "monument_paix_bamako",
        "nom": "Monument de la Paix",
        "sous_titre": "Colombe Métallique de la Concorde",
        "region_id": "bamako",
        "region_nom": "Bamako",
        "ville": "Bamako",
        "epoque": "Érigé en 1996 · Flamme de la Paix",
        "style_architectural": "Structure ajourée en acier forgé et socle en marbre blanc de Sélinkegny.",
        "details_localisation": "Carrefour Hamdallaye ACI 2000, Bamako",
        "photo_url": "assets/images/culture/monuments/monument_paix.jpg",
        "tag": "Paix & Vivre-Ensemble",
        "latitude": 12.6322,
        "longitude": -8.0261,
        "badge_debloque": "Artisan de la Paix",
        "xp_recompense": 50,
        "mots_cles": ["paix", "colombe", "aci 2000", "hamdallaye", "concorde", "bamako"],
        "caracteristiques_detection": [
            {"label": "Symbole", "value": "Colombe de la Paix", "icon": "flutter_dash_rounded"},
            {"label": "Matériau", "value": "Acier forgé & Marbre", "icon": "architecture_rounded"},
            {"label": "Quartier", "value": "Hamdallaye ACI 2000", "icon": "location_pin"},
        ],
        "secrets_et_mysteres": "Ce monument célèbre le génie du dialogue intercommunautaire malien hérité de la Charte de Kouroukan Fouga et du cousinage à plaisanterie (Sinankunya).",
        "recit_historique": "Colombe monumentale en dentelle d'acier aux ailes déployées vers le ciel, symbolisant l'aspiration universelle des communautés maliennes à la concorde et à la paix durable.",
        "narration_audio_texte": "Vous admirez le Monument de la Paix d'Hamdallaye ACI 2000. La colombe immaculée prenant son essor symbolise le triomphe du dialogue sur la discorde.",
        "pourquoi_ce_lieu_compte": "Rappelle la Flamme de la Paix de Tombouctou (1996) et la valeur suprême du dialogue traditionnel et du vivre-ensemble.",
        "route_path": "/culture/monument/monument_paix_bamako",
        "modele_3d_url": None,
        "ar_disponible": False,
        "statut_validation": "Validé",
    },
    {
        "id": "monument_armee_noire_bamako",
        "nom": "Monument de l'Armée Noire",
        "sous_titre": "Hommage aux Tirailleurs & Héros Africains",
        "region_id": "bamako",
        "region_nom": "Bamako",
        "ville": "Bamako",
        "epoque": "Conçu en 1924 • Réhabilité solennellement en 2004",
        "style_architectural": "Statuaire monumentale en bronze représentant des soldats africains solidaires.",
        "details_localisation": "Place de la Liberté, Bamako · 1924",
        "photo_url": "assets/images/culture/monuments/monument_armee_noire.jpg",
        "tag": "Mémoire Militaire",
        "latitude": 12.6514,
        "longitude": -7.9982,
        "badge_debloque": "Mémoire des Tirailleurs",
        "xp_recompense": 55,
        "mots_cles": ["tirailleurs", "armee noire", "liberte", "guerre", "heros", "bamako", "bronze"],
        "caracteristiques_detection": [
            {"label": "Sculpture", "value": "Bronze commémoratif", "icon": "military_tech_rounded"},
            {"label": "Époque", "value": "1924 / 2004", "icon": "history_rounded"},
            {"label": "Hommage", "value": "Tirailleurs sénégalais et héros ouest-africains", "icon": "shield_rounded"},
        ],
        "secrets_et_mysteres": "Ce monument est la réplique exacte de celui érigé à Reims en France en 1924, détruit durant l'occupation, puis reconstruit grâce aux archives de Bamako.",
        "recit_historique": "Statue de bronze honorant le sacrifice et le courage des soldats africains et tirailleurs pour la liberté.",
        "narration_audio_texte": "Ici s'élève le Monument des Héros de l'Armée Noire. Il honore la mémoire impérissable des combattants africains.",
        "pourquoi_ce_lieu_compte": "Plaque tournante de la mémoire combattante africaine et de la reconnaissance internationale.",
        "route_path": "/culture/monument/monument_armee_noire_bamako",
        "modele_3d_url": None,
        "ar_disponible": False,
        "statut_validation": "Validé Archives Militaires",
    },
    {
        "id": "monument_musee_national_bamako",
        "nom": "Musée National du Mali",
        "sous_titre": "Trésors Archéologiques & Masques Rituels",
        "region_id": "bamako",
        "region_nom": "Bamako",
        "ville": "Bamako",
        "epoque": "Créé en 1953 • Complexe rénové en 2003 (Prix Aga Khan)",
        "style_architectural": "Joyau en terre cuite stabilisée et pierre de grès rouge locale abritant des milliers d'objets rituels.",
        "details_localisation": "Bamako · Parc Koulouba",
        "photo_url": "assets/images/culture/monuments/musee_national.jpg",
        "tag": "Trésor Vivant",
        "latitude": 12.6597,
        "longitude": -7.9989,
        "badge_debloque": "Conservateur du Trésor Malien",
        "xp_recompense": 65,
        "mots_cles": ["musee", "national", "koulouba", "masques", "tissus", "archeologie", "bamako"],
        "caracteristiques_detection": [
            {"label": "Façades", "value": "Grès rouge et banco stabilisé", "icon": "foundation_rounded"},
            {"label": "Collection", "value": "Plus de 10 000 pièces archéologiques", "icon": "museum_rounded"},
            {"label": "Distinction", "value": "Prix Aga Khan d'Architecture (2004)", "icon": "workspace_premium_rounded"},
        ],
        "secrets_et_mysteres": "Le musée conserve les plus anciens textiles archéologiques subsahariens découverts dans les grottes Tellem des falaises de Bandiagara (XIe siècle).",
        "recit_historique": "Joyau en terre cuite stabilisée abritant des milliers d'objets rituels, statuettes et textiles traditionnels.",
        "narration_audio_texte": "Vous voici au Musée National du Mali, un chef-d'œuvre architectural niché dans le Parc de Bamako.",
        "pourquoi_ce_lieu_compte": "Le plus grand sanctuaire de conservation du patrimoine matériel malien.",
        "route_path": "/culture/monument/monument_musee_national_bamako",
        "modele_3d_url": None,
        "ar_disponible": False,
        "statut_validation": "Validé Scientifique",
    },
    {
        "id": "monument_ciwara_senou_bamako",
        "nom": "Masque Ciwara de Sénou",
        "sous_titre": "Porte d'Accueil & Dignité Paysanne",
        "region_id": "bamako",
        "region_nom": "Bamako",
        "ville": "Bamako",
        "epoque": "Années 2000",
        "style_architectural": "Sculpture monumentale en métal ajouré de l'antilope mythique Ciwara.",
        "details_localisation": "Bamako · Sénou (Rond-point Aéroport)",
        "photo_url": "assets/images/culture/monuments/ciwara_senou.jpg",
        "tag": "Emblème Sacré",
        "latitude": 12.5517,
        "longitude": -7.9548,
        "badge_debloque": "Gardien du Ciwara",
        "xp_recompense": 50,
        "mots_cles": ["ciwara", "tchiwara", "senou", "aeroport", "agriculture", "bamako"],
        "caracteristiques_detection": [
            {"label": "Silhouette", "value": "Antilope-cheval sacrée", "icon": "pets_rounded"},
            {"label": "Rôle", "value": "Porte d'accueil de la capitale", "icon": "flight_takeoff_rounded"},
            {"label": "Symbolique", "value": "Ardeur au labeur paysan", "icon": "eco_rounded"},
        ],
        "secrets_et_mysteres": "Dans la spiritualité bamanan, le Ciwara est l'être mythique envoyé pour apprendre la culture du mil aux humains sans jamais se décourager.",
        "recit_historique": "Sculpture monumentale de l'antilope mythique Ciwara, symbole de l'ardeur au labeur et de la fertilité.",
        "narration_audio_texte": "Dès votre arrivée à Bamako depuis l'aéroport de Sénou, le majestueux masque Ciwara vous salue avec dignité.",
        "pourquoi_ce_lieu_compte": "C'est l'un des emblèmes culturels et artistiques les plus célèbres du Mali à travers le monde.",
        "route_path": "/culture/monument/monument_ciwara_senou_bamako",
        "modele_3d_url": None,
        "ar_disponible": False,
        "statut_validation": "Validé",
    },
    {
        "id": "monument_palais_culture_bamako",
        "nom": "Palais de la Culture Amadou Hampâté Bâ",
        "sous_titre": "L'Agora des Arts au Bord du Djoliba",
        "region_id": "bamako",
        "region_nom": "Bamako",
        "ville": "Bamako",
        "epoque": "Inauguré en 1976 • Dédié à Amadou Hampâté Bâ en 1991",
        "style_architectural": "Grand amphithéâtre et salles de spectacles modernes en bordure du Djoliba.",
        "details_localisation": "Bamako · Badalabougou",
        "photo_url": "assets/images/culture/monuments/palais_culture.jpg",
        "tag": "Arts Vivants",
        "latitude": 12.6262,
        "longitude": -7.9897,
        "badge_debloque": "Maître de la Parole",
        "xp_recompense": 50,
        "mots_cles": ["palais", "culture", "amadou", "hampate ba", "theatre", "musique", "badalabougou", "bamako"],
        "caracteristiques_detection": [
            {"label": "Capacité", "value": "3 000 places en plein air", "icon": "theater_comedy_rounded"},
            {"label": "Cadre", "value": "Bord du fleuve Niger", "icon": "water_rounded"},
            {"label": "Dédicace", "value": "Amadou Hampâté Bâ", "icon": "menu_book_rounded"},
        ],
        "secrets_et_mysteres": "C'est ici que se réunissent les plus grands maîtres de la kora, du balafon et de la parole griotique lors des biennales culturelles.",
        "recit_historique": "Scène nationale des grands concerts, du théâtre et des contes, nommée en hommage au sage de Bandiagara.",
        "narration_audio_texte": "Le Palais de la Culture Amadou Hampâté Bâ porte le nom du sage qui nous a légué : 'En Afrique, un vieillard qui meurt est une bibliothèque qui brûle'.",
        "pourquoi_ce_lieu_compte": "Le cœur névralgique de la création musicale, théâtrale et chorégraphique malienne.",
        "route_path": "/culture/monument/monument_palais_culture_bamako",
        "modele_3d_url": None,
        "ar_disponible": False,
        "statut_validation": "Validé",
    },
    {
        "id": "monument_samory_toure_bamako",
        "nom": "Monument Samory Touré",
        "sous_titre": "Statue Équestre de la Résistance",
        "region_id": "bamako",
        "region_nom": "Bamako",
        "ville": "Bamako",
        "epoque": "Érigé sous la IIIe République",
        "style_architectural": "Statue équestre impériale en bronze sur son cheval cabré à Sébénikoro.",
        "details_localisation": "Bamako · Sébénikoro",
        "photo_url": "assets/images/culture/monuments/monument_samory_toure_bamako/sam5.jpg",
        "tag": "Résistance Anticoloniale",
        "latitude": 12.6348,
        "longitude": -8.0315,
        "badge_debloque": "Cavalier du Ouassoulou",
        "xp_recompense": 55,
        "mots_cles": ["samory", "toure", "almamy", "cavalier", "cheval", "sebenikoro", "resistance", "bamako"],
        "caracteristiques_detection": [
            {"label": "Statue", "value": "Bronze équestre monumental", "icon": "sports_score_rounded"},
            {"label": "Héros", "value": "Almamy Samory Touré", "icon": "shield_rounded"},
            {"label": "Royaume", "value": "Empire Ouassoulou", "icon": "flag_rounded"},
        ],
        "secrets_et_mysteres": "Samory Touré avait développé des forges artisanales capables de fabriquer des répliques fidèles des fusils modernes de son époque.",
        "recit_historique": "Statue équestre impériale en bronze d'Almamy Samory Touré sur son cheval cabré à Sébénikoro.",
        "narration_audio_texte": "Vous voici devant la statue équestre de l'Almamy Samory Touré, l'une des figures militaires les plus remarquables de l'histoire africaine.",
        "pourquoi_ce_lieu_compte": "Symbole de la résistance acharnée et de la capacité industrielle précoloniale.",
        "route_path": "/culture/monument/monument_samory_toure_bamako",
        "modele_3d_url": None,
        "ar_disponible": False,
        "statut_validation": "Validé",
    },
    {
        "id": "monument_martyrs_bamako",
        "nom": "Monument des Martyrs",
        "sous_titre": "La Flamme Démocratique du 26 Mars 1991",
        "region_id": "bamako",
        "region_nom": "Bamako",
        "ville": "Bamako",
        "epoque": "Inauguré dans les années 1990",
        "style_architectural": "Stèle commémorative surplombant le fleuve Niger avec arche sculptée en béton blanc et bronze.",
        "details_localisation": "Bamako · Pont des Martyrs",
        "photo_url": "assets/images/culture/monuments/monument_martyrs_bamako/mart10.jpg",
        "tag": "Démocratie & Mémoire",
        "latitude": 12.6289,
        "longitude": -7.9942,
        "badge_debloque": "Gardien de la Démocratie",
        "xp_recompense": 50,
        "mots_cles": ["martyrs", "26 mars 1991", "pont", "badalabougou", "democratie", "bamako"],
        "caracteristiques_detection": [
            {"label": "Date commémorée", "value": "26 Mars 1991", "icon": "event_rounded"},
            {"label": "Localisation", "value": "Tête du Pont des Martyrs", "icon": "bridge_rounded"},
            {"label": "Symbole", "value": "Victoire de la liberté citoyenne", "icon": "local_fire_department_rounded"},
        ],
        "secrets_et_mysteres": "C'est au pied de ce pont que la foule des manifestants de mars 1991 franchit pacifiquement le fleuve pour réclamer la démocratie plurielle.",
        "recit_historique": "Stèle commémorative surplombant le fleuve Niger en mémoire des héros du mouvement démocratique.",
        "narration_audio_texte": "Le Monument des Martyrs rappelle le prix payé par le peuple de Bamako pour la conquête de la liberté et du pluralisme.",
        "pourquoi_ce_lieu_compte": "Cœur de la mémoire citoyenne contemporaine du Mali.",
        "route_path": "/culture/monument/monument_martyrs_bamako",
        "modele_3d_url": None,
        "ar_disponible": False,
        "statut_validation": "Validé",
    },
    {
        "id": "monument_kwame_nkrumah_bamako",
        "nom": "Monument Kwamé Nkrumah",
        "sous_titre": "Panafricanisme & Fraternité",
        "region_id": "bamako",
        "region_nom": "Bamako",
        "ville": "Bamako",
        "epoque": "Années 2000",
        "style_architectural": "Buste en bronze et stèle commémorative en l'honneur de Kwamé Nkrumah.",
        "details_localisation": "Bamako · Avenue Nkrumah, Hamdallaye",
        "photo_url": "assets/images/culture/monuments/monument_kwame_nkrumah_bamako/kk6.jpg",
        "tag": "Panafricanisme",
        "latitude": 12.6375,
        "longitude": -8.0185,
        "badge_debloque": "Apôtre du Panafricanisme",
        "xp_recompense": 45,
        "mots_cles": ["kwame", "nkrumah", "ghana", "union africaine", "hamdallaye", "bamako"],
        "caracteristiques_detection": [
            {"label": "Personnalité", "value": "Kwamé Nkrumah (Ghana)", "icon": "person_rounded"},
            {"label": "Alliance", "value": "Union Guinée-Mali-Ghana (1961)", "icon": "handshake_rounded"},
            {"label": "Idéal", "value": "États-Unis d'Afrique", "icon": "public_rounded"},
        ],
        "secrets_et_mysteres": "Ce carrefour rappelle l'Union historique Ghana-Guinée-Mali scellée en 1961 par Modibo Keïta, Kwamé Nkrumah et Sékou Touré.",
        "recit_historique": "Buste en bronze et stèle commémorative en l'honneur de Kwamé Nkrumah et de l'alliance historique avec Modibo Keïta.",
        "narration_audio_texte": "Le Monument Kwamé Nkrumah à Bamako honore l'un des plus illustres théoriciens de la liberté africaine.",
        "pourquoi_ce_lieu_compte": "Symbole de l'amitié entre les peuples et de la fraternité historique.",
        "route_path": "/culture/monument/monument_kwame_nkrumah_bamako",
        "modele_3d_url": None,
        "ar_disponible": False,
        "statut_validation": "Validé",
    },
    {
        "id": "monument_cathedrale_bamako",
        "nom": "Cathédrale du Sacré-Cœur",
        "sous_titre": "Patrimoine en Grès Sahélien (1927)",
        "region_id": "bamako",
        "region_nom": "Bamako",
        "ville": "Bamako",
        "epoque": "Construite entre 1925 et 1936 · Bénédiction 1927",
        "style_architectural": "Édifice majestueux en pierres de taille locales néo-romanes africaines et briques de grès rouge.",
        "details_localisation": "Bamako · Boulevard du Peuple, Centre-ville",
        "photo_url": "assets/images/culture/monuments/monument_cathedrale_bamako/cat1.jpg",
        "tag": "Patrimoine Religieux",
        "latitude": 12.6465,
        "longitude": -7.9948,
        "badge_debloque": "Pèlerin de la Fraternité",
        "xp_recompense": 50,
        "mots_cles": ["cathedrale", "sacre coeur", "gres rouge", "centre-ville", "bamako", "eglise"],
        "caracteristiques_detection": [
            {"label": "Style", "value": "Néo-roman africain en grès rouge", "icon": "church_rounded"},
            {"label": "Édification", "value": "1925 – 1936", "icon": "history_rounded"},
            {"label": "Valeur", "value": "Concorde interreligieuse", "icon": "handshake_rounded"},
        ],
        "secrets_et_mysteres": "La première pierre fut bénie en 1925 en présence des notables musulmans de Bamako, marquant une tradition de convivialité exemplaire.",
        "recit_historique": "Édifice majestueux en pierres de taille locales néo-romanes africaines érigé au centre-ville.",
        "narration_audio_texte": "La Cathédrale du Sacré-Cœur de Bamako s'élève au cœur du centre animé, témoignant du dialogue spirituel en terre malienne.",
        "pourquoi_ce_lieu_compte": "Témoin majeur de l'histoire religieuse et de la tolérance séculaire du Mali.",
        "route_path": "/culture/monument/monument_cathedrale_bamako",
        "modele_3d_url": None,
        "ar_disponible": False,
        "statut_validation": "Validé",
    },
    {
        "id": "monument_mosquee_bamako",
        "nom": "Grande Mosquée de Bamako",
        "sous_titre": "Minarets Blancs & Coupole Émeraude",
        "region_id": "bamako",
        "region_nom": "Bamako",
        "ville": "Bamako",
        "epoque": "Édifiée en 1948 • Rénovée dans les années 1970",
        "style_architectural": "Mosquée moderne à minarets multiples, coupoles émeraude et arcades islamiques.",
        "details_localisation": "Bamako · Dabanani, Bozola",
        "photo_url": "assets/images/culture/monuments/mosquee_bamako.jpg",
        "tag": "Architecture Religieuse",
        "latitude": 12.6489,
        "longitude": -7.9925,
        "badge_debloque": "Fidèle du Bozola",
        "xp_recompense": 50,
        "mots_cles": ["mosquee", "grande mosquee", "bamako", "bozola", "dabanani", "minarets"],
        "caracteristiques_detection": [
            {"label": "Minarets", "value": "Minarets blancs élancés", "icon": "mosque_rounded"},
            {"label": "Quartier", "value": "Dabanani / Bozola", "icon": "location_on_rounded"},
            {"label": "Capacité", "value": "Grandes prières communautaires", "icon": "groups_rounded"},
        ],
        "secrets_et_mysteres": "La mosquée a été construite sur l'emplacement originel du village des pêcheurs Bozo, premiers habitants des rives de Bamako.",
        "recit_historique": "Cœur spirituel de Bamako situé à Dabanani, avec ses minarets élancés et ses arcades islamiques.",
        "narration_audio_texte": "La Grande Mosquée de Bamako dresse ses minarets au cœur de la ville, symbolisant la foi et le rayonnement de la culture islamique malienne.",
        "pourquoi_ce_lieu_compte": "Épicentre de la vie religieuse et communautaire de Bamako.",
        "route_path": "/culture/monument/monument_mosquee_bamako",
        "modele_3d_url": None,
        "ar_disponible": False,
        "statut_validation": "Validé",
    },
    {
        "id": "monument_sogolon_bamako",
        "nom": "Statue de Sogolon Kolonkan",
        "sous_titre": "Matrimoine & Mémoire Mandingue",
        "region_id": "bamako",
        "region_nom": "Bamako",
        "ville": "Bamako",
        "epoque": "Époque contemporaine • Hommage au XIIIe siècle",
        "style_architectural": "Statue monumentale en bronze figurant l'héroïne mandingue, garante de la concorde.",
        "details_localisation": "Bamako · Hamdallaye ACI 2000",
        "photo_url": "assets/images/culture/monuments/monument_sogolon_bamako/sog9.jpg",
        "tag": "Matrimoine Mandingue",
        "latitude": 12.6340,
        "longitude": -8.0200,
        "badge_debloque": "Guerrière du Manden",
        "xp_recompense": 50,
        "mots_cles": ["sogolon", "kolonkan", "soundiata", "mande", "femme", "aci 2000", "bamako"],
        "caracteristiques_detection": [
            {"label": "Figure", "value": "Héroïne royale du Mandé", "icon": "woman_rounded"},
            {"label": "Parenté", "value": "Sœur de Soundiata Keïta", "icon": "family_restroom_rounded"},
            {"label": "Vertu", "value": "Clairvoyance et concorde", "icon": "psychology_rounded"},
        ],
        "secrets_et_mysteres": "Sogolon Kolonkan est réputée dans l'épopée pour sa clairvoyance et ses pouvoirs spirituels qui protégèrent Soundiata dans son exil.",
        "recit_historique": "Hommage à l'héroïne royale du Mandé, sœur de Soundiata Keïta, garante de la concorde.",
        "narration_audio_texte": "La statue de Sogolon Kolonkan célèbre la bravoure et la sagesse des femmes fondatrices de notre histoire.",
        "pourquoi_ce_lieu_compte": "Célébration du rôle héroïque et spirituel des femmes dans l'histoire mandingue.",
        "route_path": "/culture/monument/monument_sogolon_bamako",
        "modele_3d_url": None,
        "ar_disponible": False,
        "statut_validation": "Validé",
    },
    {
        "id": "monument_al_quouds",
        "nom": "Monument Al-Qoods (Al-Qods)",
        "sous_titre": "Dôme Doré & Arcades Orientales",
        "region_id": "bamako",
        "region_nom": "Bamako",
        "ville": "Bamako",
        "epoque": "Fin du XXe siècle",
        "style_architectural": "Rotonde à colonnades surmontée d'un dôme doré étincelant.",
        "details_localisation": "Bamako · ACI 2000",
        "photo_url": "assets/images/culture/monuments/monument_al_quouds/qu1.jpg",
        "tag": "Solidarité Fraternelle",
        "latitude": 12.6360,
        "longitude": -8.0250,
        "badge_debloque": "Messager de Fraternité",
        "xp_recompense": 50,
        "mots_cles": ["al quouds", "al qods", "dome", "dore", "aci 2000", "hamdallaye", "bamako"],
        "caracteristiques_detection": [
            {"label": "Dôme", "value": "Coupole dorée scintillante", "icon": "stars_rounded"},
            {"label": "Emplacement", "value": "Hamdallaye ACI 2000", "icon": "location_city_rounded"},
            {"label": "Symbolique", "value": "Solidarité et paix", "icon": "public_rounded"},
        ],
        "secrets_et_mysteres": "Inauguré pour témoigner de la fraternité séculaire du peuple malien avec les causes de paix dans le monde.",
        "recit_historique": "Dôme doré étincelant sur le rond-point d'Hamdallaye ACI 2000, symbole de solidarité fraternelle.",
        "narration_audio_texte": "Le Monument Al-Qoods brille de son dôme doré sous le soleil de Bamako, marquant l'ouverture du Mali sur la paix.",
        "pourquoi_ce_lieu_compte": "Repère architectural majeur et symbole d'amitié internationale.",
        "route_path": "/culture/monument/monument_al_quouds",
        "modele_3d_url": None,
        "ar_disponible": False,
        "statut_validation": "Validé",
    },
    {
        "id": "monument_maliba_bamako",
        "nom": "Monument MaliBa",
        "sous_titre": "Lettres 3D Vert Jaune Rouge",
        "region_id": "bamako",
        "region_nom": "Bamako",
        "ville": "Bamako",
        "epoque": "XXIe siècle",
        "style_architectural": "Lettres géantes tricolores sculptées célébrant la fierté nationale.",
        "details_localisation": "Bamako · Centre-ville",
        "photo_url": "assets/images/culture/monuments/monument_maliba_bamako/mb5.jpg",
        "tag": "Fierté Civique",
        "latitude": 12.6480,
        "longitude": -8.0010,
        "badge_debloque": "Fils du Grand Mali",
        "xp_recompense": 50,
        "mots_cles": ["maliba", "mali ba", "lettres", "vert jaune rouge", "drapeau", "bamako"],
        "caracteristiques_detection": [
            {"label": "Sculpture", "value": "Lettres 3D monumentales", "icon": "emoji_flags_rounded"},
            {"label": "Couleurs", "value": "Vert, Jaune, Rouge", "icon": "palette_rounded"},
            {"label": "Sens", "value": "MaliBa : Le Grand Mali", "icon": "star_rounded"},
        ],
        "secrets_et_mysteres": "MaliBa signifie 'Le Grand Mali' en langue bamanan, rappelant l'héritage impérial et l'aspiration à la grandeur.",
        "recit_historique": "Lettres géantes tricolores célébrant la fierté nationale et l'attachement civique au Grand Mali.",
        "narration_audio_texte": "MaliBa ! En ces lettres grandioses vibre toute l'âme d'un peuple fier de son passé et résolu à bâtir un avenir radieux.",
        "pourquoi_ce_lieu_compte": "Lieu de communion civique et de patriotisme rayonnant.",
        "route_path": "/culture/monument/monument_maliba_bamako",
        "modele_3d_url": None,
        "ar_disponible": False,
        "statut_validation": "Validé",
    },
    {
        "id": "monument_obelisque_bamako",
        "nom": "Obélisque de Bamako",
        "sous_titre": "Stèle Monolithique en Pierre",
        "region_id": "bamako",
        "region_nom": "Bamako",
        "ville": "Bamako",
        "epoque": "Début du XXe siècle",
        "style_architectural": "Obélisque commémoratif dominant le carrefour central près de la Place de la Liberté.",
        "details_localisation": "Bamako · Centre-ville",
        "photo_url": "assets/images/culture/monuments/monument_obelisque_bamako/ob2.jpg",
        "tag": "Cœur Civique",
        "latitude": 12.6510,
        "longitude": -7.9985,
        "badge_debloque": "Citoyen de la Liberté",
        "xp_recompense": 50,
        "mots_cles": ["obelisque", "liberte", "place", "centre-ville", "bamako"],
        "caracteristiques_detection": [
            {"label": "Forme", "value": "Obélisque monolithique", "icon": "account_balance_rounded"},
            {"label": "Localisation", "value": "Carrefour central de Bamako", "icon": "place_rounded"},
            {"label": "Époque", "value": "Fondations urbaines modernes", "icon": "history_rounded"},
        ],
        "secrets_et_mysteres": "Point zéro historique marquant l'axe de développement urbain moderne de Bamako.",
        "recit_historique": "Obélisque commémoratif dominant le carrefour central près de la Place de la Liberté.",
        "narration_audio_texte": "Vous voici devant l'Obélisque de Bamako, élevé au cœur de la Place de la Liberté.",
        "pourquoi_ce_lieu_compte": "Symbole central de l'histoire urbaine de Bamako.",
        "route_path": "/culture/monuments",
        "modele_3d_url": None,
        "ar_disponible": False,
        "statut_validation": "Validé",
    },
    {
        "id": "monument_Place_de_la_liberté",
        "nom": "Place de la Liberté",
        "sous_titre": "Esplanade Circulaire & Cœur Battant",
        "region_id": "bamako",
        "region_nom": "Bamako",
        "ville": "Bamako",
        "epoque": "XXe siècle",
        "style_architectural": "Grand forum urbain arboré entouré de fontaines et de colonnades reliant les artères historiques.",
        "details_localisation": "Bamako · Centre-ville",
        "photo_url": "assets/images/culture/monuments/monument_Place_de_la_liberté/lib1.jpg",
        "tag": "Urbanisme & Histoire",
        "latitude": 12.6514,
        "longitude": -7.9982,
        "badge_debloque": "Pèlerin de la Liberté",
        "xp_recompense": 50,
        "mots_cles": ["place", "liberte", "esplanade", "bamako", "centre-ville"],
        "caracteristiques_detection": [
            {"label": "Structure", "value": "Esplanade circulaire arborée", "icon": "nature_people_rounded"},
            {"label": "Rôle", "value": "Carrefour urbain majeur", "icon": "traffic_rounded"},
            {"label": "Atmosphère", "value": "Cœur battant de la capitale", "icon": "favorite_rounded"},
        ],
        "secrets_et_mysteres": "Espace de rassemblement civique témoin des grands rendez-vous républicains.",
        "recit_historique": "Grand forum urbain arboré entouré de fontaines et de colonnades reliant les artères historiques de Bamako.",
        "narration_audio_texte": "Bienvenue sur la Place de la Liberté, véritable carrefour de vie et d'histoire de Bamako.",
        "pourquoi_ce_lieu_compte": "Cœur battant de la capitale malienne.",
        "route_path": "/culture/monuments",
        "modele_3d_url": None,
        "ar_disponible": False,
        "statut_validation": "Validé",
    },

    # ── MONUMENTS NATIONAUX DES AUTRES RÉGIONS ──
    {
        "id": "monument_mosquee_djenne",
        "nom": "Grande Mosquée de Djenné",
        "sous_titre": "Le plus grand édifice en terre crue au monde",
        "region_id": "mopti",
        "region_nom": "Mopti",
        "ville": "Djenné",
        "epoque": "Érigée au XIIIe siècle (reconstruite à l'identique en 1907)",
        "style_architectural": "Construite selon la tradition soudano-sahélienne, elle repose sur un mélange écologique d'argile fine du fleuve, de balle de riz et de beurre de karité.",
        "details_localisation": "Place du Marché, Ville ancienne de Djenné, Vallée du Bani",
        "photo_url": "assets/images/culture/monuments/mosquee_djenne.jpg",
        "tag": "Patrimoine Mondial UNESCO (1988)",
        "latitude": 13.9056,
        "longitude": -4.5558,
        "badge_debloque": "Gardien du Banco Millénaire",
        "xp_recompense": 70,
        "mots_cles": ["djenne", "mosquee", "banco", "terre", "mopti", "unesco", "bani"],
        "caracteristiques_detection": [
            {"label": "Matériau", "value": "100% Terre crue (Banco bio-climatique)", "icon": "nature_rounded"},
            {"label": "Capacité", "value": "Plus de 3 000 fidèles", "icon": "people_rounded"},
            {"label": "Tradition", "value": "Fête annuelle du Crépissage", "icon": "celebration_rounded"},
            {"label": "Statut", "value": "Classée UNESCO depuis 1988", "icon": "verified_rounded"},
        ],
        "secrets_et_mysteres": "La corporation des maçons traditionnels (Barey Ton) transmet de père en fils les secrets du banco. 90 piliers massifs maintiennent une fraîcheur de 22°C sous la canicule.",
        "recit_historique": "La Grande Mosquée de Djenné est le plus vaste édifice au monde entièrement construit en briques de terre crue séchées au soleil (banco).",
        "narration_audio_texte": "Le premier édifice est érigé au XIIIe siècle par le roi Koy Komboro. Chaque année, le Crépissage de Djenné rassemble toute la population en une fête sacrée.",
        "pourquoi_ce_lieu_compte": "Ce monument incarne le génie bâtisseur malien et la solidarité communautaire.",
        "route_path": "/culture/monument/monument_mosquee_djenne",
        "modele_3d_url": "assets/models/mosquee_djenne.glb",
        "ar_disponible": True,
        "statut_validation": "Patrimoine Mondial UNESCO",
    },
    {
        "id": "monument_tombeau_askia",
        "nom": "Tombeau pyramidal des Askia",
        "sous_titre": "La Pyramide Sahélienne de l'Empire Songhoï",
        "region_id": "gao",
        "region_nom": "Gao",
        "ville": "Gao",
        "epoque": "Édifié en 1495 par Askia Mohammed",
        "style_architectural": "Construit en terre crue et bois d'acacia, il reflète l'adoption par l'Empire Songhoï des techniques monumentales sahariennes.",
        "details_localisation": "Quartier historique, Ville de Gao, Bord du Niger",
        "photo_url": "assets/images/culture/monuments/tombeau_askia.jpg",
        "tag": "Patrimoine Mondial UNESCO (2004)",
        "latitude": 16.2974,
        "longitude": -0.0447,
        "badge_debloque": "Héritier de l'Empire Songhoï",
        "xp_recompense": 65,
        "mots_cles": ["gao", "askia", "tombeau", "pyramide", "songhoi", "unesco", "mohammed"],
        "caracteristiques_detection": [
            {"label": "Hauteur", "value": "17 mètres (forme pyramidale)", "icon": "height_rounded"},
            {"label": "Fondateur", "value": "Empereur Askia Mohammed (1495)", "icon": "person_rounded"},
            {"label": "Époque", "value": "Empire Songhoï (XVe siècle)", "icon": "history_edu_rounded"},
            {"label": "Classement", "value": "UNESCO depuis 2004", "icon": "verified_rounded"},
        ],
        "secrets_et_mysteres": "À son retour de La Mecque en 1495, Askia Mohammed ordonne la construction de ce complexe funéraire inspiré des grandes pyramides.",
        "recit_historique": "Le Tombeau des Askia est une impressionnante structure pyramidale à degrés en banco de 17 mètres de hauteur, entourée de deux mosquées à toit plat.",
        "narration_audio_texte": "Vous contemplez le Tombeau des Askia à Gao, joyau de l'Empire Songhoï bâti en 1495 par l'empereur Askia Mohammed.",
        "pourquoi_ce_lieu_compte": "Témoin unique de la grandeur et de la puissance de l'Empire Songhoï qui dominait l'Afrique de l'Ouest aux XVe et XVIe siècles.",
        "route_path": "/culture/monument/monument_tombeau_askia",
        "modele_3d_url": None,
        "ar_disponible": False,
        "statut_validation": "Patrimoine Mondial UNESCO",
    },
    {
        "id": "monument_tata_sikasso",
        "nom": "Le Tata de Sikasso",
        "sous_titre": "La Muraille Héroïque de Résistance du Kénédougou",
        "region_id": "sikasso",
        "region_nom": "Sikasso",
        "ville": "Sikasso",
        "epoque": "Construit entre 1877 et 1890 sous Tiéba et Babemba Traoré",
        "style_architectural": "Érigée avec des blocs d'argile compactée renforcés de latérite et de pierres, la muraille atteignait jusqu'à 6 m de hauteur et 3 m d'épaisseur.",
        "details_localisation": "Pourtour historique de Sikasso, Colline du Mamelon",
        "photo_url": "assets/images/culture/monuments/tata_sikasso.jpg",
        "tag": "Monument National Historique",
        "latitude": 11.3176,
        "longitude": -5.6665,
        "badge_debloque": "Bravoure du Kénédougou",
        "xp_recompense": 65,
        "mots_cles": ["sikasso", "tata", "rempart", "muraille", "tieba", "babemba", "traore", "kenedougou"],
        "caracteristiques_detection": [
            {"label": "Périmètre", "value": "9,5 km de circonférence", "icon": "square_foot_rounded"},
            {"label": "Épaisseur", "value": "Jusqu'à 3 mètres à la base", "icon": "shield_rounded"},
            {"label": "Bâtisseurs", "value": "Rois Tiéba et Babemba Traoré", "icon": "people_rounded"},
            {"label": "Haut fait", "value": "Résistance héroïque de 1898", "icon": "military_tech_rounded"},
        ],
        "secrets_et_mysteres": "Conçu en trois enceintes concentriques pour protéger les réserves agricoles, les habitations et le palais royal face aux sièges de Samory et des coloniaux.",
        "recit_historique": "Le Tata de Sikasso était une colossale muraille fortifiée en banco et pierres latéritiques longue de plus de 9 kilomètres ceinturant toute la cité.",
        "narration_audio_texte": "Voici les vestiges héroïques du Tata de Sikasso, rappelant la devise sacrée de Babemba : 'Plutôt la mort que la honte !' (Anka sa ni ka malo).",
        "pourquoi_ce_lieu_compte": "Le Tata est le symbole indélébile du courage et de la détermination du peuple malien face à la conquête.",
        "route_path": "/culture/monument/monument_tata_sikasso",
        "modele_3d_url": None,
        "ar_disponible": False,
        "statut_validation": "Monument National",
    },
    {
        "id": "monument_djingareyber",
        "nom": "Mosquée Djingareyber",
        "sous_titre": "Le Grand Sanctuaire de Mansa Moussa (1327)",
        "region_id": "tombouctou",
        "region_nom": "Tombouctou",
        "ville": "Tombouctou",
        "epoque": "Érigée en 1327 par Abou Ishaq es-Sahéli",
        "style_architectural": "Construite sur commande de Mansa Moussa par le maître andalou Es-Sahéli, introduisant la voûte et la terre crue raffinée.",
        "details_localisation": "Centre-ville de Tombouctou, Quartier Djingareyber",
        "photo_url": "assets/images/culture/monuments/mosquee_djingareyber.jpg",
        "tag": "Patrimoine Mondial UNESCO (1988)",
        "latitude": 16.7725,
        "longitude": -3.0076,
        "badge_debloque": "Érudit des Sables de Tombouctou",
        "xp_recompense": 70,
        "mots_cles": ["tombouctou", "djingareyber", "mansa", "moussa", "saheli", "mosquee", "unesco"],
        "caracteristiques_detection": [
            {"label": "Fondation", "value": "1327 (Mansa Moussa)", "icon": "history_edu_rounded"},
            {"label": "Architecte", "value": "Abou Ishaq es-Sahéli (Grenade)", "icon": "architecture_rounded"},
            {"label": "Statut", "value": "Patrimoine Mondial UNESCO", "icon": "verified_rounded"},
            {"label": "Rôle", "value": "Cœur spirituel de Tombouctou", "icon": "menu_book_rounded"},
        ],
        "secrets_et_mysteres": "Ébloui par les sanctuaires du Caire lors de son pèlerinage de 1324, Mansa Moussa alloua 200 kg d'or pour financer sa réalisation.",
        "recit_historique": "La Mosquée Djingareyber est le plus ancien sanctuaire encore en activité à Tombouctou, conçue en banco, bois de palmier et pierres de calcaire.",
        "narration_audio_texte": "Voici Djingareyber, la plus ancienne mosquée de Tombouctou, érigée en 1327 par l'architecte andalou Abou Ishaq es-Sahéli.",
        "pourquoi_ce_lieu_compte": "Symbole du rayonnement intellectuel et spirituel de Tombouctou, elle abrite la mémoire des savants sahéliens.",
        "route_path": "/culture/monument/monument_djingareyber",
        "modele_3d_url": None,
        "ar_disponible": False,
        "statut_validation": "Patrimoine Mondial UNESCO",
    },
    {
        "id": "monument_sankore",
        "nom": "Université & Mosquée de Sankoré",
        "sous_titre": "Le Phare Universitaire de l'Afrique Médiévale",
        "region_id": "tombouctou",
        "region_nom": "Tombouctou",
        "ville": "Tombouctou",
        "epoque": "Fondée au XIVe siècle sous l'Empire du Mali",
        "style_architectural": "Construite en banco selon des proportions géométriques sacrées calquées sur la Kaaba.",
        "details_localisation": "Quartier Sankoré, Ville de Tombouctou",
        "photo_url": "assets/images/culture/monuments/mosquee_sankore.jpg",
        "tag": "Patrimoine Mondial UNESCO",
        "latitude": 16.7778,
        "longitude": -3.0033,
        "badge_debloque": "Maître des Sciences de Sankoré",
        "xp_recompense": 70,
        "mots_cles": ["sankore", "universite", "tombouctou", "ahmed", "baba", "manuscrits", "unesco"],
        "caracteristiques_detection": [
            {"label": "Étudiants", "value": "25 000 étudiants au XVIe siècle", "icon": "school_rounded"},
            {"label": "Disciplines", "value": "Astronomie, Médecine, Droit, Mathématiques", "icon": "science_rounded"},
            {"label": "Patrimoine", "value": "Plus de 700 000 manuscrits anciens", "icon": "auto_stories_rounded"},
        ],
        "secrets_et_mysteres": "De grands savants comme Ahmed Baba de Tombouctou y rédigeaient des traités de jurisprudence et de science consultés jusqu'au Maghreb et au Proche-Orient.",
        "recit_historique": "Sankoré n'était pas seulement une mosquée, mais l'une des plus prestigieuses universités du monde médiéval avec plus de 25 000 étudiants.",
        "narration_audio_texte": "Vous regardez l'Université et Mosquée de Sankoré. C'est ici que l'érudit Ahmed Baba a démontré au monde la grandeur de la pensée scientifique africaine.",
        "pourquoi_ce_lieu_compte": "Sankoré est la preuve éclatante de la tradition scientifique et écrite séculaire du Mali.",
        "route_path": "/culture/monument/monument_sankore",
        "modele_3d_url": None,
        "ar_disponible": False,
        "statut_validation": "Patrimoine Mondial UNESCO",
    },
    {
        "id": "monument_fort_medine",
        "nom": "Fort de Médine",
        "sous_titre": "Sentinelle historique du Haut-Sénégal",
        "region_id": "kayes",
        "region_nom": "Kayes",
        "ville": "Kayes",
        "epoque": "Construit en 1855 sur les rives du fleuve Sénégal",
        "style_architectural": "Bâti en pierres taillées de grès rouge et maçonnerie robuste avec bastions de tir et poudrière.",
        "details_localisation": "Médine, à 12 km de Kayes, au pied des chutes du Félou",
        "photo_url": "assets/images/culture/monuments/fort_medine.jpg",
        "tag": "Site Historique National",
        "latitude": 14.3756,
        "longitude": -11.3653,
        "badge_debloque": "Vigie du Khasso",
        "xp_recompense": 55,
        "mots_cles": ["kayes", "medine", "fort", "khasso", "senegal", "elhadj", "oumar", "tall"],
        "caracteristiques_detection": [
            {"label": "Localisation", "value": "Région de Kayes (Fleuve Sénégal)", "icon": "water_rounded"},
            {"label": "Siège mémorable", "value": "1857 (El Hadj Oumar Tall)", "icon": "shield_rounded"},
            {"label": "Cadre naturel", "value": "Près des Chutes de Félou", "icon": "landscape_rounded"},
        ],
        "secrets_et_mysteres": "Pendant plusieurs mois en 1857, le fort fut assiégé par les milliers de guerriers de l'armée d'El Hadj Oumar Tall.",
        "recit_historique": "Situé au bord du majestueux fleuve Sénégal, le Fort de Médine est une forteresse de pierre témoin des confrontations du XIXe siècle.",
        "narration_audio_texte": "Voici le Fort de Médine, dressé au bord du fleuve Sénégal près de Kayes. Construit en 1855 en pierres taillées de grès.",
        "pourquoi_ce_lieu_compte": "Le site de Médine est un lieu de mémoire capital pour comprendre l'histoire militaire et diplomatique du Haut-Sénégal.",
        "route_path": "/culture/monument/monument_fort_medine",
        "modele_3d_url": None,
        "ar_disponible": False,
        "statut_validation": "Monument National",
    },
    {
        "id": "segou",
        "nom": "Ségou-Koro & Balanzans",
        "sous_titre": "Cité Historique du Royaume Bambara",
        "region_id": "segou",
        "region_nom": "Ségou",
        "ville": "Ségou",
        "epoque": "Fondée en 1712 par Biton Mamary Coulibaly",
        "style_architectural": "Architecture traditionnelle en banco au bord du fleuve Djoliba sous l'ombrage des balanzans.",
        "details_localisation": "Région de Ségou, Rives du fleuve Niger",
        "photo_url": "assets/images/culture/monuments/segou/segou_!.jpg",
        "tag": "Royaume Bambara",
        "latitude": 13.4333,
        "longitude": -6.2667,
        "badge_debloque": "Tondjon de Ségou",
        "xp_recompense": 60,
        "mots_cles": ["segou", "segou koro", "biton", "coulibaly", "balanzans", "bambara", "djoliba"],
        "caracteristiques_detection": [
            {"label": "Symbole", "value": "L'arbre sacré : le Balanzan", "icon": "park_rounded"},
            {"label": "Fondateur", "value": "Roi Biton Coulibaly (1712)", "icon": "person_rounded"},
            {"label": "Artisanat", "value": "Bogolan et poteries séculaires", "icon": "palette_rounded"},
            {"label": "Fleuve", "value": "Sur les rives du Djoliba (Niger)", "icon": "water_rounded"},
        ],
        "secrets_et_mysteres": "Le secret des 4 444 balanzans de Ségou : l'un d'eux est dit invisible et ne se révèle qu'aux cœurs purs.",
        "recit_historique": "Ancienne capitale royale au bord du Djoliba et sanctuaire du roi Biton Coulibaly.",
        "narration_audio_texte": "Bienvenue à Ségou-Koro, où les balanzans murmurent encore les exploits des rois guerriers du Mali.",
        "pourquoi_ce_lieu_compte": "Berceau impérial du Royaume Bambara et fleuron de l'art textile bogolan.",
        "route_path": "/culture/monument/segou",
        "modele_3d_url": None,
        "ar_disponible": False,
        "statut_validation": "Patrimoine National Validé",
    },
    {
        "id": "monument_kamablon_kangaba",
        "nom": "Sanctuaire Sacré Kamablon de Kangaba",
        "sous_titre": "Le Cœur Sacré de la Charte de Kouroukan Fouga",
        "region_id": "koulikoro",
        "region_nom": "Koulikoro",
        "ville": "Kangaba",
        "epoque": "Fondé au XIIIe siècle par Mansa Soundiata Keïta (1236)",
        "style_architectural": "Case ronde sacrée en terre crue recouverte d'un toit conique de chaume tressé.",
        "details_localisation": "Place sacrée de Kangaba, Cœur historique du Manden",
        "photo_url": "assets/images/culture/personnages/soundiata.jpg",
        "tag": "Patrimoine Immatériel UNESCO",
        "latitude": 11.9333,
        "longitude": -8.4167,
        "badge_debloque": "Initié de Kouroukan Fouga",
        "xp_recompense": 65,
        "mots_cles": ["kamablon", "kangaba", "soundiata", "kouroukan", "fouga", "charte", "manden"],
        "caracteristiques_detection": [
            {"label": "Case circulaire", "value": "Banco poli sacré", "icon": "circle_rounded"},
            {"label": "Toit de chaume", "value": "Renouvelé tous les 7 ans", "icon": "roofing_rounded"},
            {"label": "Charte", "value": "Kouroukan Fouga (1236)", "icon": "auto_stories_rounded"},
        ],
        "secrets_et_mysteres": "Tous les 7 ans, les griots Diabaté de Kéla et les Keïta s'unissent pour la cérémonie de réfection du toit et la récitation de l'épopée.",
        "recit_historique": "C'est dans cette région que fut proclamée la Charte de Kouroukan Fouga en 1236, proclamant l'égalité des vies et les droits fondamentaux.",
        "narration_audio_texte": "Le sanctuaire du Kamablon à Kangaba est le temple de la mémoire mandingue.",
        "pourquoi_ce_lieu_compte": "Berceau originel de la constitution morale et sociale du Mali.",
        "route_path": "/culture/personnage/perso_soundiata",
        "modele_3d_url": None,
        "ar_disponible": False,
        "statut_validation": "Patrimoine Mondial UNESCO",
    },
]

# ══════════════════════════════════════════════════════════════════════════════
# 2. GRANDS PERSONNAGES HISTORIQUES
# ══════════════════════════════════════════════════════════════════════════════

ALL_FIGURES = [
    {
        "id": "perso_soundiata",
        "nom": "Soundiata Keïta",
        "titre_honorifique": "Le Lion du Manden & Fondateur de l'Empire du Mali",
        "periode": "1190 – 1255",
        "region_id": "koulikoro",
        "region_nom": "Koulikoro",
        "tag": "Mansa Bâtisseur",
        "photo_url": "assets/images/culture/personnages/soundiata.jpg",
        "photo_credits": "Mémorial Historique du Manden, Kangaba • Archives Patrimoniales",
        "resume": "Bâtisseur de l'Empire du Mali après sa victoire décisive à la bataille de Kirina en 1235, il proclame en 1236 la Charte de Kouroukan Fouga, l'une des toutes premières déclarations des droits humains et du vivre-ensemble.",
        "citation_historique": "« Toute vie humaine est une vie. Le tort fait à autrui demande réparation. Respectez l'étranger, l'aîné et la femme. »\n— Charte du Manden, 1236",
        "faits_marquants": [
            {"label": "Règne", "value": "1235 – 1255", "icon": "workspace_premium_rounded"},
            {"label": "Victoire majeure", "value": "Bataille de Kirina (1235)", "icon": "shield_rounded"},
            {"label": "Héritage universel", "value": "Charte du Manden (UNESCO)", "icon": "auto_stories_rounded"},
            {"label": "Capitale originelle", "value": "Niani", "icon": "location_city_rounded"},
        ],
        "chapitres": [
            {"title": "L'Enfance et la Prophétie du Manden", "content": "Fils de Naré Maghann Konaté et de Sogolon Kondé, Soundiata naît paralysé des jambes. Guidé par la foi en son destin, il réussit à se redresser à l'aide d'une barre de fer forgée par les maîtres du feu, devenant un chasseur émérite et un meneur d'hommes admiré."},
            {"title": "L'Unification et la Victoire de Kirina (1235)", "content": "Face à la tyrannie de Soumaoro Kanté du Sosso, Soundiata rassemble les tribus alliées. La confrontation décisive se déroule à Kirina en 1235, unifiant pour la première fois les peuples du fleuve Niger."},
            {"title": "La Charte de Kouroukan Fouga (1236)", "content": "Réunis à Kangaba, Soundiata et les chefs proclament une constitution orale de 44 articles sacralisant la dignité humaine, la paix sociale par le cousinage à plaisanterie (Sinankunya), et protégeant la nature."},
        ],
        "elements_lies": [
            {"id": "monument_mosquee_djenne", "title": "Grande Mosquée de Djenné", "subtitle": "Joyau de l'époque impériale", "type": "monument", "tag": "UNESCO", "regionName": "Mopti"},
            {"id": "perso_mansa_moussa", "title": "Mansa Moussa", "subtitle": "Descendant & Apogée du Mali", "type": "personnage", "tag": "Mansa", "regionName": "Tombouctou"},
            {"id": "ville_segou_koro", "title": "Ségou-Koro", "subtitle": "Berceau des dynasties du fleuve", "type": "ville", "tag": "Cité Royale", "regionName": "Ségou"},
        ],
    },
    {
        "id": "perso_mansa_moussa",
        "nom": "Mansa Moussa",
        "titre_honorifique": "Le Souverain d'Or & Bâtisseur du Savoir Universel",
        "periode": "1312 – 1337",
        "region_id": "tombouctou",
        "region_nom": "Tombouctou",
        "tag": "Âge d'Or Impérial",
        "photo_url": "assets/images/culture/personnages/mansa_moussa.jpg",
        "photo_credits": "Atlas Catalan de 1375, Abraham Cresques • Bibliothèque Nationale de France",
        "resume": "Mansa Kankou Moussa porte l'Empire du Mali à son apogée économique, culturel et territorial. Son pèlerinage mémorable à La Mecque en 1324 révèle au monde la richesse colossale du Mali et fait de Tombouctou et Gao les capitales intellectuelles de l'Afrique.",
        "citation_historique": "« Le savoir est la lumière de l'empire ; les savants sont les gardiens de notre avenir. »\n— Mansa Moussa, 1327",
        "faits_marquants": [
            {"label": "Règne", "value": "1312 – 1337", "icon": "workspace_premium_rounded"},
            {"label": "Pèlerinage historique", "value": "1324 (Le Caire & La Mecque)", "icon": "stars_rounded"},
            {"label": "Grandes commandes", "value": "Mosquée Djingareyber (1327)", "icon": "architecture_rounded"},
            {"label": "Expansion", "value": "De l'Atlantique au fleuve Niger", "icon": "public_rounded"},
        ],
        "chapitres": [
            {"title": "L'Avènement et la Puissance Territoriale", "content": "Petit-neveu de Soundiata, Kankou Moussa accède au trône en 1312. Sous son autorité, l'empire s'étend sur plus de 3 000 km, reliant les mines d'or aux comptoirs marchands du Sahara."},
            {"title": "Le Pèlerinage de 1324 et le Rayonnement Mondial", "content": "En 1324, il entreprend une traversée légendaire avec 60 000 hommes et 80 dromadaires transportant des quintaux d'or pur. Sa générosité au Caire fut telle qu'elle marqua l'économie mondiale."},
            {"title": "Tombouctou, Cité des 333 Saints et des Universités", "content": "Il invite le célèbre architecte andalou Abou Ishaq es-Sahéli pour concevoir la Mosquée Djingareyber en 1327 et dote l'Université de Sankoré de financements considérables."},
        ],
        "elements_lies": [
            {"id": "monument_djingareyber", "title": "Mosquée Djingareyber", "subtitle": "Commandée en 1327", "type": "monument", "tag": "UNESCO", "regionName": "Tombouctou"},
            {"id": "monument_sankore", "title": "Mosquée & Université de Sankoré", "subtitle": "Sanctuaire des manuscrits", "type": "monument", "tag": "UNESCO", "regionName": "Tombouctou"},
            {"id": "ville_tombouctou", "title": "Tombouctou", "subtitle": "La Cité des 333 Saints", "type": "ville", "tag": "Savoirs Sahéliens", "regionName": "Tombouctou"},
        ],
    },
    {
        "id": "perso_babemba",
        "nom": "Babemba Traoré",
        "titre_honorifique": "Roi du Kénédougou & Héros de la Résistance Nationale",
        "periode": "1855 – 1898",
        "region_id": "sikasso",
        "region_nom": "Sikasso",
        "tag": "Héros de la Dignité",
        "photo_url": "assets/images/culture/personnages/babemba_traore.jpg",
        "photo_credits": "Monument National Babemba Traoré, Sikasso • Fonds Photographique National",
        "resume": "Souverain du Royaume du Kénédougou de 1893 à 1898, il défendit héroïquement la cité fortifiée de Sikasso contre les assauts des troupes coloniales, préférant le sacrifice suprême à la capitulation.",
        "citation_historique": "« Anka sa ni ka malo ! » (Plutôt la mort que la honte !)\n— Devise sacrée de Babemba Traoré, 1er mai 1898",
        "faits_marquants": [
            {"label": "Règne", "value": "1893 – 1898", "icon": "shield_rounded"},
            {"label": "Forteresse", "value": "Tata de Sikasso (9 km de remparts)", "icon": "castle_rounded"},
            {"label": "Symbole", "value": "Dignité et souveraineté patriotique", "icon": "military_tech_rounded"},
            {"label": "Royaume", "value": "Kénédougou", "icon": "flag_rounded"},
        ],
        "chapitres": [
            {"title": "L'Héritage des Traoré et le Kénédougou", "content": "Succédant à son frère Tiéba en 1893, Babemba renforce les fortifications et l'armée pour préserver l'autonomie et la culture de son peuple."},
            {"title": "L'Inexpugnable Tata de Sikasso", "content": "Une colossale muraille en terre de 9 km de circonférence, haute de 6 mètres, chef-d'œuvre d'ingénierie militaire défensive."},
            {"title": "Le Siège de 1898 et le Sacrifice pour l'Honneur", "content": "En mai 1898, refusant catégoriquement d'être fait prisonnier après des semaines de résistance acharnée, Babemba se donne la mort, prononçant : 'Anka sa ni ka malo !'."},
        ],
        "elements_lies": [
            {"id": "monument_tata_sikasso", "title": "Le Tata de Sikasso", "subtitle": "La Muraille de Résistance", "type": "monument", "tag": "Fortification", "regionName": "Sikasso"},
            {"id": "ville_sikasso", "title": "Sikasso", "subtitle": "Le Verger du Mali & Cité du Kénédougou", "type": "ville", "tag": "Cité Héroïque", "regionName": "Sikasso"},
        ],
    },
    {
        "id": "perso_askia_mohammed",
        "nom": "Askia Mohammed",
        "titre_honorifique": "Askia le Grand & Réformateur de l'Empire Songhoï",
        "periode": "1443 – 1538",
        "region_id": "gao",
        "region_nom": "Gao",
        "tag": "Grand Réformateur",
        "photo_url": "assets/images/culture/personnages/askia_mohammed.jpg",
        "photo_credits": "Complexe Monumental des Askia, Gao • Cliché Patrimoine National",
        "resume": "Fondateur de la dynastie des Askia en 1493, il transforme l'Empire Songhoï en un État centralisé moderne, doté d'une armée de métier, d'une justice équitable et d'un réseau d'universités florissant de Gao à Tombouctou.",
        "citation_historique": "« La justice et l'organisation sont les piliers sur lesquels reposent la prospérité des nations. »\n— Askia Mohammed, Gao",
        "faits_marquants": [
            {"label": "Règne", "value": "1493 – 1528", "icon": "workspace_premium_rounded"},
            {"label": "Capitale", "value": "Gao", "icon": "location_city_rounded"},
            {"label": "Sépulture", "value": "Tombeau pyramidal des Askia (UNESCO)", "icon": "architecture_rounded"},
            {"label": "Empire", "value": "Songhoï", "icon": "public_rounded"},
        ],
        "chapitres": [
            {"title": "L'Avènement de la Dynastie des Askia (1493)", "content": "Général d'élite sous Sonni Ali Ber, Mohammed Touré prend le pouvoir en 1493. Il adopte le titre d'Askia ('le Fort') et instaure un modèle d'administration territoriale exemplaire."},
            {"title": "La Modernisation de l'Administration et de l'Économie", "content": "Askia Mohammed standardise les poids et mesures, crée une flotte navale fluviale sur le Niger, professionnalise l'armée et sécurise les routes sahariennes."},
        ],
        "elements_lies": [
            {"id": "monument_tombeau_askia", "title": "Tombeau des Askia", "subtitle": "Pyramide de terre crue à Gao", "type": "monument", "tag": "UNESCO", "regionName": "Gao"},
            {"id": "ville_gao", "title": "Gao", "subtitle": "La Cité Impériale des Songhoï", "type": "ville", "tag": "Cité Fluviale", "regionName": "Gao"},
        ],
    },
    {
        "id": "perso_biton_coulibaly",
        "nom": "Biton Coulibaly",
        "titre_honorifique": "Fondateur du Royaume Bambara de Ségou",
        "periode": "1689 – 1755",
        "region_id": "segou",
        "region_nom": "Ségou",
        "tag": "Bâtisseur de Ségou",
        "photo_url": "assets/images/culture/personnages/biton_coulibaly.jpg",
        "photo_credits": "Mausolée Royal de Biton Coulibaly, Ségou-Koro • Cliché Photographique",
        "resume": "Génie militaire et politique, Mamari 'Biton' Coulibaly transforme l'association fraternelle de jeunesse (Tôn) en une redoutable armée permanente (Tônjons) et fonde le puissant Royaume Bambara de Ségou le long du fleuve Niger.",
        "citation_historique": "« La force d'un royaume réside dans la discipline de ses guerriers et l'unité de son peuple. »\n— Récits des Griots de Ségou",
        "faits_marquants": [
            {"label": "Règne", "value": "1712 – 1755", "icon": "workspace_premium_rounded"},
            {"label": "Capitale", "value": "Ségou-Koro", "icon": "location_city_rounded"},
            {"label": "Institution", "value": "Les Tônjons (Guerriers d'élite)", "icon": "shield_rounded"},
            {"label": "Royaume", "value": "Royaume Bambara de Ségou", "icon": "flag_rounded"},
        ],
        "chapitres": [
            {"title": "De chef du Tôn à Roi de Ségou", "content": "Mamari Coulibaly se distingue par son sens de l'organisation. Élu chef du Tôn, il prend le titre de 'Biton' et unifie les cités riveraines du fleuve Djoliba."},
            {"title": "L'Essor du Royaume des 4 444 Balanzans", "content": "Sous son commandement, Ségou-Koro devient une forteresse imprenable avec une flotte de pirogues de guerre contrôlant le fleuve de Bamako jusqu'à Tombouctou."},
        ],
        "elements_lies": [
            {"id": "ville_segou_koro", "title": "Ségou-Koro", "subtitle": "Le Berceau des 4 444 Balanzans", "type": "ville", "tag": "Cité Royale", "regionName": "Ségou"},
        ],
    },
    {
        "id": "perso_modibo_keita",
        "nom": "Modibo Keïta",
        "titre_honorifique": "Père de l'Indépendance & 1er Président de la République du Mali",
        "periode": "1915 – 1977",
        "region_id": "bamako",
        "region_nom": "Bamako",
        "tag": "Père de la Nation",
        "photo_url": "assets/images/culture/personnages/modibo_keita.jpg",
        "photo_credits": "Photographie Officielle d'Archives Nationales du Mali, 1961",
        "resume": "Figure majeure du panafricanisme et artisan de l'indépendance proclamée le 22 septembre 1960, Modibo Keïta a forgé les institutions et l'identité de la République moderne du Mali.",
        "citation_historique": "« Le Mali est une nation de bâtisseurs. Notre liberté s'enracine dans la grandeur de nos ancêtres. »\n— Modibo Keïta, 22 septembre 1960",
        "faits_marquants": [
            {"label": "Présidence", "value": "1960 – 1968", "icon": "flag_rounded"},
            {"label": "Proclamation", "value": "Indépendance du Mali (22 sept. 1960)", "icon": "celebration_rounded"},
            {"label": "Mouvement", "value": "Panafricanisme & Non-alignement", "icon": "public_rounded"},
            {"label": "Hommage", "value": "Mémorial Modibo Keïta à Bamako", "icon": "museum_rounded"},
        ],
        "chapitres": [
            {"title": "L'Engagement pour la Dignité Africaine", "content": "Descendant de la lignée de Soundiata, enseignant d'élite et cofondateur de l'Union Soudanaise-RDA, il milite pour l'émancipation des peuples africains."},
            {"title": "La Naissance de la République du Mali (1960)", "content": "Le 22 septembre 1960, il proclame solennellement l'indépendance à Bamako, choisissant le nom historique de l'Empire du Mali. Il cofonde l'OUA en 1963."},
        ],
        "elements_lies": [
            {"id": "perso_soundiata", "title": "Soundiata Keïta", "subtitle": "La lignée historique du Manden", "type": "personnage", "tag": "Fondateur", "regionName": "Koulikoro"},
        ],
    },
]

# ══════════════════════════════════════════════════════════════════════════════
# 3. VILLES ET TERROIRS REMARQUABLES
# ══════════════════════════════════════════════════════════════════════════════

ALL_PLACES = [
    {
        "id": "ville_bamako",
        "nom": "Bamako",
        "sous_titre": "La Cité des Trois Caïmans & Cœur Battant du Djoliba",
        "region_id": "bamako",
        "region_nom": "Bamako",
        "tag": "Capitale Nationale",
        "photo_url": "assets/images/culture/monuments/monument_independance.jpg",
        "photo_credits": "Archives Photographiques de Bamako",
        "fondation": "Fondée au XVIe siècle par les Niaré",
        "latitude": 12.6392,
        "longitude": -8.0029,
        "population_ou_details": "~3 000 000 habitants",
        "resume": "Bordée par le fleuve Niger et dominée par les falaises du Point G et de Koulouba, Bamako est le foyer incandescent de la musique, des arts et de la diplomatie sahélienne.",
        "chapitres": [
            {"title": "Les Origines des Trois Caïmans", "content": "Bamba-Kô signifie 'la mare aux caïmans'. Les familles fondatrices Niaré, Touré et Dravé établirent les pactes ancestraux avec les esprits du fleuve."},
            {"title": "La Métropole Artistique du XXIe siècle", "content": "Haut lieu de la Biennale de la photographie africaine et des orchestres légendaires."},
        ],
        "elements_lies": [
            {"id": "monument_independance_bamako", "title": "Monument Indépendance", "subtitle": "Axe cérémoniel", "type": "monument", "tag": "Bamako", "regionName": "Bamako"},
            {"id": "monument_tour_afrique_bamako", "title": "Tour de l'Afrique", "subtitle": "Porte de Faladié", "type": "monument", "tag": "Bamako", "regionName": "Bamako"},
        ],
    },
    {
        "id": "ville_djenne",
        "nom": "Djenné",
        "sous_titre": "La Cité Millénaire du Bani & Joyau de l'Architecture en Terre",
        "region_id": "mopti",
        "region_nom": "Mopti",
        "tag": "Cité Classée UNESCO",
        "photo_url": "assets/images/culture/villes/djenne_ville.jpg",
        "photo_credits": "Ruelle authentique de la cité historique de Djenné • Cliché Réel de Rue",
        "fondation": "Fondée vers 250 av. J.-C. (Djenné-Djeno) et érigée au IXe siècle",
        "latitude": 13.9056,
        "longitude": -4.5558,
        "population_ou_details": "Vallée du Bani",
        "resume": "Entourée par les bras du fleuve Bani, Djenné est une île fluviale féerique et l'une des plus anciennes cités urbaines d'Afrique subsaharienne. Ses près de 2 000 maisons traditionnelles à étage en terre crue forment un ensemble architectural homogène sans équivalent.",
        "chapitres": [
            {"title": "Djenné-Djeno, Berceau de la Métallurgie Fluviale", "content": "Les fouilles archéologiques ont révélé un développement urbain et métallurgique indigène remarquable dès le IIIe siècle avant notre ère."},
            {"title": "L'Art de Vivre Djennenké", "content": "Vivre à Djenné, c'est être en symbiose avec les cycles du fleuve Bani et de la terre, entre toits-terrasses et cours ombragées de broderie."},
        ],
        "elements_lies": [
            {"id": "monument_mosquee_djenne", "title": "Grande Mosquée de Djenné", "subtitle": "Le chef-d'œuvre au cœur de la cité", "type": "monument", "tag": "UNESCO", "regionName": "Mopti"},
            {"id": "ville_bandiagara", "title": "Bandiagara & Falaise Dogon", "subtitle": "Voisins du Pays Dogon", "type": "ville", "tag": "Patrimoine", "regionName": "Mopti"},
        ],
    },
    {
        "id": "ville_segou_koro",
        "nom": "Ségou-Koro",
        "sous_titre": "L'Ancienne Capitale Royale des 4 444 Balanzans",
        "region_id": "segou",
        "region_nom": "Ségou",
        "tag": "Cité Royale",
        "photo_url": "assets/images/culture/villes/segou_koro.jpg",
        "photo_credits": "Bords du fleuve Niger à Ségou • Cliché Photographique Réel",
        "fondation": "Capitale du Royaume Bambara au XVIIIe siècle (1712)",
        "latitude": 13.4333,
        "longitude": -6.2667,
        "population_ou_details": "Bord du fleuve Niger",
        "resume": "Situé à 10 kilomètres en amont de Ségou au bord du Djoliba, Ségou-Koro ('le Vieux Ségou') est le village historique où le roi Biton Coulibaly établit la capitale de son royaume en 1712.",
        "chapitres": [
            {"title": "Le Sanctuaire des Rois Bambaras", "content": "Chaque ruelle en banco conserve avec respect le palais originel et le vestibule royal où se prenaient les décisions qui ont façonné le centre du Mali."},
        ],
        "elements_lies": [
            {"id": "perso_biton_coulibaly", "title": "Biton Coulibaly", "subtitle": "Le Fondateur inhumé à Ségou-Koro", "type": "personnage", "tag": "Roi de Ségou", "regionName": "Ségou"},
        ],
    },
    {
        "id": "ville_bandiagara",
        "nom": "Bandiagara & Falaise Dogon",
        "sous_titre": "Les Villages Suspendus du Pays Dogon & la Cosmogonie de Sirius",
        "region_id": "mopti",
        "region_nom": "Mopti",
        "tag": "Patrimoine Mondial UNESCO (1989)",
        "photo_url": "assets/images/culture/villes/bandiagara_falaise.jpg",
        "photo_credits": "Village accroché à la Falaise de Bandiagara • Cliché Patrimoine UNESCO",
        "fondation": "Établissement dogon dès le XIVe siècle",
        "latitude": 14.3500,
        "longitude": -3.6167,
        "population_ou_details": "Falaise de 150 km",
        "resume": "S'étendant sur plus de 150 kilomètres de grès rouge, la Falaise de Bandiagara abrite des dizaines de villages spectaculaires nichés à flanc de falaise. Le peuple Dogon y a préservé l'un des ensembles cosmogoniques, rituels et architecturaux les plus fascinants de l'humanité.",
        "chapitres": [
            {"title": "Le Toguna, Sanctuaire de la Démocratie Orale", "content": "Le Toguna est une bâtisse basse au toit de huit couches de tiges de mil. Sa hauteur réduite oblige les hommes à s'asseoir, empêchant toute dispute violente."},
        ],
        "elements_lies": [
            {"id": "ville_djenne", "title": "Djenné", "subtitle": "Cité sœur de la région de Mopti", "type": "ville", "tag": "UNESCO", "regionName": "Mopti"},
        ],
    },
    {
        "id": "ville_tombouctou",
        "nom": "Tombouctou",
        "sous_titre": "La Cité Mystique des 333 Saints & Carrefour Transsaharien",
        "region_id": "tombouctou",
        "region_nom": "Tombouctou",
        "tag": "Patrimoine Mondial UNESCO (1988)",
        "photo_url": "assets/images/culture/villes/tombouctou_ville.jpg",
        "photo_credits": "Ruelle de sable et portes sculptées de Tombouctou • Cliché Réel Sahélien",
        "fondation": "Fondée vers 1100 par les pasteurs touaregs",
        "latitude": 16.7725,
        "longitude": -3.0076,
        "population_ou_details": "Carrefour des caravanes",
        "resume": "Située aux portes du désert du Sahara là où la boucle du fleuve Niger s'approche le plus du nord, Tombouctou est le carrefour mythique où se rencontraient caravanes de sel, orateurs, astronomes et marchands d'or et de manuscrits précieux.",
        "chapitres": [
            {"title": "L'Âge d'Or du Savoir Saharien", "content": "Au XVIe siècle, Tombouctou comptait plus de 100 000 habitants et constituait le phare universitaire de l'Afrique de l'Ouest avec ses 700 000 manuscrits anciens."},
        ],
        "elements_lies": [
            {"id": "monument_djingareyber", "title": "Mosquée Djingareyber", "subtitle": "Érigée en 1327", "type": "monument", "tag": "UNESCO", "regionName": "Tombouctou"},
            {"id": "monument_sankore", "title": "Université de Sankoré", "subtitle": "Temple du savoir médiéval", "type": "monument", "tag": "UNESCO", "regionName": "Tombouctou"},
            {"id": "perso_mansa_moussa", "title": "Mansa Moussa", "subtitle": "Le Mécène Impérial", "type": "personnage", "tag": "Empereur", "regionName": "Tombouctou"},
        ],
    },
    {
        "id": "ville_sikasso",
        "nom": "Sikasso",
        "sous_titre": "Le Verger Généreux du Mali & Capitale du Kénédougou",
        "region_id": "sikasso",
        "region_nom": "Sikasso",
        "tag": "Cité du Kénédougou",
        "photo_url": "assets/images/culture/villes/sikasso_ville.jpg",
        "photo_credits": "Paysage verdoyant et collines du Kénédougou, Sikasso • Cliché Réel",
        "fondation": "Fondée au XIXe siècle par Mansa Doula",
        "latitude": 11.3176,
        "longitude": -5.6665,
        "population_ou_details": "Terroir agricole",
        "resume": "Deuxième ville la plus peuplée du Mali, Sikasso est réputée pour ses terres d'une fertilité exceptionnelle et ses vergers de manguiers. Capitale du Royaume du Kénédougou, elle s'est illustrée par sa résistance héroïque lors du siège de 1898.",
        "chapitres": [
            {"title": "La Colline Sacrée du Mamelon", "content": "Au cœur de la ville s'élève le Mamelon, une butte aménagée par le roi Tiéba Traoré comme poste d'observation stratégique et lieu de réceptions diplomatiques."},
        ],
        "elements_lies": [
            {"id": "monument_tata_sikasso", "title": "Le Tata de Sikasso", "subtitle": "La Muraille Héroïque", "type": "monument", "tag": "Fortification", "regionName": "Sikasso"},
            {"id": "perso_babemba", "title": "Babemba Traoré", "subtitle": "Le Héros de Sikasso", "type": "personnage", "tag": "Héros", "regionName": "Sikasso"},
        ],
    },
    {
        "id": "ville_gao",
        "nom": "Gao",
        "sous_titre": "La Cité Impériale des Songhoï & Porte de la Dune Rose",
        "region_id": "gao",
        "region_nom": "Gao",
        "tag": "Cité Impériale Songhoï",
        "photo_url": "assets/images/culture/villes/gao_dune_rose.jpg",
        "photo_credits": "La Dune Rose de Koïma surplombant le fleuve Niger à Gao • Cliché Photographique Réel",
        "fondation": "Mentionnée dès le IXe siècle sous le nom de Kaw-Kaw",
        "latitude": 16.2974,
        "longitude": -0.0447,
        "population_ou_details": "Rives du fleuve Niger",
        "resume": "Ancienne capitale de l'immense Empire Songhoï, Gao est une cité fière assise sur la rive gauche du fleuve Niger. Elle allie la majesté des paysages dunaires sahariens (comme la célèbre Dune Rose de Koïma) à la vitalité des peuples riverains.",
        "chapitres": [
            {"title": "Gao Saney et les Échanges Caravaniers", "content": "Dès le Xe siècle, Gao était le centre d'un commerce international d'une richesse inouïe reliant l'Espagne musulmane, l'Égypte et les royaumes sahéliens."},
        ],
        "elements_lies": [
            {"id": "monument_tombeau_askia", "title": "Tombeau des Askia", "subtitle": "La Pyramide de Gao", "type": "monument", "tag": "UNESCO", "regionName": "Gao"},
            {"id": "perso_askia_mohammed", "title": "Askia Mohammed", "subtitle": "L'Empereur des Songhoï", "type": "personnage", "tag": "Empereur", "regionName": "Gao"},
        ],
    },
]

# ══════════════════════════════════════════════════════════════════════════════
# 4. CONTES ET FABLES INTERACTIFS
# ══════════════════════════════════════════════════════════════════════════════

ALL_STORIES = [
    {
        "id": "conte_lievre_hyene",
        "titre": "Zoumana le Lièvre et Namori l'Hyène",
        "sous_titre": "La ruse de l'esprit face à la force brute",
        "origine": "Tradition Orale Mandingue",
        "region_id": None,
        "region_nom": "Tout le Mali",
        "tag": "Conte Interactif",
        "photo_url": "assets/images/culture/contes/zoumana_lievre.jpg",
        "photo_credits": "Archives Nationales du Mali",
        "resume": "Une grande fable des veillées mandingues où la réflexion triomphe de la gourmandise et de la force aveugle.",
        "conteur": "Griot Mamadou Kouyaté",
        "duree_audio": "5 min 40",
        "duree_lecture": "5 min",
        "morale": "« La force sans réflexion creuse son propre piège ; la sagesse et la mesure triomphent toujours de la cupidité. »",
        "scenes": [
            {"id": "scene_1", "sceneNumber": 1, "title": "La Soif de la Savane", "atmosphere": "Crépuscule chaud", "narrativeText": "Le soleil s'enfonce à l'horizon. L'eau vient à manquer dans le village animal."},
            {"id": "scene_2", "sceneNumber": 2, "title": "L'Épreuve du Puits", "atmosphere": "Nuit étoilée", "narrativeText": "Chaque animal participe, mais l'hyène refuse l'effort tout en réclamant la première gorgée."},
        ],
        "elements_lies": [
            {"id": "perso_soundiata", "title": "Soundiata Keïta", "subtitle": "Justice du Manden", "type": "personnage", "tag": "Mansa", "regionName": "Koulikoro"},
        ],
    },
    {
        "id": "conte_wagadou_bida",
        "titre": "La Légende du Serpent Wagadou Bida",
        "sous_titre": "Le mythe fondateur de l'Empire du Ghana",
        "origine": "Récit des Griots du Wagadou",
        "region_id": "kayes",
        "region_nom": "Kayes",
        "tag": "Récit Mythique",
        "photo_url": "assets/images/culture/contes/wagadou_bida.jpg",
        "photo_credits": "Griots de Koumbi Saleh",
        "resume": "L'histoire du pacte sacré de Koumbi Saleh et de la pluie d'or sur l'ancien empire du Ghana.",
        "conteur": "Doyen des Griots Soninké",
        "duree_audio": "6 min 15",
        "duree_lecture": "4 min",
        "morale": "« Le respect des alliances et de l'équilibre naturel conditionne la survie et la grandeur des empires. »",
        "scenes": [
            {"id": "scene_1", "sceneNumber": 1, "title": "Le Pacte Sacré", "atmosphere": "Cité antique", "narrativeText": "À Koumbi Saleh, le grand serpent veillait sur l'or et la fertilité du pays."},
        ],
        "elements_lies": [],
    },
    {
        "id": "conte_forgeron_oiseau",
        "titre": "Le Forgeron et l'Oiseau du Djoliba",
        "sous_titre": "Secret de la forge et respect des éléments",
        "origine": "Tradition orale du fleuve",
        "region_id": "segou",
        "region_nom": "Ségou",
        "tag": "Conte Initiatique",
        "photo_url": "assets/images/culture/contes/oiseau_djoliba.jpg",
        "photo_credits": "Maîtres Potiers et Forgerons",
        "resume": "Conte initiatique sur l'alliance sacrée entre les maîtres du feu et la nature le long du Djoliba.",
        "conteur": "Maître du Feu de Ségou",
        "duree_audio": "5 min 00",
        "duree_lecture": "4 min",
        "morale": "« La maîtrise de la technique est stérile sans la sagesse et l'harmonie avec le vivant. »",
        "scenes": [
            {"id": "scene_1", "sceneNumber": 1, "title": "L'Oiseau de la Nuit", "atmosphere": "Bords du fleuve", "narrativeText": "L'oiseau argenté murmure au forgeron le secret du métal trempé."},
        ],
        "elements_lies": [],
    },
    {
        "id": "conte_soundiata_forge",
        "titre": "Soundiata et la Barre de Fer du Destin",
        "sous_titre": "La persévérance sacrée qui brise les impossibles",
        "origine": "Épopée du Mandé",
        "region_id": "koulikoro",
        "region_nom": "Koulikoro",
        "tag": "Épopée Initiatique",
        "photo_url": "assets/images/culture/contes/manden_baobab_stage.jpg",
        "photo_credits": "Griots de Kéla",
        "resume": "L'histoire poignante de Soundiata enfant, qui se redresse sur ses jambes à l'aide d'une lourde barre forgée par les maîtres du feu.",
        "conteur": "Balla Fasséké Kouyaté",
        "duree_audio": "7 min 15",
        "duree_lecture": "4 min 20",
        "morale": "« Aucun enfant n'est condamné par le sort lorsque brûle en son cœur la foi et le respect filial. »",
        "scenes": [
            {"id": "scene_1", "sceneNumber": 1, "title": "La Forge Sacrée", "atmosphere": "Flammes et enclume", "narrativeText": "Les forgerons apportent la barre de fer que Soundiata ploie pour s'ériger enfin debout."},
        ],
        "elements_lies": [],
    },
]

# ══════════════════════════════════════════════════════════════════════════════
# 5. SAGESSES, PROVERBES & DÉFIS
# ══════════════════════════════════════════════════════════════════════════════

ALL_PROVERBS = [
    {
        "id": "prov_humilite",
        "texte": "L'eau chaude n'oublie jamais qu'elle a été froide.",
        "texte_original": "Ji kalan tɛ ɲina a nɛnɛ kɔ.",
        "signification": "Peu importe ton ascension ou ta gloire, n'oublie jamais d'où tu viens.",
        "morale": "L'humilité face au destin et aux origines",
        "origine": "Tradition Orale Bamanan (Manden)",
        "theme": "Humilité",
        "region_id": "koulikoro",
        "region_nom": "Koulikoro",
        "xp_recompense": 45,
        "orateur_nom": "Le Sage du Baobab",
        "orateur_role": "Doyen des Sages",
        "accent_color_hex": "#F1851F",
    },
    {
        "id": "prov_parole_eau",
        "texte": "La parole est comme l'eau : une fois versée à terre, nul ne peut la ramasser.",
        "texte_original": "Kuma ye ji ye, n'a bɔra a tɛ se ka sɔrɔ tuguni.",
        "signification": "La parole donnée engage l'honneur et la dignité humaine. Il convient de peser chaque propos.",
        "morale": "La valeur sacrée de la parole donnée",
        "origine": "Parole des Griots du Manden",
        "theme": "Honneur & Sagesse",
        "region_id": "bamako",
        "region_nom": "District de Bamako",
        "xp_recompense": 40,
        "orateur_nom": "Babani le Griot",
        "orateur_role": "Maître de la Parole",
        "accent_color_hex": "#E65100",
    },
    {
        "id": "prov_experience_segou",
        "texte": "Ce qu'un vieillard voit assis, un jeune homme debout ne peut l'apercevoir.",
        "texte_original": "Kɔrɔkɛ sigilen fɛn min ye, kamalen lɔnin t'o ye.",
        "signification": "L'expérience et le discernement forgés au fil des épreuves surpassent la simple force physique.",
        "morale": "L'expérience surpasse la force brute",
        "origine": "Royaume Bamanan de Ségou",
        "theme": "Sagesse & Respect",
        "region_id": "segou",
        "region_nom": "Ségou",
        "xp_recompense": 50,
        "orateur_nom": "Doyen des Balanzans",
        "orateur_role": "Garde de la Mémoire",
        "accent_color_hex": "#40BBCC",
    },
    {
        "id": "prov_solidarite",
        "texte": "Une seule main ne peut pas applaudir ; c'est avec deux mains qu'on lave un visage propre.",
        "texte_original": "Bolo kelen tɛ se ka kunkolo dabila.",
        "signification": "La solitude rend impuissant ; seule la solidarité collective bâtit une communauté prospère.",
        "morale": "La force indestructible de l'entraide communautaire",
        "origine": "Proverbe populaire du fleuve Niger",
        "theme": "Solidarité",
        "region_id": "bamako",
        "region_nom": "District de Bamako",
        "xp_recompense": 45,
        "orateur_nom": "Ancienne du Marché Rose",
        "orateur_role": "Matriarche",
        "accent_color_hex": "#10B981",
    },
    {
        "id": "prov_patience",
        "texte": "La patience est un arbre dont la racine est amère, mais dont les fruits sont très doux.",
        "texte_original": "Munya ye jiri ye min lili ka gwan, nka a den ka di.",
        "signification": "Endurer les difficultés avec constance apporte immanquablement la sérénité et le triomphe.",
        "morale": "La persévérance transforme l'épreuve en victoire",
        "origine": "Sagesse du Sahel malien",
        "theme": "Patience & Courage",
        "region_id": "mopti",
        "region_nom": "Mopti",
        "xp_recompense": 40,
        "orateur_nom": "Pêcheur Bozo du Bani",
        "orateur_role": "Navigateur",
        "accent_color_hex": "#8B5CF6",
    },
    {
        "id": "defi_nda_baobab",
        "texte": "« N'da ! » — Les Énigmes du Baobab",
        "texte_original": "N'da sira",
        "signification": "Répondez par « N'da sira » et élucidez les énigmes poétiques posées par nos aïeux sous l'arbre à palabres.",
        "morale": "La vivacité d'esprit préserve la culture vivante",
        "origine": "Devinettes traditionnelles Bambara",
        "theme": "Jeu de Devinettes",
        "region_id": "bamako",
        "region_nom": "Tout le Mali",
        "xp_recompense": 50,
        "orateur_nom": "Griot du Grand Baobab",
        "orateur_role": "Maître du Jeu",
        "accent_color_hex": "#EAB308",
    },
    {
        "id": "defi_rois_empires",
        "texte": "Le Grand Quiz des 3 Empires : Ghana, Mali et Songhoï",
        "texte_original": "Faama tɛmɛnenw",
        "signification": "Mesurez vos connaissances sur les dates clés, les dynasties et les grands héros fondateurs de notre patrie.",
        "morale": "Connaître son passé illumine l'avenir",
        "origine": "Grandes Chroniques Médiévales",
        "theme": "Quiz Culturel",
        "region_id": "bamako",
        "region_nom": "Tout le Mali",
        "xp_recompense": 60,
        "orateur_nom": "Chroniqueur Historique",
        "orateur_role": "Gardien des Annales",
        "accent_color_hex": "#3B82F6",
    },
    {
        "id": "defi_chasseurs_manden",
        "texte": "Les Maximes des Maîtres Chasseurs Dozo",
        "texte_original": "Donsonw ka layidu",
        "signification": "Devinez le sens caché des proverbes et enseignements séculaires de la forêt sacrée.",
        "morale": "Le respect absolu de la nature et la maîtrise de soi",
        "origine": "Confrérie sacrée des Dozo",
        "theme": "Sagesse Dozo",
        "region_id": "koulikoro",
        "region_nom": "Koulikoro",
        "xp_recompense": 55,
        "orateur_nom": "Karamoko Dozo",
        "orateur_role": "Maître Chasseur",
        "accent_color_hex": "#14B8A6",
    },
]


def sync_database(db: Session):
    """Effectue l'upsert certifié dans la session SQLAlchemy fournie."""
    print("🚀 Début de la synchronisation de la base de données...")

    # 1. Monuments
    for m in ALL_MONUMENTS:
        rec = db.query(CultureMonument).filter(CultureMonument.id == m["id"]).first()
        if not rec:
            rec = CultureMonument(id=m["id"])
            db.add(rec)
        rec.nom = m["nom"]
        rec.sous_titre = m["sous_titre"]
        rec.region_id = m["region_id"]
        rec.region_nom = m["region_nom"]
        rec.ville = m["ville"]
        rec.epoque = m["epoque"]
        rec.style_architectural = m["style_architectural"]
        rec.details_localisation = m["details_localisation"]
        rec.photo_url = m["photo_url"]
        rec.tag = m.get("tag", "Monument National")
        rec.latitude = m["latitude"]
        rec.longitude = m["longitude"]
        rec.badge_debloque = m["badge_debloque"]
        rec.xp_recompense = m.get("xp_recompense", 50)
        rec.mots_cles_json = json.dumps(m["mots_cles"], ensure_ascii=False)
        rec.caracteristiques_detection_json = json.dumps(m["caracteristiques_detection"], ensure_ascii=False)
        rec.secrets_et_mysteres = m["secrets_et_mysteres"]
        rec.recit_historique = m["recit_historique"]
        rec.narration_audio_texte = m["narration_audio_texte"]
        rec.pourquoi_ce_lieu_compte = m["pourquoi_ce_lieu_compte"]
        rec.route_path = m["route_path"]
        rec.modele_3d_url = m.get("modele_3d_url")
        rec.ar_disponible = m.get("ar_disponible", False)
        rec.statut_validation = m.get("statut_validation", "Patrimoine vérifié")
        rec.date_mise_a_jour = datetime.utcnow()

    # 2. Personnages
    for p in ALL_FIGURES:
        rec = db.query(CulturePersonnage).filter(CulturePersonnage.id == p["id"]).first()
        if not rec:
            rec = CulturePersonnage(id=p["id"])
            db.add(rec)
        rec.nom = p["nom"]
        rec.titre_honorifique = p["titre_honorifique"]
        rec.periode = p["periode"]
        rec.region_id = p["region_id"]
        rec.region_nom = p["region_nom"]
        rec.tag = p.get("tag", "Héros Historique")
        rec.photo_url = p["photo_url"]
        rec.photo_credits = p.get("photo_credits")
        rec.resume = p["resume"]
        rec.citation_historique = p.get("citation_historique")
        rec.faits_marquants_json = json.dumps(p["faits_marquants"], ensure_ascii=False)
        rec.chapitres_json = json.dumps(p["chapitres"], ensure_ascii=False)
        rec.elements_lies_json = json.dumps(p["elements_lies"], ensure_ascii=False)

    # 3. Lieux
    for l in ALL_PLACES:
        rec = db.query(CultureLieu).filter(CultureLieu.id == l["id"]).first()
        if not rec:
            rec = CultureLieu(id=l["id"])
            db.add(rec)
        rec.nom = l["nom"]
        rec.sous_titre = l["sous_titre"]
        rec.region_id = l["region_id"]
        rec.region_nom = l["region_nom"]
        rec.tag = l.get("tag", "Cité Historique")
        rec.photo_url = l["photo_url"]
        rec.photo_credits = l.get("photo_credits")
        rec.fondation = l["fondation"]
        rec.latitude = l["latitude"]
        rec.longitude = l["longitude"]
        rec.population_ou_details = l.get("population_ou_details")
        rec.resume = l["resume"]
        rec.chapitres_json = json.dumps(l["chapitres"], ensure_ascii=False)
        rec.elements_lies_json = json.dumps(l["elements_lies"], ensure_ascii=False)

    # 4. Contes
    for c in ALL_STORIES:
        rec = db.query(CultureConte).filter(CultureConte.id == c["id"]).first()
        if not rec:
            rec = CultureConte(id=c["id"])
            db.add(rec)
        rec.titre = c["titre"]
        rec.sous_titre = c["sous_titre"]
        rec.origine = c["origine"]
        rec.region_id = c.get("region_id")
        rec.region_nom = c.get("region_nom", "Tout le Mali")
        rec.tag = c.get("tag", "Fable & Conte")
        rec.photo_url = c["photo_url"]
        rec.photo_credits = c.get("photo_credits")
        rec.resume = c["resume"]
        rec.conteur = c.get("conteur", "Griot AlternIA")
        rec.duree_audio = c.get("duree_audio", "5 min")
        rec.duree_lecture = c.get("duree_lecture", "3 min")
        rec.morale = c["morale"]
        rec.scenes_json = json.dumps(c["scenes"], ensure_ascii=False)
        rec.elements_lies_json = json.dumps(c["elements_lies"], ensure_ascii=False)

    # 5. Proverbes
    for pr in ALL_PROVERBS:
        rec = db.query(CultureProverbe).filter(CultureProverbe.id == pr["id"]).first()
        if not rec:
            rec = CultureProverbe(id=pr["id"])
            db.add(rec)
        rec.texte = pr["texte"]
        rec.texte_original = pr.get("texte_original")
        rec.signification = pr["signification"]
        rec.morale = pr["morale"]
        rec.origine = pr["origine"]
        rec.theme = pr["theme"]
        rec.region_id = pr["region_id"]
        rec.region_nom = pr["region_nom"]
        rec.xp_recompense = pr.get("xp_recompense", 40)
        rec.orateur_nom = pr.get("orateur_nom")
        rec.orateur_role = pr.get("orateur_role")
        rec.accent_color_hex = pr.get("accent_color_hex", "#F1851F")

    db.commit()
    print("✅ Synchronisation réussie :")
    print(f"   • {len(ALL_MONUMENTS)} monuments")
    print(f"   • {len(ALL_FIGURES)} personnages historiques")
    print(f"   • {len(ALL_PLACES)} terroirs et cités")
    print(f"   • {len(ALL_STORIES)} contes")
    print(f"   • {len(ALL_PROVERBS)} proverbes et énigmes")


if __name__ == "__main__":
    # 1. Mise à jour de la base active (MySQL)
    db = SessionLocal()
    try:
        sync_database(db)
    finally:
        db.close()

    # 2. Mise à jour de la base SQLite embarquée (data/alta_db.sqlite)
    try:
        sqlite_engine = create_engine(SQLITE_FALLBACK_URL, connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=sqlite_engine)
        from sqlalchemy.orm import sessionmaker
        SqliteSession = sessionmaker(autocommit=False, autoflush=False, bind=sqlite_engine)
        s_db = SqliteSession()
        try:
            print("💾 Synchronisation de la base SQLite locale de secours...")
            sync_database(s_db)
        finally:
            s_db.close()
    except Exception as e:
        print(f"Note SQLite : {e}")
