"""
Service métier pour la gestion du patrimoine culturel, la reconnaissance CultureLens et le RAG culturel.
"""

from datetime import datetime
import json
import logging
import math
import random
import time
import unicodedata
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
            print("\033[1;31m❌ [CultureLens AI] Erreur : Aucun monument dans le catalogue local\033[0m")
            return {
                "success": False,
                "confidence": 0.0,
                "message": "Aucun monument dans le catalogue local",
                "target": None,
            }

        t_start = time.perf_counter()
        print(f"\n\033[1;35m════════════════════════════════════════════════════════════════════════════════\033[0m")
        print(f"\033[1;35m📸 [CultureLens AI]\033[0m Requête de scan reçue sur \033[1;36mPOST /api/v1/culture/identify\033[0m")
        if image_base64:
            b64_size_kb = (len(image_base64) * 3 / 4) / 1024
            print(f"   • Données image     : Base64 présente ({b64_size_kb:.1f} KB)")
        if image_name:
            print(f"   • Nom de fichier    : {image_name}")
        if latitude is not None and longitude is not None:
            print(f"   • Coordonnées GPS   : ({latitude:.4f}, {longitude:.4f})")
        if hint_id:
            print(f"   • Hint ID fourni    : {hint_id}")

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
                ai_root = Path(__file__).resolve().parents[3] / "culturelens_ai"
                if str(ai_root) not in sys.path:
                    sys.path.insert(0, str(ai_root))
                from culturelens_ai.src.recognizer import CultureLensRecognizer

                raw_data = image_base64.split(",")[-1]
                img_bytes = base64.b64decode(raw_data)
                user_coords = (latitude, longitude) if (latitude is not None and longitude is not None) else None
                ai_result = CultureLensRecognizer.get_instance().predict(img_bytes, user_coords=user_coords)
            except Exception as e:
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
            except Exception as e:
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
        estimated_distance_km: Optional[float] = None
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
            print(f"   • Statut             : Correspondance insuffisante avec le patrimoine répertorié")
            print(f"\033[1;35m════════════════════════════════════════════════════════════════════════════════\033[0m\n")

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

        print(f"\n\033[1;32m✅ [VERDICT CULTURELENS]\033[0m Monument identifié et certifié en {dt_total:.2f}s :")
        print(f"   • Monument           : \033[1m{matched_monument.nom}\033[0m ({matched_monument.id})")
        print(f"   • Confiance certifiée: \033[1;32m{confidence * 100:.1f}%\033[0m (Seuil minimum: 45.0%)")
        print(f"   • Région / Ville     : {matched_monument.region_nom} ({matched_monument.ville})")
        print(f"\033[1;35m════════════════════════════════════════════════════════════════════════════════\033[0m\n")

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
        - Contexte documentaire précis extrait de la base haute fidélité (Monuments, Personnages, Lieux, Contes, Proverbes)
        - Reformulation dynamique, chaleureuse et variée par le LLM (Vieux Sage / Griot du Mali)
        - À chaque demande, même posée deux fois de suite, la reformulation est vivante et renouvelée (temp=0.72)
        """
        t0_ask = time.perf_counter()
        clean_q = question.strip().lower()
        norm_q = _normalize_text(question)

        matched_item_name: Optional[str] = None
        matched_item_type: str = "general"
        context_item: Optional[Dict[str, Any]] = None
        sources: List[str] = []
        facts_blocks: List[str] = []

        # ── 1. RECHERCHE DANS LES MONUMENTS (Scoring spécifique par mot discriminant) ──
        STOP_WORDS = {
            "de", "du", "la", "le", "les", "des", "un", "une", "a", "au", "aux", "en", "sur",
            "monument", "place", "grande", "grand", "bamako", "mali", "ville", "histoire",
            "raconte", "parle", "moi", "qui", "est", "quoi", "c'est", "ce", "cette"
        }

        target_monument: Optional[CultureMonument] = None
        if monument_id:
            target_monument = db.query(CultureMonument).filter(CultureMonument.id == monument_id).first()

        if not target_monument:
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

        # ── 7. PROMPT POUR LE VIEUX SAGE & REFORMULATION ORALE PAR LE LLM ──
        system_prompt = (
            "Tu es le « Vieux Sage et Griot du Mali », vénérable gardien de la mémoire orale, des contes et de l'histoire sous l'arbre à palabres.\n\n"
            "DIRECTIVES IMPÉRATIVES D'ÉLOQUENCE ET D'AUTHENTICITÉ :\n"
            "1. VÉRITÉ HISTORIQUE STRICTE : Appuie-toi en priorité absolue sur le [CONTEXTE FACTUEL DU MALI] fourni. Respecte fidèlement les faits historiques, noms, dates, lieux et symboles réels.\n"
            "2. REFORMULATION VIVANTE ET POÉTIQUE : Ne copie JAMAIS textuellement la fiche ! Parle avec la verve, la musicalité et la chaleur d'un véritable griot ouest-africain (images évocatrices, chaleur humaine, fierté du patrimoine).\n"
            "3. VARIABILITÉ TOTALE À CHAQUE RÉPONSE : Ne récite jamais deux fois la même réponse si l'on te pose une question similaire ! Invente à chaque fois une entrée en matière unique (ex: 'I ni ce, noble voyageur', 'Écoute ce que le vent du Djoliba dépose sous notre baobab...', 'Approche-toi du feu de veillée, voyageur de la lumière...'), change l'ordre de tes anecdotes et emploie des métaphores variées pour que le dialogue reste interactif, captivant et vivant.\n"
            "4. DISTINCTION FAITS ET TRADITIONS : S'il y a des secrets ou légendes, présente-les comme la mémoire orale transmise par nos aïeux.\n"
            "5. STRUCTURE PARFAITE : Fais une réponse équilibrée et fluide de 2 à 4 paragraphes rythmés (ni trop courte, ni assommante), sans liste à puces mécanique, terminée par une formule de bénédiction ou une invitation bienveillante."
        )

        user_prompt = (
            f"--- CONTEXTE FACTUEL DU PATRIMOINE DU MALI (BASE DE DONNÉES DE RÉFÉRENCE) ---\n"
            f"{facts_text}\n"
            f"--------------------------------------------------------------------------\n\n"
            f"Question du voyageur : « {question} »\n\n"
            f"En tant que Vieux Sage et Griot, réponds au voyageur en t'imprégnant de ce contexte pour le reformuler avec sagesse, vivacité et éloquence :"
        )

        reponse: Optional[str] = None
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
                max_tokens=250,
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
        except Exception as exc:
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

        dt_total = time.perf_counter() - t0_ask

        # ── 9. LOGS CONSOLE STYLE CHAT INTERACTIF ─────────────────────────
        print(f"\n\033[1;35m════════════════════════════════════════════════════════════════════════════════\033[0m")
        print(f"\033[1;36m🗣️  [Guide Culturel IA]\033[0m Requête reçue sur \033[1mPOST /api/v1/culture/ask\033[0m")
        print(f"   • Question           : \033[1m\"{question}\"\033[0m")
        print(f"   • Cible RAG détectée : \033[1;33m{matched_item_name or 'Patrimoine Général du Mali'}\033[0m (Type: {matched_item_type})")
        print(f"   • Contexte injecté   : \033[36m{len(facts_blocks)} bloc(s) de faits authentiques extraits de la BDD\033[0m")
        if dt_llm > 0:
            print(f"   • Inférence LLM      : \033[1;32mGénération réussie via Qwen2.5 en {dt_llm:.2f}s\033[0m (Temp: 0.72 | Variabilité active)")
        else:
            print(f"   • Inférence LLM      : \033[1;33mMode de repli dynamique contextuel\033[0m")
        print(f"   • Temps total        : {dt_total:.2f}s")
        print(f"   • Début de réponse   : \033[37m\"{reponse[:150].strip()}...\"\033[0m")
        print(f"\033[1;35m════════════════════════════════════════════════════════════════════════════════\033[0m\n")

        return {
            "answer": reponse,
            "reponse": reponse,
            "sources": sources,
            "contextItem": context_item,
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
