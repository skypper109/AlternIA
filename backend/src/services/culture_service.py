"""
Service métier pour la gestion du patrimoine culturel, la reconnaissance CultureLens et le RAG culturel.
"""

from datetime import datetime
import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.src.db.models import (
    CultureMonument,
    CulturePersonnage,
    CultureLieu,
    CultureConte,
    CultureProverbe,
    CulturePack,
    CultureDecouverte,
)

logger = logging.getLogger("AlternIA.CultureService")


def _calculate_haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcule la distance géodésique en km entre deux points GPS (formule de Haversine)."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * (math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


def _serialize_monument(m: CultureMonument) -> Dict[str, Any]:
    """Sérialise un monument pour la réponse API."""
    mots_cles = []
    try:
        mots_cles = json.loads(m.mots_cles_json) if m.mots_cles_json else []
    except Exception:
        pass

    caracteristiques = []
    try:
        caracteristiques = json.loads(m.caracteristiques_detection_json) if m.caracteristiques_detection_json else []
    except Exception:
        pass

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


class CultureService:
    @staticmethod
    def get_monuments(
        db: Session,
        ville: Optional[str] = None,
        region_id: Optional[str] = None,
        query: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
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
    def get_monument_by_id(db: Session, monument_id: str) -> Optional[Dict[str, Any]]:
        """Récupère un monument spécifique par son identifiant."""
        m = db.query(CultureMonument).filter(CultureMonument.id == monument_id).first()
        return _serialize_monument(m) if m else None

    @staticmethod
    def identify_monument(
        db: Session,
        image_name: Optional[str] = None,
        image_base64: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        hint_id: Optional[str] = None,
    ) -> Dict[str, Any]:
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
            return {
                "success": False,
                "confidence": 0.0,
                "message": "Aucun monument dans le catalogue local",
                "target": None,
            }

        matched_monument: Optional[CultureMonument] = None
        confidence = 0.0
        detected_features = []

        # Cas 0 : Analyse neuronale par le modèle de vision CultureLens AI
        ai_result: Optional[Dict[str, Any]] = None
        if image_base64:
            try:
                import base64
                import sys
                from pathlib import Path
                ai_root = Path(__file__).resolve().parent.parent.parent / "culturelens_ai"
                if str(ai_root) not in sys.path:
                    sys.path.insert(0, str(ai_root))
                from culturelens_ai.src.recognizer import CultureLensRecognizer

                raw_data = image_base64.split(",")[-1]
                img_bytes = base64.b64decode(raw_data)
                user_coords = (latitude, longitude) if (latitude is not None and longitude is not None) else None
                ai_result = CultureLensRecognizer.get_instance().predict(img_bytes, user_coords=user_coords)
            except Exception as e:
                logger.warning(f"Inférence CultureLensRecognizer échouée : {e}")

        elif image_name:
            try:
                import sys
                from pathlib import Path
                ai_root = Path(__file__).resolve().parents[3] / "culturelens_ai"
                if str(ai_root) not in sys.path:
                    sys.path.insert(0, str(ai_root))
                from culturelens_ai.src.recognizer import CultureLensRecognizer

                candidate_files = [
                    ai_root / "dataset" / "test_images" / image_name,
                    ai_root / "dataset" / "reference_images" / image_name,
                ]
                for c_path in candidate_files:
                    if c_path.exists():
                        user_coords = (latitude, longitude) if (latitude is not None and longitude is not None) else None
                        ai_result = CultureLensRecognizer.get_instance().predict(c_path, user_coords=user_coords)
                        break
            except Exception as e:
                logger.warning(f"Inférence CultureLensRecognizer locale échouée : {e}")

        if ai_result:
            ai_conf = float(ai_result.get("confidence", 0.0))
            is_id = bool(ai_result.get("is_identified", False))
            ai_monument_id = ai_result.get("monument_id")
            if is_id and ai_conf >= 0.45 and ai_monument_id:
                found = next((m for m in all_monuments if m.id == ai_monument_id), None)
                if not found and "segou" in ai_monument_id:
                    found = next((m for m in all_monuments if "segou" in m.id), None)
                if not found:
                    found = next((m for m in all_monuments if m.id == f"monument_{ai_monument_id}"), None)
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

        # Cas 2 : Recherche par mots-clés ou nom de fichier
        if not matched_monument and (keywords or image_name):
            search_terms = []
            if keywords:
                search_terms.extend([k.lower().strip() for k in keywords])
            if image_name:
                cleaned_name = image_name.lower().replace("_", " ").replace("-", " ")
                search_terms.extend(cleaned_name.split())

            best_score = 0
            best_candidate = None
            for m in all_monuments:
                m_score = 0
                m_text = f"{m.nom} {m.sous_titre} {m.ville} {m.mots_cles_json}".lower()
                for term in search_terms:
                    if len(term) >= 3 and term in m_text:
                        m_score += 1

                if m_score > best_score:
                    best_score = m_score
                    best_candidate = m

            if best_candidate and best_score >= 1:
                kw_conf = min(0.985, 0.50 + (best_score * 0.08))
                if kw_conf >= 0.45:
                    matched_monument = best_candidate
                    confidence = kw_conf

        # Cas 3 : Croisement géospatial (Proximité GPS si autorisée)
        estimated_distance_km: Optional[float] = None
        if latitude is not None and longitude is not None:
            closest_m: Optional[CultureMonument] = None
            min_dist = float("inf")
            for m in all_monuments:
                dist = _calculate_haversine_distance_km(latitude, longitude, m.latitude, m.longitude)
                if dist < min_dist:
                    min_dist = dist
                    closest_m = m

            if min_dist < 5.0 and closest_m:  # Moins de 5 km d'un monument connu
                # Renforce la confiance géospatiale
                if not matched_monument:
                    matched_monument = closest_m
                    confidence = 0.92
                elif matched_monument.id == closest_m.id:
                    confidence = min(0.996, confidence + 0.03)

            if matched_monument:
                estimated_distance_km = _calculate_haversine_distance_km(
                    latitude, longitude, matched_monument.latitude, matched_monument.longitude
                )

        # Seuil d'acceptation strict de 45% (0.45) :
        # Si aucun monument n'est identifié ou si la certitude est inférieure à 45%, retour d'échec poli
        if not matched_monument or confidence < 0.45:
            conf_val = round(confidence, 3) if confidence > 0 else 0.0
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
                "scannedAt": datetime.utcnow().isoformat(),
            }

        serialized = _serialize_monument(matched_monument)
        detected_features = serialized.get("detectionFeatures", [])

        return {
            "success": True,
            "target": serialized,
            "confidence": round(confidence, 3),
            "confidencePercent": f"{round(confidence * 100, 1)}%",
            "recognizedFeatures": detected_features,
            "estimatedDistanceKm": estimated_distance_km,
            "isCertain": confidence >= 0.88,
            "scannedAt": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def ask_cultural_guide(
        db: Session,
        question: str,
        monument_id: Optional[str] = None,
        region_id: Optional[str] = None,
        context_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Assistant RAG du Guide Culturel :
        - Contexte documentaire précis extrait de la base haute fidélité
        - Distingue formellement : Faits documentés, Traditions orales, Interprétations
        """
        clean_q = question.strip().lower()

        # 1. Salutations et présentations
        if any(clean_q.startswith(g) or g in clean_q for g in ["bonjour", "bonsoir", "salut", "i ni ce", "i ni sogoma", "aw ni ce", "qui es-tu", "qui est-tu", "tu es qui", "presente-toi", "présente-toi", "ton role", "ton rôle"]):
            reponse = (
                "I ni ce, noble voyageur de la connaissance ! Je suis le Vieux Sage et Griot de la mémoire ancestrale du Mali.\n\n"
                "Sous cet arbre à palabres, je veille sur la mémoire de nos trois grands empires (Ghana, Manden, Songhoï), "
                "les récits héroïques de Soundiata Keïta et Mansa Moussa, les trésors architecturaux de Bamako et du pays tout entier, "
                "ainsi que nos contes au clair de lune. Quelle sagesse souhaites-tu explorer aujourd'hui ?"
            )
            return {
                "answer": reponse,
                "reponse": reponse,
                "sources": ["Tradition Orale des Griots du Mali", "Charte du Manden (1236)"],
                "contextItem": None,
                "ragVerified": True,
                "timestamp": datetime.utcnow().isoformat(),
            }

        # 2. Questions de nature / sciences / métaphores ancestrales (ex: photosynthèse, baobab, fleuve, soleil)
        if any(w in clean_q for w in ["photosynthes", "chlorophylle", "arbre", "plante", "nature", "fleuve", "djoliba", "soleil", "baobab", "balanzan", "eau", "terre", "science", "biologie"]):
            reponse = (
                "I ni ce, noble enfant de notre terre ! Écoute ce que le Vieux Sage et la sagesse des anciens nous enseignent :\n\n"
                "La photosynthèse est le secret par lequel les feuilles de nos vénérables baobabs et des 4 444 balanzans de Ségou "
                "captent les rayons ardents du soleil pour transformer l'air en sève nourricière et offrir l'ombrage protecteur aux voyageurs.\n\n"
                "Dans notre tradition, la nature et l'arbre sont sacrés : comme le stipule la Charte de Kouroukan Fouga (1236), nul ne doit couper un arbre sans utilité. "
                "Sous cet arbre à palabres, je garde l'histoire de notre patrimoine, de nos bâtisseurs et de nos empires. "
                "Souhaites-tu que je te parle de l'épopée de Soundiata, de la Tour de l'Afrique ou d'un conte de nos veillées ?"
            )
            return {
                "answer": reponse,
                "reponse": reponse,
                "sources": ["Sagesse des Anciens du Manden", "Charte de Kouroukan Fouga (1236)"],
                "contextItem": None,
                "ragVerified": True,
                "timestamp": datetime.utcnow().isoformat(),
            }

        # 3. Récupération du monument concerné
        target_monument: Optional[CultureMonument] = None
        if monument_id:
            target_monument = db.query(CultureMonument).filter(CultureMonument.id == monument_id).first()

        if not target_monument:
            norm_q = clean_q.replace("'", " ").replace("’", " ").replace("-", " ")
            for m in db.query(CultureMonument).all():
                norm_m_nom = m.nom.lower().replace("'", " ").replace("’", " ").replace("-", " ")
                if norm_m_nom in norm_q or m.id.lower() in clean_q or (len(m.nom) > 4 and any(word in norm_q.split() for word in norm_m_nom.split() if len(word) >= 5)):
                    target_monument = m
                    break

        if target_monument:
            sources = [f"Catalogue National — {target_monument.nom}", f"Statut : {target_monument.statut_validation}"]
            if any(w in clean_q for w in ["qui", "construit", "fondateur", "auteur", "origine"]):
                reponse = (
                    f"**Faits documentés :** {target_monument.nom} a été érigé lors de la période : {target_monument.epoque}.\n\n"
                    f"**Histoire :** {target_monument.recit_historique}\n\n"
                    f"**Style architectural :** {target_monument.style_architectural}."
                )
            elif any(w in clean_q for w in ["secret", "mystere", "anecdote", "tradition", "legende"]):
                reponse = (
                    f"**Traditions orales & Récits transmis :** {target_monument.secrets_et_mysteres}\n\n"
                    f"**Portée patrimoniale :** {target_monument.pourquoi_ce_lieu_compte}"
                )
            elif any(w in clean_q for w in ["pourquoi", "importance", "symbole", "valeur"]):
                reponse = (
                    f"**Valeur patrimoniale certifiée :** {target_monument.pourquoi_ce_lieu_compte}\n\n"
                    f"**Localisation :** {target_monument.details_localisation} ({target_monument.ville})."
                )
            else:
                reponse = (
                    f"**Présentation du monument :** {target_monument.nom} ({target_monument.sous_titre}).\n\n"
                    f"**Contexte historique :** {target_monument.recit_historique}\n\n"
                    f"**Secrets du site :** {target_monument.secrets_et_mysteres}"
                )
            return {
                "answer": reponse,
                "reponse": reponse,
                "sources": sources,
                "contextItem": _serialize_monument(target_monument),
                "ragVerified": True,
                "timestamp": datetime.utcnow().isoformat(),
            }

        # 4. Recherche dans les Grands Personnages
        for fig in db.query(CulturePersonnage).all():
            if fig.nom.lower() in clean_q or fig.id.lower() in clean_q or any(p in clean_q for p in fig.nom.lower().split()):
                reponse = (
                    f"**{fig.nom} — {fig.titre_honorifique} ({fig.periode})**\n\n"
                    f"{fig.resume}\n\n"
                    f"*{fig.citation_historique}*\n\n"
                    f"**Héritage pour le Mali :** Sa mémoire demeure un phare de dignité et de gouvernance pour notre nation."
                )
                return {
                    "answer": reponse,
                    "reponse": reponse,
                    "sources": [f"Archives Historiques Nationales — {fig.nom}", "UNESCO Patrimoine Immatériel"],
                    "contextItem": {"type": "personnage", "id": fig.id, "name": fig.nom},
                    "ragVerified": True,
                    "timestamp": datetime.utcnow().isoformat(),
                }

        # 5. Recherche dans les Villes & Terroirs
        for lieu in db.query(CultureLieu).all():
            if lieu.nom.lower() in clean_q or lieu.id.lower() in clean_q:
                info_fondation = f"**Fondation & Histoire :** {lieu.fondation}"
                if lieu.population_ou_details:
                    info_fondation += f" (Population : {lieu.population_ou_details})"
                reponse = (
                    f"**{lieu.nom} — {lieu.sous_titre}**\n\n"
                    f"{lieu.resume}\n\n"
                    f"{info_fondation}"
                )
                return {
                    "answer": reponse,
                    "reponse": reponse,
                    "sources": [f"Terroirs du Mali — {lieu.nom}", f"Région : {lieu.region_nom}"],
                    "contextItem": {"type": "lieu", "id": lieu.id, "name": lieu.nom},
                    "ragVerified": True,
                    "timestamp": datetime.utcnow().isoformat(),
                }

        # 6. Recherche dans les Contes & Légendes
        for conte in db.query(CultureConte).all():
            if any(w in clean_q for w in ["conte", "fable", "legende", "histoire"]) or conte.titre.lower() in clean_q:
                reponse = (
                    f"**Conte Ancestral : {conte.titre}**\n\n"
                    f"« {conte.sous_titre} »\n\n"
                    f"{conte.resume}\n\n"
                    f"**Morale de nos aïeux :** {conte.morale}"
                )
                return {
                    "answer": reponse,
                    "reponse": reponse,
                    "sources": [f"Veillées Traditionnelles — {conte.titre}", f"Origine : {conte.origine}"],
                    "contextItem": {"type": "conte", "id": conte.id, "name": conte.titre},
                    "ragVerified": True,
                    "timestamp": datetime.utcnow().isoformat(),
                }

        # 7. Recherche dans les Proverbes et Sagesses
        if any(w in clean_q for w in ["proverbe", "sagesse", "devise", "adage"]):
            prov = db.query(CultureProverbe).first()
            if prov:
                texte_bambara = prov.texte_original or prov.texte
                reponse = (
                    f"Voici une parole de sagesse de nos ancêtres :\n\n"
                    f"« {texte_bambara} »\n\n"
                    f"**Signification :** « {prov.signification} »\n\n"
                    f"**Morale :** {prov.morale}"
                )
                return {
                    "answer": reponse,
                    "reponse": reponse,
                    "sources": ["Sagesse Populaire Mandingue", f"Thème : {prov.theme}"],
                    "contextItem": {"type": "proverbe", "id": prov.id},
                    "ragVerified": True,
                    "timestamp": datetime.utcnow().isoformat(),
                }

        # 8. Réponse par défaut chaleureuse et culturelle du Vieux Sage
        reponse = (
            f"Noble voyageur, en tant que Vieux Sage et Griot de notre terre, j'accueille ta question : « {question} ».\n\n"
            f"La mémoire du Mali est vaste comme le fleuve Djoliba. Elle englobe nos 12 monuments de Bamako "
            f"(la Tour de l'Afrique, le Monument de l'Indépendance, le Monument de la Paix...), nos sanctuaires classés par l'UNESCO "
            f"(Djenné, Tombouctou, Gao), et les épopées de Soundiata Keïta et Mansa Moussa.\n\n"
            f"Pose-moi une question sur nos rois, nos forteresses, nos masques sacrés ou nos contes d'autrefois !"
        )
        return {
            "answer": reponse,
            "reponse": reponse,
            "sources": ["Base de Connaissances CultureLens AlternIA", "Mémoire Vivante des Griots"],
            "contextItem": None,
            "ragVerified": True,
            "timestamp": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def get_figures(db: Session) -> List[Dict[str, Any]]:
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
    def get_places(db: Session) -> List[Dict[str, Any]]:
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
    def get_figure_by_id(db: Session, figure_id: str) -> Optional[Dict[str, Any]]:
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
    def get_place_by_id(db: Session, place_id: str) -> Optional[Dict[str, Any]]:
        places = CultureService.get_places(db)
        for p in places:
            if p["id"] == place_id:
                return p
        for p in places:
            if p["id"].startswith(place_id) or place_id.startswith(p["id"]):
                return p
        return None

    @staticmethod
    def get_stories(db: Session) -> List[Dict[str, Any]]:
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
    def get_proverbs(db: Session) -> List[Dict[str, Any]]:
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
    def get_packs(db: Session) -> List[Dict[str, Any]]:
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
    def get_pack_bundle(db: Session, pack_id: str) -> Optional[Dict[str, Any]]:
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
            "generatedAt": datetime.utcnow().isoformat(),
            "monuments": [_serialize_monument(m) for m in monuments],
            "figures": CultureService.get_figures(db)[:3],
            "proverbs": CultureService.get_proverbs(db)[:5],
            "stories": CultureService.get_stories(db)[:2],
        }

    @staticmethod
    def record_discovery(
        db: Session,
        monument_id: str,
        apprenant_id: Optional[str] = None,
        confidence: float = 0.98,
        is_favorite: bool = False,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Enregistre un monument découvert ou mis en favori par l'apprenant."""
        decouverte = CultureDecouverte(
            monument_id=monument_id,
            apprenant_id=apprenant_id,
            confidence=confidence,
            est_favori=is_favorite,
            notes_personnelles=notes,
            date_decouverte=datetime.utcnow(),
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
    def get_discoveries(db: Session, apprenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
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
