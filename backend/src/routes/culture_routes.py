"""
Routes FastAPI pour le module CultureLens & Patrimoine du Mali.
Fournit les endpoints de consultation, d'identification visuelle/géospatiale,
de dialogue RAG culturel et de synchronisation des packs hors ligne.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.src.db.database import get_db
from backend.src.services.culture_service import CultureService

router = APIRouter(prefix="/api/v1/culture", tags=["CultureLens & Patrimoine"])


# ==============================================================================
# SCHÉMAS DE REQUÊTES ET RÉPONSES
# ==============================================================================

class IdentifyRequest(BaseModel):
    image_name: Optional[str] = Field(None, description="Nom du fichier image ou identifiant de capture")
    image_base64: Optional[str] = Field(None, description="Image encodée en base64 pour inférence IA vision directe")
    keywords: Optional[List[str]] = Field(None, description="Mots-clés extraits ou annotations")
    latitude: Optional[float] = Field(None, description="Position GPS de l'appareil (latitude)")
    longitude: Optional[float] = Field(None, description="Position GPS de l'appareil (longitude)")
    hint_id: Optional[str] = Field(None, description="ID cible suggéré (mode démo ou balise)")


class AskGuideRequest(BaseModel):
    question: str = Field(..., description="Question posée au guide culturel")
    monument_id: Optional[str] = Field(None, description="ID du monument en cours de consultation")
    region_id: Optional[str] = Field(None, description="ID de la région contextuelle")


class DiscoveryRecordRequest(BaseModel):
    monument_id: str = Field(..., description="ID du monument scanné")
    apprenant_id: Optional[str] = Field(None, description="ID de l'apprenant")
    confidence: float = Field(0.98, description="Indice de confiance de la détection")
    is_favorite: bool = Field(False, description="Marqué en favori")
    notes: Optional[str] = Field(None, description="Notes personnelles de l'apprenant")


# ==============================================================================
# ENDPOINTS MONUMENTS ET SITES (PRIORITÉ BAMAKO)
# ==============================================================================

@router.get("/health")
def culture_health(db: Session = Depends(get_db)):
    """Vérification de l'état du sous-système CultureLens."""
    from backend.src.db.models import CultureMonument
    count = db.query(CultureMonument).count()
    bamako_count = db.query(CultureMonument).filter(CultureMonument.ville == "Bamako").count()
    return {
        "status": "online",
        "service": "CultureLens Edge & Cloud Service",
        "totalMonuments": count,
        "bamakoMonuments": bamako_count,
        "offlineReady": True,
    }


