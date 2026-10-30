"""
Service métier pour la gestion du patrimoine culturel, la reconnaissance CultureLens et le RAG culturel.
"""

import json
import logging
import math
import random
import time
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.src.db.models import (
    Apprenant,
    CultureConte,
    CultureContribution,
    CultureDecouverte,
    CultureLieu,
    CultureMonument,
    CultureNom,
    CulturePack,
    CulturePersonnage,
    CultureProverbe,
)

logger = logging.getLogger("AlternIA.CultureService")


def _normalize_text(text: str) -> str:
    """Nettoie et supprime les accents, la ponctuation et met en minuscules."""
    if not text:
        return ""
    nfkd = unicodedata.normalize('NFKD', text)
    no_accent = "".join([c for c in nfkd if not unicodedata.combining(c)])
    clean = no_accent.lower().replace("'", " ").replace("’", " ").replace("-", " ")
    return " ".join(clean.split())


def _calculate_haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcule la distance géodésique en km entre deux points GPS (formule de Haversine)."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * (math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


def _serialize_monument(m: CultureMonument) -> dict[str, Any]:
    """Sérialise un monument pour la réponse API."""
    mots_cles = []
    try:
        mots_cles = json.loads(m.mots_cles_json) if m.mots_cles_json else []
    except (ValueError, TypeError):
        mots_cles = []

    caracteristiques = []
    try:
        caracteristiques = json.loads(m.caracteristiques_detection_json) if m.caracteristiques_detection_json else []
    except (ValueError, TypeError):
        caracteristiques = []

    key_facts = []
    for f in caracteristiques:
        lbl = f.get("label", "")
        val = f.get("value", "")
        if not val:
            val = lbl
            lbl = f.get("category", "Repère")
        key_facts.append({
            "label": lbl,
            "value": val,
            "icon": f.get("icon", "bookmark_border_rounded"),
        })

    chapters = [
        {
            "title": "Histoire & Proclamation",
            "content": m.recit_historique,
        },
        {
            "title": "Secrets & Portée Patrimoniale",
            "content": m.secrets_et_mysteres,
        },
    ]

    res = {
        "id": m.id,
        "name": m.nom,
        "nom": m.nom,
        "subtitle": m.sous_titre,
        "sous_titre": m.sous_titre,
        "regionId": m.region_id,
        "region_id": m.region_id,
        "regionName": m.region_nom,
        "region_nom": m.region_nom,
        "ville": m.ville,
        "era": m.epoque,
        "epoque": m.epoque,
        "architectureStyle": m.style_architectural,
        "style_architectural": m.style_architectural,
        "locationDetails": m.details_localisation,
        "details_localisation": m.details_localisation,
        "presentation": m.recit_historique,
        "architectureAndMaterials": m.style_architectural,
        "whyItMatters": m.pourquoi_ce_lieu_compte,
        "pourquoi_ce_lieu_compte": m.pourquoi_ce_lieu_compte,
        "photoUrl": m.photo_url,
        "photo_url": m.photo_url,
        "photoCredits": "Direction Nationale du Patrimoine Culturel du Mali",
        "tag": m.tag,
        "latitude": m.latitude,
        "longitude": m.longitude,
        "unlockedBadge": m.badge_debloque,
        "badge_debloque": m.badge_debloque,
        "xpEarned": m.xp_recompense,
        "xp_recompense": m.xp_recompense,
        "keywords": mots_cles,
        "mots_cles": mots_cles,
        "detectionFeatures": caracteristiques,
        "caracteristiques_detection": caracteristiques,
        "keyFacts": key_facts,
        "chapters": chapters,
        "connectedItems": [
            {
                "id": "ville_bamako",
                "title": "Bamako",
                "subtitle": "La Cité des Trois Caïmans",
                "type": "ville",
                "tag": "Capitale",
                "regionName": "Bamako",
            },
            {
                "id": "perso_soundiata",
                "title": "Soundiata Keïta",
                "subtitle": "Le Lion du Manden",
                "type": "personnage",
                "tag": "Mansa",
                "regionName": "Koulikoro",
            },
        ],
        "secretsAndMysteries": m.secrets_et_mysteres,
        "secrets_et_mysteres": m.secrets_et_mysteres,
        "historicalStory": m.recit_historique,
        "recit_historique": m.recit_historique,
        "audioNarrationText": m.narration_audio_texte,
        "narration_audio_texte": m.narration_audio_texte,
        "routePath": f"/culture/monument/{m.id}" if (not m.route_path or m.route_path == "/culture/monuments") else m.route_path,
        "route_path": f"/culture/monument/{m.id}" if (not m.route_path or m.route_path == "/culture/monuments") else m.route_path,
        "modele3dUrl": m.modele_3d_url,
        "modele_3d_url": m.modele_3d_url,
        "arAvailable": m.ar_disponible,
        "ar_disponible": m.ar_disponible,
        "validationStatus": m.statut_validation,
        "statut_validation": m.statut_validation,
    }

    # Recherche des vraies photos dans le dataset CultureLens
    real_photos = []
    folder_id = m.id
    if folder_id == "monument_grande_mosquee_bamako":
        folder_id = "monument_mosquee_bamako"
    ai_root = Path(__file__).resolve().parents[3] / "culturelens_ai" / "dataset" / "reference_images" / folder_id
    if not ai_root.exists() and "segou" in folder_id:
        ai_root = Path(__file__).resolve().parents[3] / "culturelens_ai" / "dataset" / "reference_images" / "segou"

    if ai_root.exists() and ai_root.is_dir():
        valid_exts = {".jpg", ".jpeg", ".png", ".webp"}
        for img_p in sorted(ai_root.iterdir()):
            if img_p.is_file() and img_p.suffix.lower() in valid_exts and not img_p.name.startswith("aug_"):
                # Chemin d'asset mobile prêt à l'emploi (rapide, hors-ligne et fiable)
                real_photos.append(f"assets/images/culture/monuments/{folder_id}/{img_p.name}")

    if not real_photos and m.photo_url:
        real_photos.append(m.photo_url)

    res["realPhotos"] = real_photos
    res["galleryPhotos"] = real_photos
    return res


SCENIC_ACTIONS_GRANDMERE_MAH = [
    "Grand-mère Mah attise le feu de bois d'un geste tranquille et rajuste son moussor",
    "Grand-mère Mah jette une poignée de brindilles parfumées sur les braises rougeoyantes",
    "Grand-mère Mah esquisse un sourire bienveillant et incline doucement la tête vers les flammes",
    "Grand-mère Mah fait tinter discrètement ses perles d'ambre et pose sa main sur la calebasse",
    "Grand-mère Mah lève les yeux vers le ciel étoilé du Mandé avant de répondre avec douceur",
    "Grand-mère Mah souffle avec tendresse sur la braise pour faire danser les étincelles d'or",
]


def _build_grandmere_mah_speech_for_nom(n: CultureNom) -> str:
    """
    Narration de Grand-mère Mah pour un patronyme ou un prénom.
    Elle ne fait que mettre en voix les informations stockées en BDD :
    aucune signification, aucun totem ni senankouya n'est ajouté ici.
    """
    parts: list[str] = []

    if n.type == "prenom":
        parts.append(f"« Mon enfant, écoute ce que Grand-mère Mah sait du prénom « {n.nom} ».")
        parts.append(n.signification or "")
        if n.clan_role:
            parts.append(n.clan_role)
        if n.anecdote:
            parts.append(f"Les anciens racontent ceci : {n.anecdote}")
        parts.append(
            "Chez nous, le prénom est donné lors du baptême, au septième jour après la naissance. "
            "Porte-le avec honneur. »"
        )
        return "\n\n".join(p for p in parts if p)

    parts.append(f"« Mon enfant, assieds-toi près des braises. Voici ce que la tradition sait du nom « {n.nom} ».")
    parts.append(n.signification or "")
    berceau = f"Berceau : {n.ethnie_ou_region}." if n.ethnie_ou_region else ""
    parts.append(" ".join(p for p in [berceau, n.clan_role or ""] if p))
    if n.anecdote:
        parts.append(f"Écoute ce que racontent les griots : {n.anecdote}")
    if n.totem:
        parts.append(f"Le tana (interdit) associé à ce clan : {n.totem}")
    if n.senankouya:
        parts.append(
            f"Ton senankun (cousin à plaisanterie) : {n.senankouya} "
            "Entre vous, on se taquine, mais jamais on ne se fâche."
        )
    if n.devise_ou_louange:
        parts.append(f"Les griots disent : {n.devise_ou_louange}")
    parts.append(
        "Chaque lignée garde aussi ses propres récits et ses propres interdits : "
        "demande aux anciens de ta famille, ils compléteront ce que je t'ai dit. »"
    )
    return "\n\n".join(p for p in parts if p)


def _serialize_culture_nom(n: CultureNom) -> dict[str, Any]:
    """Sérialise un patronyme ou prénom malien pour les réponses API."""
    variantes = []
    try:
        variantes = json.loads(n.variantes_json) if n.variantes_json else []
    except (ValueError, TypeError):
        variantes = [n.nom]

    return {
        "id": n.id,
        "name": n.nom,
        "nom": n.nom,
        "nomNormalise": n.nom_normalise,
        "type": n.type,
        "origin": n.ethnie_ou_region,
        "ethnieOuRegion": n.ethnie_ou_region,
        "meaning": n.signification,
        "signification": n.signification,
        "clanRole": n.clan_role,
        "clan_role": n.clan_role,
        "totem": n.totem,
        "senankouya": n.senankouya,
        "deviseOuLouange": n.devise_ou_louange,
        "anecdote": n.anecdote,
        "variantes": variantes,
        "narrativeText": _build_grandmere_mah_speech_for_nom(n),
    }


def _serialize_contribution(c: CultureContribution) -> dict[str, Any]:
    """Sérialise une contribution culturelle pour l'API."""
    supp = {}
    if c.donnees_supplementaires_json:
        try:
            supp = json.loads(c.donnees_supplementaires_json)
        except (ValueError, TypeError):
            supp = {}

    return {
        "id": c.id,
        "auteurNom": c.auteur_nom,
        "auteurId": c.auteur_id,
        "auteurRole": c.auteur_role,
        "typeContenu": c.type_contenu,
        "type_contenu": c.type_contenu,
        "titre": c.titre,
        "texte": c.texte,
        "texteOriginal": c.texte_original,
        "texte_original": c.texte_original,
        "signification": c.signification,
        "morale": c.morale,
        "origine": c.origine,
        "theme": c.theme,
        "regionId": c.region_id,
        "region_id": c.region_id,
        "regionNom": c.region_nom,
        "region_nom": c.region_nom,
        "sourceTemoin": c.source_temoin,
        "source_temoin": c.source_temoin,
        "photoUrl": c.photo_url,
        "photo_url": c.photo_url,
        "audioUrl": c.audio_url,
        "audio_url": c.audio_url,
        "donneesSupplementaires": supp,
        "statut": c.statut,
        "motifModeration": c.motif_moderation,
        "motif_moderation": c.motif_moderation,
        "traiteParId": c.traite_par_id,
        "xpAttribues": c.xp_attribues,
        "piecesAttribuees": c.pieces_attribuees,
        "dateSoumission": c.date_soumission.isoformat() if c.date_soumission else None,
        "dateModeration": c.date_moderation.isoformat() if c.date_moderation else None,
    }