@router.get("/monuments")
def get_monuments(
    ville: Optional[str] = Query(None, description="Filtrer par ville (ex: 'Bamako', 'Djenné')"),
    region_id: Optional[str] = Query(None, description="Filtrer par région (ex: 'bamako', 'mopti')"),
    q: Optional[str] = Query(None, description="Recherche textuelle libre"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Récupère le catalogue des monuments et sites culturels."""
    return CultureService.get_monuments(
        db=db,
        ville=ville,
        region_id=region_id,
        query=q,
        skip=skip,
        limit=limit,
    )


@router.get("/sites")
def get_sites(
    ville: Optional[str] = None,
    region_id: Optional[str] = None,
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Alias pour /monuments conforme à la nomenclature internationale."""
    return get_monuments(ville=ville, region_id=region_id, q=q, skip=skip, limit=limit, db=db)


@router.get("/monuments/{monument_id}")
def get_monument_detail(monument_id: str, db: Session = Depends(get_db)):
    """Récupère la fiche détaillée et certifiée d'un monument."""
    m = CultureService.get_monument_by_id(db, monument_id)
    if not m:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Monument '{monument_id}' introuvable dans le catalogue",
        )
    return m


@router.get("/sites/{site_id}")
def get_site_detail(site_id: str, db: Session = Depends(get_db)):
    """Alias pour /monuments/{id}."""
    return get_monument_detail(monument_id=site_id, db=db)


@router.get("/sites/{site_id}/narration")
def get_site_narration(site_id: str, db: Session = Depends(get_db)):
    """Fournit le texte de narration audio haute fidélité pour le lecteur vocal."""
    m = CultureService.get_monument_by_id(db, site_id)
    if not m:
        raise HTTPException(status_code=404, detail="Site introuvable")

    return {
        "siteId": m["id"],
        "siteName": m["nom"],
        "narrationText": m["narration_audio_texte"],
        "audioUrl": m.get("audioUrl"),
        "languages": ["fr-FR", "bm-ML"],
        "durationEstimate": "1 min 30 s",
    }


# ==============================================================================
# SCANNER INTELLIGENT & IDENTIFICATION CULTURELENS
# ==============================================================================

@router.post("/identify")
def identify_monument(payload: IdentifyRequest, db: Session = Depends(get_db)):
    """
    Analyse d'identification visuelle et géospatiale du scanner CultureLens.
    Retourne la cible reconnue, le taux de certitude et les caractéristiques détectées.
    """
    result = CultureService.identify_monument(
        db=db,
        image_name=payload.image_name,
        image_base64=payload.image_base64,
        keywords=payload.keywords,
        latitude=payload.latitude,
        longitude=payload.longitude,
        hint_id=payload.hint_id,
    )
    return result


@router.get("/dataset-images/{monument_id}/{filename}")
def get_dataset_image(monument_id: str, filename: str):
    """Sert une photo réelle ou augmentée issue du dataset de référence CultureLens."""
    ai_root = Path(__file__).resolve().parents[3] / "culturelens_ai"
    target = ai_root / "dataset" / "reference_images" / monument_id / filename
    if target.exists() and target.is_file():
        return FileResponse(str(target))
    raise HTTPException(status_code=404, detail="Image de monument non trouvée")


# ==============================================================================
# GUIDE CULTUREL CONVERSATIONNEL (RAG)
# ==============================================================================

@router.post("/ask")
def ask_cultural_guide(payload: AskGuideRequest, db: Session = Depends(get_db)):
    """
    Interroge le Guide Culturel AlterniA (RAG vérifié).
    Distingue faits documentés, traditions orales et portée patrimoniale.
    """
    return CultureService.ask_cultural_guide(
        db=db,
        question=payload.question,
        monument_id=payload.monument_id,
        region_id=payload.region_id,
    )


# ==============================================================================
# PERSONNAGES, TERROIRS, CONTES ET PROVERBES
# ==============================================================================

@router.get("/figures")
def get_figures(db: Session = Depends(get_db)):
    """Liste des grands personnages historiques du Mali."""
    return CultureService.get_figures(db)


@router.get("/places")
def get_places(db: Session = Depends(get_db)):
    """Liste des terroirs et cités historiques du Mali."""
    return CultureService.get_places(db)


@router.get("/stories")
def get_stories(db: Session = Depends(get_db)):
    """Liste des contes et récits oraux interactifs."""
    return CultureService.get_stories(db)


@router.get("/proverbs")
def get_proverbs(db: Session = Depends(get_db)):
    """Liste des proverbes et sagesses des terroirs maliens."""
    return CultureService.get_proverbs(db)


# ==============================================================================
# PACKS HORS LIGNE ET SYNCHRONISATION
# ==============================================================================

@router.get("/packs")
def get_packs(db: Session = Depends(get_db)):
    """Liste des packs culturels téléchargeables pour utilisation hors ligne."""
    return CultureService.get_packs(db)


@router.get("/packs/{pack_id}/download")
def download_pack_bundle(pack_id: str, db: Session = Depends(get_db)):
    """Génère et télécharge le bundle de données complet d'un pack hors ligne."""
    bundle = CultureService.get_pack_bundle(db, pack_id)
    if not bundle:
        raise HTTPException(status_code=404, detail="Pack introuvable")
    return bundle


# ==============================================================================
# DÉCOUVERTES ET FAVORIS
# ==============================================================================

@router.post("/discoveries")
def save_discovery(payload: DiscoveryRecordRequest, db: Session = Depends(get_db)):
    """Enregistre un monument scanné ou mis en favori par un utilisateur."""
    return CultureService.record_discovery(
        db=db,
        monument_id=payload.monument_id,
        apprenant_id=payload.apprenant_id,
        confidence=payload.confidence,
        is_favorite=payload.is_favorite,
        notes=payload.notes,
    )


@router.get("/discoveries")
def get_user_discoveries(
    apprenant_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Récupère l'historique des découvertes enregistrées."""
    return CultureService.get_discoveries(db, apprenant_id=apprenant_id)