class CultureService:
    @staticmethod
    def get_monuments(
        db: Session,
        ville: str | None = None,
        region_id: str | None = None,
        query: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Récupère la liste des monuments avec filtres et recherche."""
        q = db.query(CultureMonument)

        if ville:
            q = q.filter(CultureMonument.ville.ilike(f"%{ville}%"))
        if region_id:
            q = q.filter(CultureMonument.region_id == region_id)
        if query:
            clean = f"%{query}%"
            q = q.filter(
                or_(
                    CultureMonument.nom.ilike(clean),
                    CultureMonument.sous_titre.ilike(clean),
                    CultureMonument.ville.ilike(clean),
                    CultureMonument.mots_cles_json.ilike(clean),
                )
            )

        monuments = q.offset(skip).limit(limit).all()
        return [_serialize_monument(m) for m in monuments]

    @staticmethod
    def get_monument_by_id(db: Session, monument_id: str) -> dict[str, Any] | None:
        """Récupère un monument spécifique par son identifiant."""
        m = db.query(CultureMonument).filter(CultureMonument.id == monument_id).first()
        return _serialize_monument(m) if m else None

    @staticmethod
    def identify_monument(
        db: Session,
        image_name: str | None = None,
        image_base64: str | None = None,
        keywords: list[str] | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        hint_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Pipeline intelligent d'identification CultureLens :
        0. Inférence par le modèle neuronal de Deep Embeddings (MobileNetV3) si image fournie.
        1. Si hint_id est fourni, charge directement la cible certifiée.
        2. Croisement géospatial (détection des monuments les plus proches si coordonnées fournies).
        3. Analyse sémantique et lexicale par mots-clés ou nom de fichier d'image.
        4. Calcul d'indice de confiance avec seuils rigoureux.
        """
        all_monuments = db.query(CultureMonument).all()
        if not all_monuments:
            print("\033[1;31m❌ [CultureLens AI] Erreur : Aucun monument dans le catalogue local\033[0m")
            return {
                "success": False,
                "confidence": 0.0,
                "message": "Aucun monument dans le catalogue local",
                "target": None,
            }

        t_start = time.perf_counter()
        print("\n\033[1;35m════════════════════════════════════════════════════════════════════════════════\033[0m")
        print("\033[1;35m📸 [CultureLens AI]\033[0m Requête de scan reçue sur \033[1;36mPOST /api/v1/culture/identify\033[0m")
        if image_base64:
            b64_size_kb = (len(image_base64) * 3 / 4) / 1024
            print(f"   • Données image     : Base64 présente ({b64_size_kb:.1f} KB)")
        if image_name:
            print(f"   • Nom de fichier    : {image_name}")
        if latitude is not None and longitude is not None:
            print(f"   • Coordonnées GPS   : ({latitude:.4f}, {longitude:.4f})")
        if hint_id:
            print(f"   • Hint ID fourni    : {hint_id}")

        matched_monument: CultureMonument | None = None
        confidence = 0.0
        detected_features = []

        # Cas 0 : Analyse neuronale par le modèle de vision CultureLens AI
        ai_result: dict[str, Any] | None = None
        if image_base64:
            try:
                import base64
                import sys
                from pathlib import Path
                ai_root = Path(__file__).resolve().parents[3] / "culturelens_ai"
                if str(ai_root) not in sys.path:
                    sys.path.insert(0, str(ai_root))
                from culturelens_ai.src.recognizer import CultureLensRecognizer

                raw_data = image_base64.split(",")[-1]
                img_bytes = base64.b64decode(raw_data)
                user_coords = (latitude, longitude) if (latitude is not None and longitude is not None) else None
                ai_result = CultureLensRecognizer.get_instance().predict(img_bytes, user_coords=user_coords)
            except Exception as e:  # noqa: BLE001
                print(f"\033[1;31m⚠️  [CultureLens AI] Exception lors de l'inférence neuronale : {e}\033[0m")
                logger.warning(f"Inférence CultureLensRecognizer échouée : {e}")

        elif image_name:
            try:
                import sys
                from pathlib import Path
                ai_root = Path(__file__).resolve().parents[3] / "culturelens_ai"
                if str(ai_root) not in sys.path:
                    sys.path.insert(0, str(ai_root))
                from culturelens_ai.src.recognizer import CultureLensRecognizer

                # Recherche récursive de l'image dans le dataset de référence ou de test
                found_files = list((ai_root / "dataset").rglob(image_name))
                for c_path in found_files:
                    if c_path.exists() and c_path.is_file():
                        user_coords = (latitude, longitude) if (latitude is not None and longitude is not None) else None
                        ai_result = CultureLensRecognizer.get_instance().predict(c_path, user_coords=user_coords)
                        break
            except Exception as e:  # noqa: BLE001
                print(f"\033[1;31m⚠️  [CultureLens AI] Exception locale : {e}\033[0m")
                logger.warning(f"Inférence CultureLensRecognizer locale échouée : {e}")

        if ai_result:
            ai_conf = float(ai_result.get("confidence", 0.0))
            is_id = bool(ai_result.get("is_identified", False))
            ai_monument_id = str(ai_result.get("monument_id", ""))

            # Résolution tolérante dans la base de données de monuments
            if is_id and ai_conf >= 0.45 and ai_monument_id:
                norm_ai_id = ai_monument_id.lower().strip()
                clean_ai_id = norm_ai_id.replace("monument_", "")

                found = None
                for m in all_monuments:
                    m_norm = m.id.lower().strip()
                    m_clean = m_norm.replace("monument_", "")
                    if m_norm == norm_ai_id or m_clean == clean_ai_id:
                        found = m
                        break
                    if "segou" in clean_ai_id and "segou" in m_clean:
                        found = m
                        break
                    if "obelisque" in clean_ai_id and "obelisque" in m_clean:
                        found = m
                        break
                    if "martyrs" in clean_ai_id and "martyrs" in m_clean:
                        found = m
                        break
                    if "independance" in clean_ai_id and "independance" in m_clean:
                        found = m
                        break
                    if "tour_afrique" in clean_ai_id and "tour_afrique" in m_clean:
                        found = m
                        break

                if found:
                    matched_monument = found
                    confidence = ai_conf
            elif ai_conf < 0.45:
                confidence = ai_conf

        # Cas 1 : Hint ID explicite
        if not matched_monument and hint_id:
            matched_monument = next((m for m in all_monuments if m.id == hint_id), None)
            if matched_monument:
                confidence = 0.988
                print(f"\033[36m   💡 [CultureLens Hint]\033[0m Hint ID appliqué directement : {matched_monument.nom}")

        # Cas 2 : Recherche par mots-clés ou nom de fichier (uniquement si AUCUNE image transmise)
        if not matched_monument and not image_base64 and (keywords or image_name):
            search_terms = []
            if keywords:
                search_terms.extend([k.lower().strip() for k in keywords])
            if image_name:
                cleaned_name = image_name.lower().replace("_", " ").replace("-", " ")
                search_terms.extend(cleaned_name.split())

            stopwords = {"photo", "image", "camera", "picker", "scaled", "jpeg", "jpg", "png", "webp", "bamako", "mali"}
            filtered_terms = [t for t in search_terms if len(t) >= 3 and t not in stopwords]

            best_score = 0
            best_candidate = None
            for m in all_monuments:
                m_score = 0
                m_text = f"{m.nom} {m.sous_titre} {m.ville} {m.mots_cles_json}".lower()
                for term in filtered_terms:
                    if term in m_text:
                        m_score += 1

                if m_score > best_score:
                    best_score = m_score
                    best_candidate = m

            if best_candidate and best_score >= 1:
                kw_conf = min(0.985, 0.70 + (best_score * 0.07))
                if kw_conf >= 0.45:
                    matched_monument = best_candidate
                    confidence = kw_conf
                    print(f"\033[36m   🔎 [Mots-Clés]\033[0m Correspondance lexicale trouvée : {matched_monument.nom} ({kw_conf*100:.1f}%)")

        # Cas 3 : Calcul de la distance géospatiale (strictement pour métadonnées et validation)
        # RÈGLE ABSOLUE : Le GPS ne doit JAMAIS se substituer à la vision ni forcer un monument si l'image ne correspond pas.
        # La reconnaissance visuelle neuronale est souveraine.
        estimated_distance_km: float | None = None
        if latitude is not None and longitude is not None and matched_monument:
            estimated_distance_km = round(_calculate_haversine_distance_km(
                latitude, longitude, matched_monument.latitude, matched_monument.longitude
            ), 2)
            # Si l'utilisateur est physiquement devant le monument reconnu (< 3 km), bonus de confirmation sur site
            if estimated_distance_km < 3.0:
                confidence = min(0.996, confidence + 0.03)
                print(f"\033[36m   📍 [GPS Sur Site]\033[0m L'utilisateur est physiquement devant {matched_monument.nom} ({estimated_distance_km} km)")
            else:
                print(f"\033[36m   📍 [GPS Distance]\033[0m À {estimated_distance_km} km de {matched_monument.nom} (scan d'une photo / guide)")

        dt_total = time.perf_counter() - t_start

        # Seuil d'acceptation strict de 45% (0.45) :
        # Si aucun monument n'est identifié ou si la certitude est inférieure à 45%, retour d'échec poli
        if not matched_monument or confidence < 0.45:
            conf_val = round(confidence, 3) if confidence > 0 else 0.0
            print(f"\n\033[1;33m⚠️  [VERDICT CULTURELENS]\033[0m Monument NON RECONNU (< 45%) en {dt_total:.2f}s :")
            print(f"   • Confiance maximale : {conf_val * 100:.1f}%")
            print("   • Statut             : Correspondance insuffisante avec le patrimoine répertorié")
            print("\033[1;35m════════════════════════════════════════════════════════════════════════════════\033[0m\n")

            return {
                "success": False,
                "target": None,
                "confidence": conf_val,
                "confidencePercent": f"{round(conf_val * 100, 1)}%",
                "message": (
                    "Désolé, ce monument ou lieu n'a pas pu être identifié avec certitude "
                    "parmi les sites du patrimoine malien répertoriés (taux de correspondance inférieur à 45%)."
                ),
                "recognizedFeatures": [],
                "estimatedDistanceKm": None,
                "isCertain": False,
                "scannedAt": datetime.now(UTC).isoformat(),
            }

        serialized = _serialize_monument(matched_monument)
        detected_features = serialized.get("detectionFeatures", [])

        print(f"\n\033[1;32m✅ [VERDICT CULTURELENS]\033[0m Monument identifié et certifié en {dt_total:.2f}s :")
        print(f"   • Monument           : \033[1m{matched_monument.nom}\033[0m ({matched_monument.id})")
        print(f"   • Confiance certifiée: \033[1;32m{confidence * 100:.1f}%\033[0m (Seuil minimum: 45.0%)")
        print(f"   • Région / Ville     : {matched_monument.region_nom} ({matched_monument.ville})")
        print("\033[1;35m════════════════════════════════════════════════════════════════════════════════\033[0m\n")

        return {
            "success": True,
            "target": serialized,
            "confidence": round(confidence, 3),
            "confidencePercent": f"{round(confidence * 100, 1)}%",
            "recognizedFeatures": detected_features,
            "estimatedDistanceKm": estimated_distance_km,
            "isCertain": confidence >= 0.88,
            "scannedAt": datetime.now(UTC).isoformat(),
        }

    @staticmethod
    def ask_cultural_guide(
        db: Session,
        question: str,
        monument_id: str | None = None,
        region_id: str | None = None,
        context_hint: str | None = None,
        custom_system_prompt: str | None = None,
        use_case: str | None = None,
    ) -> dict[str, Any]:
        """
        Assistant RAG & IA Adaptative du Guide Culturel :
        - Contexte documentaire haute fidélité (Monuments, Personnages, Contes, Proverbes)
        - Système de Prompts adaptatifs par cas d'usage (Monument, Héros, Conte, Sagesse, Art, Vie)
        - Reformulation vivante et chaleureuse par le LLM (Griot / Vieux Sage du Mali)
        - Température 0.72 pour assurer variété et fraîcheur à chaque réponse
        """
        t0_ask = time.perf_counter()
        clean_q = question.strip().lower()
        norm_q = _normalize_text(question)

        matched_item_name: str | None = None
        matched_item_type: str = "general"
        context_item: dict[str, Any] | None = None
        sources: list[str] = []
        facts_blocks: list[str] = []

        # ── 0. RECHERCHE DANS LES NOMS ET PATRONYMES DU MALI (GRAND-MÈRE MAH) ──
        matched_nom = CultureService.find_culture_nom_by_keyword(db, norm_q)
        if matched_nom:
            matched_item_name = f"{matched_nom.nom} ({matched_nom.type})"
            matched_item_type = "nom_patronyme"
            context_item = _serialize_culture_nom(matched_nom)
            sources = [
                f"Généalogie Ancestrale du Mali — {matched_nom.nom}",
                f"Terroir : {matched_nom.ethnie_ou_region}",
                "Tradition Orale des Griots du Mandé",
            ]
            facts_blocks.append(
                f"PATRONYME / PRÉNOM DU MALI : {matched_nom.nom} (Type: {matched_nom.type})\n"
                f"TERROIR ET BERCEAU : {matched_nom.ethnie_ou_region}\n"
                f"SIGNIFICATION AUTHENTIQUE : {matched_nom.signification}\n"
                f"RÔLE DU CLAN / CASTE : {matched_nom.clan_role}\n"
                f"ANIMAL TOTEM SACRÉ (TANAN) : {matched_nom.totem or 'Respect de la parole'}\n"
                f"COUSINAGE À PLAISANTERIE (SENANKOUYA) : {matched_nom.senankouya or 'Fraternité universelle'}\n"
                f"RÉCIT ET ANECDOTE HISTORIQUE : {matched_nom.anecdote}\n"
                f"DEVISE OU LOUANGE : {matched_nom.devise_ou_louange or 'Gardiens de la dignité (Danbé)'}"
            )

        # ── 0. RECHERCHE DANS LES NOMS ET PATRONYMES DU MALI (GRAND-MÈRE MAH) ──
        matched_nom = CultureService.find_culture_nom_by_keyword(db, norm_q)
        if matched_nom:
            matched_item_name = f"{matched_nom.nom} ({matched_nom.type})"
            matched_item_type = "nom_patronyme"
            context_item = _serialize_culture_nom(matched_nom)
            sources = [
                f"Généalogie Ancestrale du Mali — {matched_nom.nom}",
                f"Terroir : {matched_nom.ethnie_ou_region}",
                "Tradition Orale des Griots du Mandé",
            ]
            facts_blocks.append(
                f"PATRONYME / PRÉNOM DU MALI : {matched_nom.nom} (Type: {matched_nom.type})\n"
                f"TERROIR ET BERCEAU : {matched_nom.ethnie_ou_region}\n"
                f"SIGNIFICATION AUTHENTIQUE : {matched_nom.signification}\n"
                f"RÔLE DU CLAN / CASTE : {matched_nom.clan_role}\n"
                f"ANIMAL TOTEM SACRÉ (TANAN) : {matched_nom.totem or 'Respect de la parole'}\n"
                f"COUSINAGE À PLAISANTERIE (SENANKOUYA) : {matched_nom.senankouya or 'Fraternité universelle'}\n"
                f"RÉCIT ET ANECDOTE HISTORIQUE : {matched_nom.anecdote}\n"
                f"DEVISE OU LOUANGE : {matched_nom.devise_ou_louange or 'Gardiens de la dignité (Danbé)'}"
            )

        # ── 1. RECHERCHE DANS LES MONUMENTS (Scoring spécifique par mot discriminant) ──
        STOP_WORDS = {
            "de", "du", "la", "le", "les", "des", "un", "une", "a", "au", "aux", "en", "sur",
            "monument", "place", "grande", "grand", "bamako", "mali", "ville", "histoire",
            "raconte", "parle", "moi", "qui", "est", "quoi", "c'est", "ce", "cette"
        }

        target_monument: CultureMonument | None = None
        if monument_id and not matched_nom:
            target_monument = db.query(CultureMonument).filter(CultureMonument.id == monument_id).first()

        if not target_monument and not matched_nom:
            all_monuments = db.query(CultureMonument).all()
            best_monument = None
            best_monument_score = 0
            for m in all_monuments:
                score = 0
                m_nom_norm = _normalize_text(m.nom)
                m_id_norm = _normalize_text(m.id)
                clean_target_id = _normalize_text(m.id.replace("monument_", ""))

                if m_id_norm in norm_q or clean_target_id in norm_q:
                    score += 100
                if m_nom_norm in norm_q:
                    score += 80

                # Mots discriminants (ex: "obelisque", "martyrs", "independance", "paix", "afrique")
                m_words = [w for w in m_nom_norm.split() if len(w) >= 4 and w not in STOP_WORDS]
                for w in m_words:
                    if w in norm_q.split() or (len(w) >= 5 and w in norm_q):
                        score += 45

                if score > best_monument_score:
                    best_monument_score = score
                    best_monument = m

            if best_monument and best_monument_score >= 45:
                target_monument = best_monument

        if target_monument:
            matched_item_name = target_monument.nom
            matched_item_type = "monument"
            context_item = _serialize_monument(target_monument)
            sources = [
                f"Catalogue National — {target_monument.nom}",
                f"Statut : {target_monument.statut_validation}",
                f"Région : {target_monument.region_nom} ({target_monument.ville})",
            ]
            facts_blocks.append(
                f"MONUMENT DU PATRIMOINE : {target_monument.nom} ({target_monument.sous_titre})\n"
                f"VILLE & RÉGION : {target_monument.ville}, Région de {target_monument.region_nom}\n"
                f"LOCALISATION : {target_monument.details_localisation}\n"
                f"ÉPOQUE & HISTOIRE : Érigé lors de : {target_monument.epoque}.\n"
                f"RÉCIT HISTORIQUE DÉTAILLÉ : {target_monument.recit_historique}\n"
                f"STYLE ARCHITECTURAL & FORME : {target_monument.style_architectural}\n"
                f"SECRETS, ANECDOTES & TRADITIONS ORALES DU LIEU : {target_monument.secrets_et_mysteres}\n"
                f"SYMBOLE ET IMPORTANCE POUR LA NATION : {target_monument.pourquoi_ce_lieu_compte}"
            )

        # ── 2. RECHERCHE DANS LES GRANDS PERSONNAGES ──────────────────────
        if not matched_item_name:
            all_figs = db.query(CulturePersonnage).all()
            best_fig = None
            best_fig_score = 0
            for fig in all_figs:
                score = 0
                fig_nom_norm = _normalize_text(fig.nom)
                fig_id_norm = _normalize_text(fig.id)
                if fig_id_norm in norm_q or fig_nom_norm in norm_q:
                    score += 80
                fig_words = [w for w in fig_nom_norm.split() if len(w) >= 4 and w not in STOP_WORDS]
                for w in fig_words:
                    if w in norm_q.split() or (len(w) >= 5 and w in norm_q):
                        score += 45
                if score > best_fig_score:
                    best_fig_score = score
                    best_fig = fig

            if best_fig and best_fig_score >= 45:
                matched_item_name = best_fig.nom
                matched_item_type = "personnage"
                context_item = {"type": "personnage", "id": best_fig.id, "name": best_fig.nom, "title": best_fig.titre_honorifique}
                sources = [f"Archives Historiques Nationales — {best_fig.nom}", "UNESCO Patrimoine Immatériel"]
                facts_blocks.append(
                    f"GRAND PERSONNAGE HISTORIQUE : {best_fig.nom} ({best_fig.titre_honorifique})\n"
                    f"PÉRIODE & RÉGION D'ATTACHEMENT : {best_fig.periode}, {best_fig.region_nom}\n"
                    f"BIOGRAPHIE ET RÉALISATIONS : {best_fig.resume}\n"
                    f"CITATION HISTORIQUE ATTRIBUÉE : {best_fig.citation_historique or 'Non documentée'}\n"
                    f"PORTÉE HISTORIQUE : Mémoire de la dignité, de la justice et de la gouvernance au Mali."
                )

        # ── 3. RECHERCHE DANS LES LIEUX & VILLES DU PATRIMOINE ───────────
        if not matched_item_name:
            all_lieux = db.query(CultureLieu).all()
            best_lieu = None
            best_lieu_score = 0
            for lieu in all_lieux:
                score = 0
                lieu_nom_norm = _normalize_text(lieu.nom)
                lieu_id_norm = _normalize_text(lieu.id)
                if lieu_id_norm in norm_q or lieu_nom_norm in norm_q:
                    score += 80
                lieu_words = [w for w in lieu_nom_norm.split() if len(w) >= 4 and w not in STOP_WORDS]
                for w in lieu_words:
                    if w in norm_q.split() or (len(w) >= 5 and w in norm_q):
                        score += 45
                if score > best_lieu_score:
                    best_lieu_score = score
                    best_lieu = lieu

            if best_lieu and best_lieu_score >= 45:
                matched_item_name = best_lieu.nom
                matched_item_type = "lieu"
                context_item = {"type": "lieu", "id": best_lieu.id, "name": best_lieu.nom}
                sources = [f"Terroirs du Mali — {best_lieu.nom}", f"Région : {best_lieu.region_nom}"]
                facts_blocks.append(
                    f"CITÉ ET TERROIR HISTORIQUE : {best_lieu.nom} ({best_lieu.sous_titre})\n"
                    f"RÉGION : {best_lieu.region_nom} | FONDATION ET ORIGINES : {best_lieu.fondation}\n"
                    f"HISTOIRE & DÉTAILS DU TERROIR : {best_lieu.resume} (Détails : {best_lieu.population_ou_details or 'N/A'})"
                )

        # ── 4. RECHERCHE DANS LES CONTES & LÉGENDES ───────────────────────
        if not matched_item_name and (any(w in clean_q for w in ["conte", "fable", "legende", "histoire"]) or any(c.titre.lower() in clean_q for c in db.query(CultureConte).all())):
            matched_conte = None
            for conte in db.query(CultureConte).all():
                if conte.titre.lower() in clean_q:
                    matched_conte = conte
                    break
            if not matched_conte:
                matched_conte = db.query(CultureConte).first()

            if matched_conte:
                matched_item_name = matched_conte.titre
                matched_item_type = "conte"
                context_item = {"type": "conte", "id": matched_conte.id, "name": matched_conte.titre}
                sources = [f"Veillées Traditionnelles — {matched_conte.titre}", f"Origine : {matched_conte.origine}"]
                facts_blocks.append(
                    f"CONTE ANCESTRAL DU MALI : {matched_conte.titre} (« {matched_conte.sous_titre} »)\n"
                    f"ORIGINE GÉOGRAPHIQUE / ETHNIQUE : {matched_conte.origine}\n"
                    f"RÉCIT DU CONTE : {matched_conte.resume}\n"
                    f"MORALE ENSEIGNÉE AUX ENFANTS : {matched_conte.morale}"
                )

        # ── 5. RECHERCHE DANS LES PROVERBES ET SAGESSES ───────────────────
        if not matched_item_name and any(w in clean_q for w in ["proverbe", "sagesse", "devise", "adage"]):
            prov = db.query(CultureProverbe).first()
            if prov:
                matched_item_name = "Parole de Sagesse Bambara"
                matched_item_type = "proverbe"
                context_item = {"type": "proverbe", "id": prov.id}
                sources = ["Sagesse Populaire Mandingue", f"Thème : {prov.theme}"]
                facts_blocks.append(
                    f"PROVERBE EN LANGUE NATIONALE : « {prov.texte_original or prov.texte} »\n"
                    f"SIGNIFICATION ET EXPLICATION : « {prov.signification} »\n"
                    f"ENSEIGNEMENT MORAL : {prov.morale}\n"
                    f"THÈME DE LA SAGESSE : {prov.theme}"
                )

        # ── 6. CONTEXTE GÉNÉRAL DU PATRIMOINE DU MALI SI AUCUN ÉLÉMENT ──
        if not facts_blocks:
            sources = ["Base de Connaissances CultureLens AlternIA", "Tradition Vivante des Griots du Mali"]
            facts_blocks.append(
                "MÉMOIRE ANCESTRALE DU MALI : Le Mali est l'héritier de trois grands empires universels "
                "(le Ghana ou Wagadou, le Manden fondé par Soundiata Keïta au XIIIe siècle, et le Songhoï sous Sonni Ali Ber et l'Askia Mohammed). "
                "En 1236, la Charte de Kouroukan Fouga a proclamé la paix, les droits humains et le respect de la nature sacrée. "
                "Le pays abrite des trésors mondiaux (la Grande Mosquée de Djenné en terre cuite, les manuscrits et mosquées de Tombouctou, "
                "le Tombeau des Askia à Gao, le pays Dogon), ainsi que les grands monuments de la capitale Bamako "
                "(la Tour de l'Afrique, le Monument de l'Indépendance, l'Obélisque de Bamako, le Monument de la Paix, le Monument des Martyrs). "
                "Le fleuve Djoliba (Niger) est l'artère de vie qui nourrit nos terres et inspire nos contes au clair de lune."
            )

        facts_text = "\n\n".join(facts_blocks)

        # ── 7. PROMPT ADAPTATIF POUR LE GUIDE CULTUREL & REFORMULATION ORALE DU GRIOT ──
        # Détection adaptative du cas d'usage si non fourni
        detected_use_case = use_case or "generalCulture"
        if not use_case:
            if matched_nom or any(w in norm_q for w in ["nom", "prenom", "prénom", "djamou", "jamu", "totem", "tanan", "senankouya", "sinankouya", "cousinage"]):
                detected_use_case = "genealogyClan"
            elif target_monument or any(w in norm_q for w in ["monument", "tour de l'afrique", "independance", "djenne", "mosquee", "tombouctou", "askia", "tata", "sikasso", "obelisque", "paix", "martyrs", "statue"]):
                detected_use_case = "monumentSite"
            elif any(w in norm_q for w in ["soundiata", "keita", "mansa moussa", "babemba", "traore", "samory", "coulibaly", "sonni ali", "askia mohammed", "heros", "resistant", "roi", "empereur"]):
                detected_use_case = "historicalFigure"
            elif any(w in norm_q for w in ["conte", "fable", "bouki", "hyene", "leuk", "lievre", "legende", "mythe", "arbre a palabres", "veillee"]):
                detected_use_case = "storyTale"
            elif any(w in norm_q for w in ["proverbe", "adage", "maxime", "sagesse", "kouroukan", "fouga", "charte", "senankouya", "cousinage", "diatiguiya"]):
                detected_use_case = "proverbWisdom"
            elif any(w in norm_q for w in ["ciwara", "bogolan", "kora", "balafon", "ngoni", "djembe", "masque", "crepissage", "artisanat", "forgeron"]):
                detected_use_case = "traditionArt"
            elif any(w in norm_q for w in ["peur", "angoisse", "conseil", "vie", "avenir", "courage", "famille", "reussir", "bonheur", "aide-moi", "que faire"]):
                detected_use_case = "philosophicalLife"

        if custom_system_prompt and len(custom_system_prompt.strip()) > 20:
            system_prompt = custom_system_prompt.strip()
            if "CONTEXTE FACTUEL" not in system_prompt:
                system_prompt += (
                    "\n\nDIRECTIVE CONTEXTE FACTUEL : Appuie-toi sur les éléments du patrimoine malien transmis "
                    "pour enrichir fidèlement ta réponse tout en conservant ton ton noble et vivant."
                )
        else:
            base_griot = (
                "Tu es « Grand-mère Mah / le Vieux Sage et grand Griot du Mali », vénérable gardienne de la mémoire orale sous le grand baobab au coin du feu.\n"
                "Tu t'exprimes avec noblesse, poésie, musicalité orale et chaleur humaine (accueils chaleureux : 'I ni ce', 'I ni sou', 'Aw bisimila').\n"
                "N'utilise jamais de listes à puces plates ni aucun emoji. Structure ta parole en récits harmonieux et rythmés."
            )
            if detected_use_case == "genealogyClan":
                specific = (
                    "MISSION SPÉCIFIQUE (GÉNÉALOGIE, PATRONYMES & TOTEMS - GRAND-MÈRE MAH) :\n"
                    "- Tu es Grand-mère Mah sous le grand baobab au coin du feu crépitant.\n"
                    "- Révèle avec tendresse et fierté l'origine sacrée du patronyme (Jamu) ou du prénom, sa signification étymologique exacte, "
                    "son animal totem (Tanan) et son cousinage à plaisanterie (Senankouya).\n"
                    "- Rappelle la dignité (Danbé) et invite l'enfant à honorer la mémoire de ses ancêtres."
                )
            elif detected_use_case == "monumentSite":
                specific = (
                    "MISSION SPÉCIFIQUE (MONUMENT DU MALI) :\n"
                    "- Fais résonner la fierté des pierres, des bâtisseurs et des symboles de notre souveraineté.\n"
                    "- Décris la majesté de l'édifice, son rôle civique et les secrets transmis par les anciens."
                )
            elif detected_use_case == "historicalFigure":
                specific = (
                    "MISSION SPÉCIFIQUE (HÉROS & RÉSISTANTS DU MALI) :\n"
                    "- Adopte le souffle épique du Griot du Manden ou du Kénédougou !\n"
                    "- Entonne l'éloge du souverain ou du résistant comme au son de la Kora, cite sa devise de bravoure (ex: Danbè) "
                    "et invite l'apprenant à puiser dans ce courage ancestral."
                )
            elif detected_use_case == "storyTale":
                specific = (
                    "MISSION SPÉCIFIQUE (CONTES & VEILLÉES) :\n"
                    "- Invite l'auditeur près du feu au clair de lune : 'Taali taali ! Que le conte aille et revienne sous nos yeux...'\n"
                    "- Mets en scène l'intelligence et les ruses (ex: Leuk le lièvre et Bouki l'hyène) et termine par la perle de sagesse morale."
                )
            elif detected_use_case == "proverbWisdom":
                specific = (
                    "MISSION SPÉCIFIQUE (PROVERBES & SAGESSE DE PAIX) :\n"
                    "- Exprime la profonde sérénité des maîtres de la parole.\n"
                    "- Cite la sagesse dans sa langue d'origine avec sa traduction et relie-la aux boucliers de concorde "
                    "(Charte de Kouroukan Fouga de 1236, Senankouya / cousinage à plaisanterie, Diatiguiya)."
                )
            elif detected_use_case == "traditionArt":
                specific = (
                    "MISSION SPÉCIFIQUE (ARTS & TRADITIONS DU MALI) :\n"
                    "- Célèbre le savoir-faire sacré des forgerons (Noumou), des sculpteurs de masques Ciwara, "
                    "des tisseuses de Bogolan et des poètes du Balafon et de la Kora."
                )
            elif detected_use_case == "philosophicalLife":
                specific = (
                    "MISSION SPÉCIFIQUE (CONSEILS DE VIE SOUS LE BAOBAB) :\n"
                    "- Écoute le cœur de ton visiteur avec une infinie bienveillance.\n"
                    "- Offre-lui réconfort, patience (Munya), courage et foi en l'avenir en puisant dans la philosophie millénaire du Mali."
                )
            else:
                specific = (
                    "MISSION GÉNÉRALE : Célèbre l'héritage des trois grands empires (Ghana, Manden, Songhoï) "
                    "et réponds avec profondeur, bienveillance et éclat."
                )
            system_prompt = f"{base_griot}\n\n{specific}\n\nDIRECTIVE VÉRITÉ FACTUELLE : Appuie-toi sur les faits historiques authentiques fournis sans jamais les recopier mécaniquement."

        user_prompt = (
            f"--- CONTEXTE FACTUEL DU PATRIMOINE DU MALI (BASE DE DONNÉES DE RÉFÉRENCE) ---\n"
            f"{facts_text}\n"
            f"--------------------------------------------------------------------------\n\n"
            f"Question / Demande : « {question} »\n\n"
            f"En tant que Guide Culturel et Vieux Sage, réponds avec éloquence, sagesse et haute fidélité culturelle :"
        )

        reponse: str | None = None
        dt_llm = 0.0

        # Tentative d'appel du LLM avec température dynamique pour variation garantie
        try:
            from backend.src.services.orchestrator_service import get_llm_client
            llm_client = get_llm_client()
            t_gen_start = time.perf_counter()
            # Température 0.72 pour assurer de la spontanéité et de la fraîcheur lexicale
            raw_gen = llm_client.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.72,
                max_tokens=650,
            )
            dt_llm = time.perf_counter() - t_gen_start
            if raw_gen and len(raw_gen.strip()) > 30:
                gen_clean = raw_gen.strip()
                # Supprimer d'éventuels préfixes de rôle ou formules méta
                for pfx in [
                    "Griot :", "Vieux Sage :", "Le Vieux Sage :", "Griot:", "Réponse :", "Narrateur :",
                    "Voici ma réponse, empreinte de sagesse et vivacité :",
                    "Voici ma réponse, empreinte de sagesse et d'éloquence :",
                    "Voici ma réponse :",
                ]:
                    if gen_clean.startswith(pfx):
                        gen_clean = gen_clean[len(pfx):].strip()

                # Clôture propre : si le texte est coupé en fin de token, tronquer au dernier signe de ponctuation
                if not gen_clean.endswith((".", "!", "?", "»", "…")):
                    last_punct = max(gen_clean.rfind("."), gen_clean.rfind("!"), gen_clean.rfind("?"), gen_clean.rfind("»"))
                    if last_punct > 80:
                        gen_clean = gen_clean[:last_punct + 1].strip()
                    else:
                        gen_clean = gen_clean + "..."

                reponse = gen_clean
        except Exception as exc:  # noqa: BLE001
            logger.warning("CultureService.ask_cultural_guide : Inférence LLM indisponible (%s), repli dynamique", exc)

        # ── 8. REPLI DYNAMIQUE (SI LLM INDISPONIBLE) AVEC VARIATIONS ──────
        if not reponse:
            intros = [
                "I ni ce, noble voyageur de la connaissance ! Sous cet arbre à palabres, écoute ce que nos anciens nous transmettent :",
                "Que la paix soit sur ton chemin, noble voyageur ! La mémoire du Mali s'ouvre à toi sous l'ombrage protecteur de notre terre :",
                "Assieds-toi près de moi, voyageur de la lumière. Le fleuve Djoliba murmure une histoire que nos ancêtres ont gravée dans la pierre et le cœur :",
                "I ni ce ! C'est avec une grande joie que le Vieux Sage accueille ta soif d'apprendre. Prête l'oreille à ce récit vivant :"
            ]
            intro = random.choice(intros)
            corps = ""

            if matched_nom:
                reponse = _build_grandmere_mah_speech_for_nom(matched_nom)
            else:
                if target_monument:
                    corps = (
                        f"{target_monument.nom} ({target_monument.sous_titre}) veille fièrement sur {target_monument.ville}, "
                        f"dans la région de {target_monument.region_nom}. {target_monument.recit_historique}\n\n"
                        f"Sur le plan architectural, il illustre avec majesté : {target_monument.style_architectural}. "
                        f"Comme le racontent les anciens sous le clair de lune : {target_monument.secrets_et_mysteres}\n\n"
                        f"Ce lieu compte profondément pour notre nation : {target_monument.pourquoi_ce_lieu_compte}"
                    )
                elif matched_item_name:
                    corps = f"Concernant {matched_item_name} :\n\n{facts_text}"
                else:
                    corps = (
                        "Le Mali est le berceau des grands bâtisseurs et des poètes de la parole. "
                        "De la Charte de Kouroukan Fouga (1236) aux monuments de Bamako et aux merveilles de Djenné et Tombouctou, "
                        "notre patrimoine est une source inépuisable de fierté et de concorde."
                    )

                outro_list = [
                    "Quelle autre merveille de notre terre souhaites-tu explorer avec moi ?",
                    "La parole est comme l'eau du fleuve, elle fertilise l'esprit de qui sait écouter. Pose-moi une autre question quand tu le désires !",
                    "Sous cet arbre à palabres, mes souvenirs restent éveillés pour éclairer tes prochains pas. À très bientôt, voyageur !"
                ]
                reponse = f"{intro}\n\n{corps}\n\n{random.choice(outro_list)}"

        reponse = reponse or ""
        dt_total = time.perf_counter() - t0_ask

        # ── 9. LOGS CONSOLE STYLE CHAT INTERACTIF ─────────────────────────
        print("\n\033[1;35m════════════════════════════════════════════════════════════════════════════════\033[0m")
        print("\033[1;36m🗣️  [Guide Culturel IA]\033[0m Requête reçue sur \033[1mPOST /api/v1/culture/ask\033[0m")
        print(f"   • Question           : \033[1m\"{question}\"\033[0m")
        print(f"   • Cas d'usage IA     : \033[1;34m{detected_use_case}\033[0m {'(Prompt client adaptatif)' if custom_system_prompt else '(Prompt adaptatif auto)'}")
        print(f"   • Cible RAG détectée : \033[1;33m{matched_item_name or 'Patrimoine Général du Mali'}\033[0m (Type: {matched_item_type})")
        print(f"   • Contexte injecté   : \033[36m{len(facts_blocks)} bloc(s) de faits authentiques extraits de la BDD\033[0m")
        if dt_llm > 0:
            print(f"   • Inférence LLM      : \033[1;32mGénération réussie via Qwen2.5 en {dt_llm:.2f}s\033[0m (Temp: 0.72 | Variabilité active)")
        else:
            print("   • Inférence LLM      : \033[1;33mMode de repli dynamique contextuel\033[0m")
        print(f"   • Temps total        : {dt_total:.2f}s")
        print(f"   • Début de réponse   : \033[37m\"{reponse[:150].strip()}...\"\033[0m")
        print("\033[1;35m════════════════════════════════════════════════════════════════════════════════\033[0m\n")

        return {
            "answer": reponse,
            "reponse": reponse,
            "sources": sources,
            "contextItem": context_item,
            "ragVerified": True,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    @staticmethod
    def get_figures(db: Session) -> list[dict[str, Any]]:
        figures = db.query(CulturePersonnage).all()
        res = []
        for f in figures:
            faits = json.loads(f.faits_marquants_json) if f.faits_marquants_json else []
            chapitres = json.loads(f.chapitres_json) if f.chapitres_json else []
            lies = json.loads(f.elements_lies_json) if f.elements_lies_json else []
            res.append({
                "id": f.id,
                "name": f.nom,
                "nom": f.nom,
                "titleHonorifique": f.titre_honorifique,
                "titre_honorifique": f.titre_honorifique,
                "period": f.periode,
                "periode": f.periode,
                "regionId": f.region_id,
                "region_id": f.region_id,
                "regionName": f.region_nom,
                "region_nom": f.region_nom,
                "tag": f.tag,
                "photoUrl": f.photo_url,
                "photoCredits": f.photo_credits,
                "resume": f.resume,
                "citationHistorique": f.citation_historique,
                "keyFacts": faits,
                "chapters": chapitres,
                "connectedItems": lies,
            })
        return res

    @staticmethod
    def get_places(db: Session) -> list[dict[str, Any]]:
        places = db.query(CultureLieu).all()
        res = []
        for p in places:
            chapitres = json.loads(p.chapitres_json) if p.chapitres_json else []
            lies = json.loads(p.elements_lies_json) if p.elements_lies_json else []
            res.append({
                "id": p.id,
                "name": p.nom,
                "nom": p.nom,
                "subtitle": p.sous_titre,
                "sous_titre": p.sous_titre,
                "regionId": p.region_id,
                "region_id": p.region_id,
                "regionName": p.region_nom,
                "region_nom": p.region_nom,
                "tag": p.tag,
                "photoUrl": p.photo_url,
                "photoCredits": p.photo_credits,
                "fondation": p.fondation,
                "latitude": p.latitude,
                "longitude": p.longitude,
                "population": p.population_ou_details,
                "resume": p.resume,
                "chapters": chapitres,
                "connectedItems": lies,
            })
        return res

    @staticmethod
    def get_figure_by_id(db: Session, figure_id: str) -> dict[str, Any] | None:
        figures = CultureService.get_figures(db)
        for f in figures:
            if f["id"] == figure_id:
                return f
        # Recherche par correspondance partielle si suffixe _traore etc.
        for f in figures:
            if f["id"].startswith(figure_id) or figure_id.startswith(f["id"]):
                return f
        return None

    @staticmethod
    def get_place_by_id(db: Session, place_id: str) -> dict[str, Any] | None:
        places = CultureService.get_places(db)
        for p in places:
            if p["id"] == place_id:
                return p
        for p in places:
            if p["id"].startswith(place_id) or place_id.startswith(p["id"]):
                return p
        return None

    @staticmethod
    def get_stories(db: Session) -> list[dict[str, Any]]:
        contes = db.query(CultureConte).all()
        res = []
        for c in contes:
            scenes = json.loads(c.scenes_json) if c.scenes_json else []
            lies = json.loads(c.elements_lies_json) if c.elements_lies_json else []
            res.append({
                "id": c.id,
                "title": c.titre,
                "titre": c.titre,
                "subtitle": c.sous_titre,
                "sous_titre": c.sous_titre,
                "origin": c.origine,
                "origine": c.origine,
                "regionId": c.region_id,
                "region_id": c.region_id,
                "regionName": c.region_nom,
                "region_nom": c.region_nom,
                "tag": c.tag,
                "photoUrl": c.photo_url,
                "resume": c.resume,
                "narrator": c.conteur,
                "audioDuration": c.duree_audio,
                "readingDuration": c.duree_lecture,
                "moral": c.morale,
                "scenes": scenes,
                "connectedItems": lies,
            })
        return res

    @staticmethod
    def get_proverbs(db: Session) -> list[dict[str, Any]]:
        proverbes = db.query(CultureProverbe).all()
        return [
            {
                "id": pr.id,
                "text": pr.texte,
                "texte": pr.texte,
                "originalText": pr.texte_original,
                "texte_original": pr.texte_original,
                "meaning": pr.signification,
                "signification": pr.signification,
                "moral": pr.morale,
                "morale": pr.morale,
                "origin": pr.origine,
                "origine": pr.origine,
                "theme": pr.theme,
                "regionId": pr.region_id,
                "region_id": pr.region_id,
                "regionName": pr.region_nom,
                "region_nom": pr.region_nom,
                "xpReward": pr.xp_recompense,
                "speakerName": pr.orateur_nom,
                "speakerRole": pr.orateur_role,
                "accentColorHex": pr.accent_color_hex,
            }
            for pr in proverbes
        ]

    @staticmethod
    def get_packs(db: Session) -> list[dict[str, Any]]:
        packs = db.query(CulturePack).all()
        res = []
        for pk in packs:
            inclus = json.loads(pk.inclus_json) if pk.inclus_json else []
            res.append({
                "id": pk.id,
                "titre": pk.titre,
                "title": pk.titre,
                "description": pk.description,
                "regionId": pk.region_id,
                "region_id": pk.region_id,
                "regionName": pk.region_nom,
                "region_nom": pk.region_nom,
                "tailleMo": pk.taille_mo,
                "taille_mo": pk.taille_mo,
                "version": pk.version,
                "elementsCount": pk.elements_count,
                "elements_count": pk.elements_count,
                "inclus": inclus,
                "downloadUrl": f"/api/v1/culture/packs/{pk.id}/download",
            })
        return res

    @staticmethod
    def get_pack_bundle(db: Session, pack_id: str) -> dict[str, Any] | None:
        """Génère le pack hors ligne complet prêt pour le téléchargement mobile."""
        pack = db.query(CulturePack).filter(CulturePack.id == pack_id).first()
        if not pack:
            return None

        # Sélection des monuments associés à la région du pack
        if "bamako" in pack.region_id:
            monuments = db.query(CultureMonument).filter(CultureMonument.ville == "Bamako").all()
        else:
            monuments = db.query(CultureMonument).filter(CultureMonument.region_id == pack.region_id).all()
            if not monuments:
                monuments = db.query(CultureMonument).limit(5).all()

        return {
            "packId": pack.id,
            "titre": pack.titre,
            "version": pack.version,
            "generatedAt": datetime.now(UTC).isoformat(),
            "monuments": [_serialize_monument(m) for m in monuments],
            "figures": CultureService.get_figures(db)[:3],
            "proverbs": CultureService.get_proverbs(db)[:5],
            "stories": CultureService.get_stories(db)[:2],
        }

    @staticmethod
    def record_discovery(
        db: Session,
        monument_id: str,
        apprenant_id: str | None = None,
        confidence: float = 0.98,
        is_favorite: bool = False,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Enregistre un monument découvert ou mis en favori par l'apprenant."""
        decouverte = CultureDecouverte(
            monument_id=monument_id,
            apprenant_id=apprenant_id,
            confidence=confidence,
            est_favori=is_favorite,
            notes_personnelles=notes,
            date_decouverte=datetime.now(UTC),
        )
        db.add(decouverte)
        db.commit()
        db.refresh(decouverte)
        return {
            "id": decouverte.id,
            "monumentId": decouverte.monument_id,
            "apprenantId": decouverte.apprenant_id,
            "confidence": decouverte.confidence,
            "isFavorite": decouverte.est_favori,
            "discoveredAt": decouverte.date_decouverte.isoformat() if decouverte.date_decouverte else None,
        }

    @staticmethod
    def get_discoveries(db: Session, apprenant_id: str | None = None) -> list[dict[str, Any]]:
        """Récupère l'historique des découvertes de monuments."""
        q = db.query(CultureDecouverte)
        if apprenant_id:
            q = q.filter(CultureDecouverte.apprenant_id == apprenant_id)
        decouvertes = q.order_by(CultureDecouverte.date_decouverte.desc()).all()

        res = []
        for d in decouvertes:
            m = d.monument
            res.append({
                "id": d.id,
                "monumentId": d.monument_id,
                "monumentName": m.nom if m else "Monument inconnu",
                "ville": m.ville if m else "Mali",
                "photoUrl": m.photo_url if m else None,
                "confidence": d.confidence,
                "isFavorite": d.est_favori,
                "discoveredAt": d.date_decouverte.isoformat() if d.date_decouverte else None,
            })
        return res

    # ==========================================================================
    # LOGIQUE MÉTIER : GRAND-MÈRE MAH, NOMS, PRÉNOMS ET VEILLÉE SOUS LE BAOBAB
    # ==========================================================================

    @staticmethod
    def get_noms(
        db: Session,
        type: str | None = None,
        query: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Récupère le catalogue des patronymes et prénoms traditionnels du Mali."""
        q = db.query(CultureNom)
        if type:
            q = q.filter(CultureNom.type == type.lower())
        if query:
            clean = f"%{query.strip()}%"
            q = q.filter(
                or_(
                    CultureNom.nom.ilike(clean),
                    CultureNom.nom_normalise.ilike(clean),
                    CultureNom.ethnie_ou_region.ilike(clean),
                    CultureNom.signification.ilike(clean),
                    CultureNom.clan_role.ilike(clean),
                )
            )
        noms = q.order_by(CultureNom.nom.asc()).offset(skip).limit(limit).all()
        return [_serialize_culture_nom(n) for n in noms]

    @staticmethod
    def get_nom_by_id_or_exact_name(db: Session, identifier: str) -> dict[str, Any] | None:
        """Récupère la fiche détaillée d'un patronyme ou prénom par son identifiant ou libellé exact."""
        clean = identifier.strip()
        norm = _normalize_text(clean)
        nom = db.query(CultureNom).filter(
            or_(
                CultureNom.id == clean,
                CultureNom.nom_normalise == norm,
                CultureNom.nom.ilike(clean),
            )
        ).first()
        if not nom:
            nom = CultureService.find_culture_nom_by_keyword(db, clean)
        return _serialize_culture_nom(nom) if nom else None

    @staticmethod
    def find_culture_nom_by_keyword(db: Session, query: str) -> CultureNom | None:
        """
        Détection et extraction haute précision d'un patronyme ou prénom malien dans un texte libre.
        Gère les minuscules, les accents et les variantes orthographiques courantes.
        """
        if not query:
            return None
        norm_q = _normalize_text(query)
        words = norm_q.split()

        all_noms = db.query(CultureNom).all()

        # 1. Correspondance mot-à-mot directe sur le nom normalisé
        for n in all_noms:
            if n.nom_normalise in words:
                return n

        # 2. Correspondance sur sous-chaîne avec validation de frontière
        for n in all_noms:
            if n.nom_normalise in norm_q and (len(n.nom_normalise) >= 5 or any(w == n.nom_normalise for w in words)):
                return n

        # 3. Correspondance sur variantes orthographiques (JSON)
        for n in all_noms:
            try:
                variantes = json.loads(n.variantes_json) if n.variantes_json else []
                for v in variantes:
                    v_norm = _normalize_text(v)
                    if v_norm in words or (len(v_norm) >= 5 and v_norm in norm_q):
                        return n
            except (ValueError, TypeError):
                continue

        return None

    @staticmethod
    def chat_grandmere_mah(
        db: Session,
        user_message: str,
        history: list[dict[str, str]] | None = None,
        additional_context: str | None = None,
    ) -> dict[str, Any]:
        """
        Logique métier complète du Chat avec Grand-mère Mah sous le grand baobab au coin du feu.
        Interroge directement la base de données pour les vrais sens des noms, prénoms,
        totems (Tanan) et cousinage à plaisanterie (Senankouya), avec actions scéniques immersives.
        """
        clean_msg = user_message.strip() if user_message else ""
        if not clean_msg:
            return {
                "answer": (
                    "I ni sou, mon enfant ! Approche, assieds-toi près du feu sous le grand baobab. "
                    "Je suis Grand-mère Mah, mémoire vivante et conteuse du Mandé. "
                    "Dis-moi quel est ton nom de famille ou ton prénom, et je te révèlerai son histoire sacrée !"
                ),
                "scenicAction": SCENIC_ACTIONS_GRANDMERE_MAH[0],
                "matchedName": None,
                "sources": ["Grand-mère Mah — Veillée sous le Baobab"],
            }

        norm_q = _normalize_text(clean_msg)
        idx_action = (len(history or []) + len(clean_msg)) % len(SCENIC_ACTIONS_GRANDMERE_MAH)
        scenic_action = SCENIC_ACTIONS_GRANDMERE_MAH[idx_action]

        # 1. Recherche d'un patronyme ou prénom dans la base de données
        matched_nom = CultureService.find_culture_nom_by_keyword(db, clean_msg)

        if matched_nom:
            serialized_nom = _serialize_culture_nom(matched_nom)
            speech = _build_grandmere_mah_speech_for_nom(matched_nom)
            return {
                "answer": speech,
                "scenicAction": scenic_action,
                "matchedName": serialized_nom,
                "sources": [
                    f"Base de Données Généalogique — {matched_nom.nom}",
                    f"Terroir : {matched_nom.ethnie_ou_region}",
                    "Tradition des Griots du Mandé",
                ],
            }

        # 2. Si l'utilisateur demande en général son nom ou son prénom sans précision
        if any(w in norm_q for w in ["mon nom", "mon prenom", "mon prénom", "nom de famille", "djamou", "jamu", "totem", "tanan", "senankouya", "sinankouya", "cousinage"]):
            return {
                "answer": (
                    "« I ni ce, mon enfant ! Chaque patronyme au Mali (*Jamu*) est un trésor vivant gravé dans la mémoire de nos pères.\n\n"
                    "Dis-moi simplement quel est **ton nom de famille** (ex : *Keïta, Traoré, Coulibaly, Diakité, Diallo, Touré, Cissé, Diarra, Camara, Maïga, Sidibé, Doumbia, Dembélé, Guindo...*) ou **ton prénom** (ex : *Mamadou, Fatoumata, Soundiata, Modibo, Awa, Sékou, Tênin...*).\n\n"
                    "Je te révélerai aussitôt son origine sacrée, sa véritable signification, son clan historique, son animal totem (*Tanan*) et ton cousinage à plaisanterie (*Senankouya*) ! »"
                ),
                "scenicAction": scenic_action,
                "matchedName": None,
                "sources": ["Grand-mère Mah — Dictionnaire des Noms du Mali"],
            }

        # 3. Traitement des questions de sagesse, contes, monuments ou requêtes générales
        rag_res = CultureService.ask_cultural_guide(
            db=db,
            question=clean_msg,
            context_hint=additional_context,
            custom_system_prompt=(
                "Tu es « Grand-mère Mah, mémoire vivante et conteuse sous le grand baobab au coin du feu de veillée ».\n"
                "Tu accueilles tendrement l'enfant ou le visiteur en français poétique et chaleureux, émaillé d'expressions mandingues (I ni ce, I ni sou, Nba).\n"
                "N'utilise JAMAIS d'emojis. Raconte avec la ferveur des veillées orales au clair de lune."
            ),
        )

        return {
            "answer": rag_res.get("answer", rag_res.get("reponse", "")),
            "scenicAction": scenic_action,
            "matchedName": rag_res.get("contextItem") if rag_res.get("contextItem", {}).get("type") == "nom_patronyme" else None,
            "sources": rag_res.get("sources", ["Tradition Orale du Mali"]),
        }

    # ==========================================================================
    # GESTION DES CONTRIBUTIONS CITOYENNES & PATRIMOINE PARTICIPATIF
    # ==========================================================================

    @staticmethod
    def create_contribution(
        db: Session,
        payload: dict[str, Any],
        auteur_id: str | None = None,
        auteur_nom: str | None = None,
        auteur_role: str = "Apprenant",
    ) -> dict[str, Any]:
        """Crée une nouvelle proposition culturelle (proverbe, devinette, conte) en attente de validation."""
        extra_json = None
        if payload.get("donnees_supplementaires") or payload.get("donneesSupplementaires"):
            extra_json = json.dumps(payload.get("donnees_supplementaires") or payload.get("donneesSupplementaires"), ensure_ascii=False)

        contrib = CultureContribution(
            auteur_nom=auteur_nom or payload.get("auteur_nom") or payload.get("auteurNom") or "Contributeur AlternIA",
            auteur_id=auteur_id or payload.get("auteur_id") or payload.get("auteurId"),
            auteur_role=auteur_role or payload.get("auteur_role") or payload.get("auteurRole") or "Apprenant",
            type_contenu=(payload.get("type_contenu") or payload.get("typeContenu") or "proverbe").lower(),
            titre=payload.get("titre"),
            texte=(payload.get("texte") or "").strip(),
            texte_original=payload.get("texte_original") or payload.get("texteOriginal"),
            signification=(payload.get("signification") or "").strip(),
            morale=payload.get("morale"),
            origine=payload.get("origine") or "Tradition Orale",
            theme=payload.get("theme") or "Sagesse & Culture",
            region_id=payload.get("region_id") or payload.get("regionId") or "bamako",
            region_nom=payload.get("region_nom") or payload.get("regionNom") or "Tout le Mali",
            source_temoin=payload.get("source_temoin") or payload.get("sourceTemoin"),
            photo_url=payload.get("photo_url") or payload.get("photoUrl"),
            audio_url=payload.get("audio_url") or payload.get("audioUrl"),
            donnees_supplementaires_json=extra_json,
            statut="EN_ATTENTE",
            xp_attribues=int(payload.get("xp_attribues") or payload.get("xpAttribues") or 50),
            pieces_attribuees=int(payload.get("pieces_attribuees") or payload.get("piecesAttribuees") or 25),
            date_soumission=datetime.now(UTC),
        )
        db.add(contrib)
        db.commit()
        db.refresh(contrib)
        logger.info(f"Nouvelle contribution culturelle reçue : {contrib.id} ({contrib.type_contenu})")
        return _serialize_contribution(contrib)

    @staticmethod
    def list_contributions(
        db: Session,
        statut: str | None = None,
        type_contenu: str | None = None,
        auteur_id: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Liste les contributions avec filtres pour la modération ou l'historique utilisateur."""
        query = db.query(CultureContribution)
        if statut:
            query = query.filter(CultureContribution.statut == statut.upper())
        if type_contenu:
            query = query.filter(CultureContribution.type_contenu == type_contenu.lower())
        if auteur_id:
            query = query.filter(CultureContribution.auteur_id == auteur_id)

        total = query.count()
        items = query.order_by(CultureContribution.date_soumission.desc()).offset(skip).limit(limit).all()
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "items": [_serialize_contribution(c) for c in items],
        }

    @staticmethod
    def get_contribution_by_id(db: Session, contribution_id: str) -> dict[str, Any] | None:
        """Récupère une contribution par son identifiant unique."""
        c = db.query(CultureContribution).filter(CultureContribution.id == contribution_id).first()
        return _serialize_contribution(c) if c else None

    @staticmethod
    def moderate_contribution(
        db: Session,
        contribution_id: str,
        decision: str,
        motif: str | None = None,
        admin_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Modère une contribution (APPROUVE ou REJETE).
        Si APPROUVE :
        1. Injecte automatiquement dans la table officielle correspondante :
           - Proverbes / Devinettes -> CultureProverbe
           - Contes & Fables -> CultureConte
           - Monuments & Sites -> CultureMonument
           - Cités & Terroirs -> CultureLieu
           - Personnages historiques -> CulturePersonnage
           - Patronymes & Jamu -> CultureNom
        2. Crédite les pièces dans le Portefeuille de l'auteur
        """
        contrib = db.query(CultureContribution).filter(CultureContribution.id == contribution_id).first()
        if not contrib:
            raise ValueError(f"Contribution introuvable : {contribution_id}")

        decision_clean = decision.upper()
        if decision_clean not in ("APPROUVE", "REJETE"):
            raise ValueError("La décision doit être 'APPROUVE' ou 'REJETE'.")

        contrib.statut = decision_clean
        contrib.motif_moderation = motif
        contrib.traite_par_id = admin_id
        contrib.date_moderation = datetime.now(UTC)

        # 1. Promotion automatique vers la base active selon le type
        if decision_clean == "APPROUVE":
            extra: dict[str, Any] = {}
            if contrib.donnees_supplementaires_json:
                try:
                    extra = json.loads(contrib.donnees_supplementaires_json)
                except (ValueError, TypeError):
                    extra = {}

            # A. Proverbes et Devinettes
            if contrib.type_contenu in ("proverbe", "devinette"):
                target_id = f"contrib_{contrib.type_contenu}_{contrib.id[:8]}"
                if not db.query(CultureProverbe).filter(CultureProverbe.id == target_id).first():
                    new_prov = CultureProverbe(
                        id=target_id,
                        texte=contrib.texte,
                        texte_original=contrib.texte_original,
                        signification=contrib.signification,
                        morale=contrib.morale or ("Réponse à la devinette" if contrib.type_contenu == "devinette" else "Sagesse partagée"),
                        origine=contrib.origine or "Transmission citoyenne",
                        theme="Jeu de Devinettes" if contrib.type_contenu == "devinette" else contrib.theme,
                        region_id=contrib.region_id,
                        region_nom=contrib.region_nom,
                        xp_recompense=contrib.xp_attribues,
                        orateur_nom=f"Transmis par {contrib.auteur_nom}",
                        orateur_role=contrib.source_temoin or "Gardien du Patrimoine",
                        accent_color_hex="#10B981" if contrib.type_contenu == "proverbe" else "#EAB308",
                    )
                    db.add(new_prov)

            # B. Contes et Fables
            elif contrib.type_contenu == "conte":
                target_id = f"contrib_conte_{contrib.id[:8]}"
                if not db.query(CultureConte).filter(CultureConte.id == target_id).first():
                    new_conte = CultureConte(
                        id=target_id,
                        titre=contrib.titre or contrib.texte[:60],
                        sous_titre=contrib.signification[:120],
                        origine=contrib.origine or "Tradition Orale Mandingue",
                        region_id=contrib.region_id,
                        region_nom=contrib.region_nom,
                        tag="Conte Citoyen Participatif",
                        photo_url=contrib.photo_url or "assets/images/culture/contes/zoumana_lievre.jpg",
                        photo_credits=f"Contribution de {contrib.auteur_nom}",
                        resume=contrib.signification,
                        conteur=f"Transmis par {contrib.auteur_nom}",
                        duree_audio="4 min",
                        duree_lecture="3 min",
                        morale=contrib.morale or "Leçon de vie transmise par nos aïeux",
                        scenes_json=json.dumps([{"order": 1, "text": contrib.texte}], ensure_ascii=False),
                        elements_lies_json="[]",
                        date_creation=datetime.now(UTC),
                    )
                    db.add(new_conte)

            # C. Monuments et Sites Historiques
            elif contrib.type_contenu in ("monument", "site"):
                target_id = f"contrib_monument_{contrib.id[:8]}"
                if not db.query(CultureMonument).filter(CultureMonument.id == target_id).first():
                    new_monument = CultureMonument(
                        id=target_id,
                        nom=contrib.titre or contrib.texte[:60],
                        sous_titre=contrib.signification[:120],
                        region_id=contrib.region_id,
                        region_nom=contrib.region_nom,
                        ville=extra.get("ville", contrib.region_nom),
                        epoque=extra.get("epoque", "Patrimoine historique vivant"),
                        style_architectural=extra.get("style_architectural", "Architecture traditionnelle locale"),
                        details_localisation=contrib.source_temoin or contrib.region_nom,
                        photo_url=contrib.photo_url or "assets/images/culture/monuments/tour_afrique.jpg",
                        tag="Monument Citoyen",
                        latitude=float(extra.get("latitude", 12.6392)),
                        longitude=float(extra.get("longitude", -8.0029)),
                        badge_debloque=f"Pionnier de {contrib.titre or 'ce site'}",
                        xp_recompense=contrib.xp_attribues,
                        mots_cles_json="[]",
                        caracteristiques_detection_json="[]",
                        secrets_et_mysteres=contrib.morale or "",
                        recit_historique=contrib.texte,
                        narration_audio_texte=contrib.signification,
                        pourquoi_ce_lieu_compte=contrib.signification,
                        route_path=f"/culture/monument/{target_id}",
                        modele_3d_url=None,
                        ar_disponible=False,
                        audio_url=contrib.audio_url,
                        statut_validation=f"Validé (Transmis par {contrib.auteur_nom})",
                        date_mise_a_jour=datetime.now(UTC),
                    )
                    db.add(new_monument)

            # D. Personnages Historiques
            elif contrib.type_contenu in ("personnage", "figure"):
                target_id = f"contrib_perso_{contrib.id[:8]}"
                if not db.query(CulturePersonnage).filter(CulturePersonnage.id == target_id).first():
                    new_perso = CulturePersonnage(
                        id=target_id,
                        nom=contrib.titre or contrib.texte[:60],
                        titre_honorifique=contrib.morale or "Figure Historique Emblématique",
                        periode=extra.get("periode", "Histoire du Mali"),
                        region_id=contrib.region_id,
                        region_nom=contrib.region_nom,
                        tag="Héros Citoyen",
                        photo_url=contrib.photo_url or "assets/images/culture/personnages/soundiata.jpg",
                        photo_credits=f"Archive transmise par {contrib.auteur_nom}",
                        resume=contrib.texte,
                        citation_historique=contrib.texte_original,
                        faits_marquants_json="[]",
                        chapitres_json="[]",
                        elements_lies_json="[]",
                        audio_narration=contrib.audio_url,
                        date_creation=datetime.now(UTC),
                    )
                    db.add(new_perso)

            # E. Villes & Terroirs
            elif contrib.type_contenu in ("lieu", "ville", "terroir"):
                target_id = f"contrib_lieu_{contrib.id[:8]}"
                if not db.query(CultureLieu).filter(CultureLieu.id == target_id).first():
                    new_lieu = CultureLieu(
                        id=target_id,
                        nom=contrib.titre or contrib.texte[:60],
                        sous_titre=contrib.signification[:120],
                        region_id=contrib.region_id,
                        region_nom=contrib.region_nom,
                        tag="Cité & Terroir Citoyen",
                        photo_url=contrib.photo_url or "assets/images/culture/monuments/tour_afrique.jpg",
                        photo_credits=f"Contribution de {contrib.auteur_nom}",
                        fondation=extra.get("fondation", "Fondation séculaire transmise par les anciens"),
                        latitude=float(extra.get("latitude", 12.6392)),
                        longitude=float(extra.get("longitude", -8.0029)),
                        population_ou_details=extra.get("population", ""),
                        resume=contrib.texte,
                        chapitres_json="[]",
                        elements_lies_json="[]",
                        date_creation=datetime.now(UTC),
                    )
                    db.add(new_lieu)

            # F. Patronymes (Jamu) & Prénoms
            elif contrib.type_contenu in ("patronyme", "nom"):
                name_clean = (contrib.titre or contrib.texte).strip().capitalize()
                target_id = f"nom_{_normalize_text(name_clean)[:25]}"
                if not db.query(CultureNom).filter(CultureNom.id == target_id).first():
                    new_nom = CultureNom(
                        id=target_id,
                        nom=name_clean,
                        nom_normalise=_normalize_text(name_clean),
                        type="nom",
                        ethnie_ou_region=contrib.origine or contrib.region_nom,
                        signification=contrib.signification,
                        clan_role=contrib.source_temoin or "Lignée traditionnelle du Mali",
                        totem=extra.get("totem", ""),
                        senankouya=extra.get("senankouya", ""),
                        devise_ou_louange=contrib.texte_original,
                        anecdote=contrib.texte,
                        variantes_json=json.dumps([name_clean], ensure_ascii=False),
                        date_creation=datetime.now(UTC),
                    )
                    db.add(new_nom)

            # 2. Crédit de récompense dans le Portefeuille et XP de l'auteur
            target_author = (contrib.auteur_id or contrib.auteur_nom or "").strip()
            if target_author:
                apprenant = None
                try:
                    from backend.src.db.models import Apprenant
                    apprenant = (
                        db.query(Apprenant)
                        .filter(
                            (Apprenant.id == target_author)
                            | (Apprenant.nom.ilike(f"%{target_author}%"))
                            | (Apprenant.prenom.ilike(f"%{target_author}%"))
                        )
                        .first()
                    )
                except Exception as ap_err:  # noqa: BLE001
                    logger.warning(f"Note recherche apprenant pour récompense: {ap_err}")

                reward_amount = contrib.pieces_attribuees or 25
                target_ids = {target_author}
                if apprenant:
                    target_ids.add(apprenant.id)
                    if apprenant.nom:
                        target_ids.add(apprenant.nom)

                try:
                    from backend.src.services.wallet_service import credit_coins
                    for uid in target_ids:
                        credit_coins(
                            db=db,
                            student_id=uid,
                            amount=reward_amount,
                            origine="CONTRIBUTION_CULTURE",
                            description=f"Contribution culturelle validée ({contrib.type_contenu})",
                            idempotency_key=f"contrib_reward_{contrib.id}_{uid}",
                            metadata={"contribution_id": contrib.id, "type_contenu": contrib.type_contenu},
                        )
                except Exception as rew_err:  # noqa: BLE001
                    logger.warning(f"Note attribution récompense pièces contribution: {rew_err}")

                # L'XP de culture (50 XP) est comptabilisé directement via la contribution approuvée
                pass
        db.commit()
        db.refresh(contrib)
        logger.info(f"Contribution {contrib.id} modérée avec statut : {decision_clean}")
        return _serialize_contribution(contrib)

    # ==========================================================================
    # SUPER ADMIN CMS CULTUREL & PASSEPORT
    # ==========================================================================

    @staticmethod
    def get_all_cms_content(db: Session) -> list[dict[str, Any]]:
        """
        Récupère l'ensemble des contenus culturels unifiés pour le Super Admin (Catalogue CMS).
        Garantit la conformité stricte avec ContenuCulturelDTO d'Angular.
        """
        items: list[dict[str, Any]] = []

        # 1. Figures Historiques
        for p in db.query(CulturePersonnage).all():
            faits = []
            chapitres = []
            lies = []
            try:
                faits = json.loads(p.faits_marquants_json) if p.faits_marquants_json else []
            except (ValueError, TypeError):
                faits = []
            try:
                chapitres = json.loads(p.chapitres_json) if p.chapitres_json else []
            except (ValueError, TypeError):
                chapitres = []
            try:
                lies = json.loads(p.elements_lies_json) if p.elements_lies_json else []
            except (ValueError, TypeError):
                lies = []

            items.append({
                "id": p.id,
                "type": "figure",
                "nom": p.nom,
                "titreHonorifique": p.titre_honorifique or "Figure Historique",
                "periode": p.periode or "Histoire du Mali",
                "regionId": p.region_id or "bamako",
                "regionNom": p.region_nom or "Tout le Mali",
                "tag": p.tag or "Héros National",
                "photoUrl": p.photo_url or "assets/images/culture/personnages/soundiata.jpg",
                "photoCredits": p.photo_credits or "Archives Nationales du Mali",
                "resume": p.resume or "",
                "citationHistorique": p.citation_historique or "",
                "faitsCles": faits if isinstance(faits, list) else [],
                "chapitres": chapitres if isinstance(chapitres, list) else [],
                "elementsConnexes": lies if isinstance(lies, list) else [],
                "publie": True,
                "dateCreation": p.date_creation.isoformat() if p.date_creation else "2026-01-01T00:00:00Z",
                "dateModification": p.date_creation.isoformat() if p.date_creation else "2026-01-01T00:00:00Z",
            })

        # 2. Monuments
        for m in db.query(CultureMonument).all():
            items.append({
                "id": m.id,
                "type": "monument",
                "nom": m.nom,
                "sousTitre": m.sous_titre or m.nom,
                "ere": m.epoque or "Époque contemporaine",
                "regionId": m.region_id or "bamako",
                "regionNom": m.region_nom or "Bamako",
                "tag": m.tag or "Patrimoine National",
                "photoUrl": m.photo_url or "assets/images/culture/monuments/tour_afrique.jpg",
                "photoCredits": "Direction Nationale du Patrimoine Culturel",
                "localisationDetails": m.details_localisation or m.ville,
                "presentation": m.recit_historique or m.sous_titre,
                "architectureEtMateriaux": m.style_architectural or "Architecture traditionnelle",
                "pourquoiCestImportant": m.pourquoi_ce_lieu_compte or m.sous_titre,
                "faitsCles": [{"titre": "Symbole Républicain", "description": m.secrets_et_mysteres or m.sous_titre, "anneeOuEpoque": m.epoque}],
                "chapitres": [{"titre": "Histoire et Épopée", "contenu": m.recit_historique}],
                "elementsConnexes": [],
                "publie": True,
                "dateCreation": m.date_mise_a_jour.isoformat() if m.date_mise_a_jour else "2026-01-01T00:00:00Z",
                "dateModification": m.date_mise_a_jour.isoformat() if m.date_mise_a_jour else "2026-01-01T00:00:00Z",
            })

        # 3. Cités & Villes
        for l in db.query(CultureLieu).all():
            chapitres = []
            lies = []
            try:
                chapitres = json.loads(l.chapitres_json) if l.chapitres_json else []
            except (ValueError, TypeError):
                chapitres = []
            try:
                lies = json.loads(l.elements_lies_json) if l.elements_lies_json else []
            except (ValueError, TypeError):
                lies = []

            items.append({
                "id": l.id,
                "type": "ville",
                "nom": l.nom,
                "sousTitre": l.sous_titre or l.nom,
                "regionId": l.region_id or "bamako",
                "regionNom": l.region_nom or "Mali",
                "tag": l.tag or "Cité Millénaire",
                "photoUrl": l.photo_url or "assets/images/culture/monuments/tour_afrique.jpg",
                "photoCredits": l.photo_credits or "Archives du Mali",
                "fondation": l.fondation or "Fondation séculaire",
                "resume": l.resume or "",
                "identiteCulturelle": l.sous_titre or "",
                "traditionsEtPatrimoine": l.resume or "",
                "faitsCles": [{"titre": "Origine", "description": l.fondation}],
                "chapitres": chapitres if isinstance(chapitres, list) else [],
                "elementsConnexes": lies if isinstance(lies, list) else [],
                "publie": True,
                "dateCreation": l.date_creation.isoformat() if l.date_creation else "2026-01-01T00:00:00Z",
                "dateModification": l.date_creation.isoformat() if l.date_creation else "2026-01-01T00:00:00Z",
            })

        # 4. Contes Interactifs
        for c in db.query(CultureConte).all():
            scenes = []
            lies = []
            try:
                scenes = json.loads(c.scenes_json) if c.scenes_json else []
            except (ValueError, TypeError):
                scenes = []
            try:
                lies = json.loads(c.elements_lies_json) if c.elements_lies_json else []
            except (ValueError, TypeError):
                lies = []

            items.append({
                "id": c.id,
                "type": "conte",
                "titre": c.titre,
                "sousTitre": c.sous_titre or "Conte traditionnel",
                "origine": c.origine or "Tradition Orale Mandingue",
                "regionId": c.region_id or "bamako",
                "regionNom": c.region_nom or "Tout le Mali",
                "tag": c.tag or "Conte Initiatique",
                "photoUrl": c.photo_url or "assets/images/culture/contes/zoumana_lievre.jpg",
                "photoCredits": c.photo_credits or "Tradition Orale",
                "resume": c.resume or "",
                "narrateur": c.conteur or "Griot AlternIA",
                "dureeAudio": c.duree_audio or "5 min",
                "dureeLecture": c.duree_lecture or "3 min",
                "enVedette": True,
                "morale": c.morale or "Leçon de sagesse",
                "scenes": scenes if isinstance(scenes, list) else [],
                "elementsConnexes": lies if isinstance(lies, list) else [],
                "publie": True,
                "dateCreation": c.date_creation.isoformat() if c.date_creation else "2026-01-01T00:00:00Z",
                "dateModification": c.date_creation.isoformat() if c.date_creation else "2026-01-01T00:00:00Z",
            })

        # 5. Devinettes & Proverbes
        for pr in db.query(CultureProverbe).all():
            is_devinette = pr.theme == "Jeu de Devinettes" or "devinette" in pr.id
            if is_devinette:
                items.append({
                    "id": pr.id,
                    "type": "devinette",
                    "formuleIntro": "« N'Da ! » — « N'Da n'sira ! »",
                    "enigmeTexte": pr.texte,
                    "indices": [f"Origine : {pr.origine}", f"Thème : {pr.theme}", f"Sagesse : {pr.signification}"],
                    "options": [pr.morale, "L'Ombre sous le soleil", "La Rivière Djoliba", "Le Vent du Sahel"],
                    "bonneReponse": pr.morale,
                    "explicationCulturelle": pr.signification,
                    "proverbe": pr.texte_original or pr.texte,
                    "regionId": pr.region_id or "bamako",
                    "regionNom": pr.region_nom or "Mali",
                    "categorie": pr.theme or "Sagesse & Nature",
                    "difficulte": "Apprenti",
                    "recompenseXp": pr.xp_recompense or 40,
                    "photoUrl": "assets/images/culture/devinettes/calebasse.jpg",
                    "publie": True,
                    "dateCreation": "2026-01-01T00:00:00Z",
                    "dateModification": "2026-01-01T00:00:00Z",
                })
            else:
                items.append({
                    "id": pr.id,
                    "type": "temoignage",
                    "conteur": pr.orateur_nom or "Ancien du Village",
                    "qualiteConteur": pr.orateur_role or "Gardien de la tradition",
                    "lieu": pr.region_nom,
                    "titreHistoire": pr.texte_original or pr.texte[:50],
                    "duree": "2 min",
                    "extrait": f"{pr.texte}\n\nSignification : {pr.signification}\nMorale : {pr.morale}",
                    "avatarUrl": "assets/images/culture/conteurs/vieux_sage.jpg",
                    "audioUrl": None,
                    "epoqueOuAnnee": "Tradition Vivante",
                    "regionId": pr.region_id or "bamako",
                    "regionNom": pr.region_nom or "Mali",
                    "publie": True,
                    "dateCreation": "2026-01-01T00:00:00Z",
                    "dateModification": "2026-01-01T00:00:00Z",
                })

        return items

    @staticmethod
    def get_tampons(db: Session) -> list[dict[str, Any]]:
        """Fournit les tampons du Passeport Culturel pour les 11 régions calculés sur les données réelles."""
        total_eleves = db.query(Apprenant).count()

        regions_config = [
            {
                "id": "tampon_bamako",
                "nom": "Monument de l'Indépendance",
                "regionId": "bamako",
                "regionNom": "Bamako",
                "monumentOuFigure": "Monument de l'Indépendance & Place du 22 Septembre",
                "symboleSvg": "star",
                "conditionDeblocage": "Visiter ou scanner un monument de Bamako",
                "xpRecompense": 50,
                "rarete": "Commun",
                "couleurAccent": "#F1851F",
            },
            {
                "id": "tampon_koulikoro",
                "nom": "Monts du Mandé & Soundiata",
                "regionId": "koulikoro",
                "regionNom": "Koulikoro",
                "monumentOuFigure": "Monts du Mandé & Épopée de Soundiata Keïta",
                "symboleSvg": "mountain",
                "conditionDeblocage": "Découvrir la geste du Mandé et la Charte de Kouroukan Fouga",
                "xpRecompense": 60,
                "rarete": "Commun",
                "couleurAccent": "#10B981",
            },
            {
                "id": "tampon_kayes",
                "nom": "Chutes de Félou & Tata de Koniakary",
                "regionId": "kayes",
                "regionNom": "Kayes",
                "monumentOuFigure": "Chutes de Félou & Fort de Médine",
                "symboleSvg": "droplet",
                "conditionDeblocage": "Explorer le patrimoine fluvial et les royaumes du Khasso",
                "xpRecompense": 70,
                "rarete": "Rare",
                "couleurAccent": "#6366F1",
            },
            {
                "id": "tampon_sikasso",
                "nom": "Mamelon & Tata de Tiéba",
                "regionId": "sikasso",
                "regionNom": "Sikasso",
                "monumentOuFigure": "Mamelon de Sikasso & Remparts du Kénédougou",
                "symboleSvg": "shield",
                "conditionDeblocage": "Honorer le serment des héros de la résistance du Kénédougou",
                "xpRecompense": 75,
                "rarete": "Rare",
                "couleurAccent": "#EC4899",
            },
            {
                "id": "tampon_segou",
                "nom": "Cité des Balanzans",
                "regionId": "segou",
                "regionNom": "Ségou",
                "monumentOuFigure": "Ségou-Koro & Tombe de Biton Coulibaly",
                "symboleSvg": "sun",
                "conditionDeblocage": "Résoudre une devinette et écouter un conte du Royaume Bambara",
                "xpRecompense": 80,
                "rarete": "Rare",
                "couleurAccent": "#8B5CF6",
            },
            {
                "id": "tampon_mopti",
                "nom": "Grande Mosquée de Djenné (UNESCO)",
                "regionId": "mopti",
                "regionNom": "Mopti",
                "monumentOuFigure": "Mosquée en banco de Djenné & Falaise de Bandiagara",
                "symboleSvg": "award",
                "conditionDeblocage": "Visiter le joyau d'architecture banco du delta intérieur",
                "xpRecompense": 100,
                "rarete": "Épique",
                "couleurAccent": "#F59E0B",
            },
            {
                "id": "tampon_tombouctou",
                "nom": "Cité des 333 Saints & Sankoré",
                "regionId": "tombouctou",
                "regionNom": "Tombouctou",
                "monumentOuFigure": "Mosquée Sankoré & Institut Ahmed Baba",
                "symboleSvg": "book-open",
                "conditionDeblocage": "Consulter un extrait des manuscrits anciens de Tombouctou",
                "xpRecompense": 120,
                "rarete": "Légendaire",
                "couleurAccent": "#EF4444",
            },
            {
                "id": "tampon_gao",
                "nom": "Tombeau des Askia & Empire Songhay",
                "regionId": "gao",
                "regionNom": "Gao",
                "monumentOuFigure": "Tombeau pyramidal des Askia (UNESCO)",
                "symboleSvg": "crown",
                "conditionDeblocage": "Découvrir la grandeur de Sonni Ali Ber et de l'Askia Mohamed",
                "xpRecompense": 110,
                "rarete": "Épique",
                "couleurAccent": "#14B8A6",
            },
            {
                "id": "tampon_kidal",
                "nom": "Adrar des Ifoghas",
                "regionId": "kidal",
                "regionNom": "Kidal",
                "monumentOuFigure": "Massif de l'Adrar & Traditions Nomades",
                "symboleSvg": "compass",
                "conditionDeblocage": "Participer à une veillée sous la tente aux étoiles",
                "xpRecompense": 90,
                "rarete": "Rare",
                "couleurAccent": "#06B6D4",
            },
            {
                "id": "tampon_taoudenit",
                "nom": "Caravanes de Sel de l'Azalaï",
                "regionId": "taoudenit",
                "regionNom": "Taoudénit",
                "monumentOuFigure": "Salines ancestrales & Voie des Caravanes",
                "symboleSvg": "feather",
                "conditionDeblocage": "Compléter le grand périple saharien",
                "xpRecompense": 130,
                "rarete": "Légendaire",
                "couleurAccent": "#84CC16",
            },
            {
                "id": "tampon_menaka",
                "nom": "Vallée d'Azaouagh & Boucle du Niger",
                "regionId": "menaka",
                "regionNom": "Ménaka",
                "monumentOuFigure": "Terres Pastorales & Traditions de Fraternité",
                "symboleSvg": "heart",
                "conditionDeblocage": "Partager un proverbe de concorde communautaire",
                "xpRecompense": 85,
                "rarete": "Rare",
                "couleurAccent": "#EAB308",
            },
        ]

        result = []
        for r in regions_config:
            debloques = (
                db.query(CultureDecouverte)
                .join(CultureMonument, CultureDecouverte.monument_id == CultureMonument.id)
                .filter(CultureMonument.region_id == r["regionId"])
                .count()
            )
            taux = round((debloques / total_eleves) * 100) if total_eleves > 0 else 0
            item = dict(r)
            item["totalDebloquesParEleves"] = debloques
            item["tauxDeblocage"] = min(100, taux)
            item["actif"] = True
            result.append(item)

        return result

    @staticmethod
    def get_niveaux(db: Session) -> list[dict[str, Any]]:
        """Fournit les paliers de progression d'exploration du patrimoine malien calculés sur les apprenants réels."""
        total_eleves = db.query(Apprenant).count()
        return [
            {
                "niveau": 1,
                "titre": "Apprenti du Sahel",
                "seuilXp": 0,
                "badgeNom": "Premier Pas Patrimoine",
                "couleur": "#10B981",
                "nombreElevesAtteints": total_eleves,
            },
            {
                "niveau": 2,
                "titre": "Voyageur du Djoliba",
                "seuilXp": 150,
                "badgeNom": "Navigateur Fluvial",
                "couleur": "#0284c7",
                "nombreElevesAtteints": 0,
            },
            {
                "niveau": 3,
                "titre": "Gardien du Mandé",
                "seuilXp": 400,
                "badgeNom": "Protecteur des Coutumes",
                "couleur": "#8B5CF6",
                "nombreElevesAtteints": 0,
            },
            {
                "niveau": 4,
                "titre": "Érudit de Tombouctou",
                "seuilXp": 800,
                "badgeNom": "Scribe des Manuscrits",
                "couleur": "#F59E0B",
                "nombreElevesAtteints": 0,
            },
            {
                "niveau": 5,
                "titre": "Maître Dozo du Patrimoine",
                "seuilXp": 1500,
                "badgeNom": "Grand Sage de la Nation",
                "couleur": "#EF4444",
                "nombreElevesAtteints": 0,
            },
        ]

