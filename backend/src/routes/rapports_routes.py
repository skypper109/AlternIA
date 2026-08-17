"""
Routes API pour la génération et consultation des rapports d'activité (connecté à alta_db).
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.src.db.database import get_db
from backend.src.db.models import RapportModel

router = APIRouter(prefix="/api/rapports", tags=["Rapports Pédagogiques"])


class GenererRapportRequest(BaseModel):
    titre: str
    periode: str = "Semaine en cours"
    typeFichier: str = "pdf"
    etablissementId: Optional[str] = "etab-lbad-01"


def serialize_rapport(r: RapportModel) -> Dict[str, Any]:
    return {
        "id": r.id,
        "etablissementId": r.etablissement_id,
        "titre": r.titre,
        "periode": r.periode,
        "dateDebut": r.date_debut.isoformat() if r.date_debut else None,
        "dateFin": r.date_fin.isoformat() if r.date_fin else None,
        "type": r.type_fichier,
        "statut": r.statut,
        "tailleFichier": r.taille_fichier_octets,
        "urlTelechargement": r.url_telechargement or f"/api/rapports/{r.id}/telecharger",
        "dateGeneration": r.date_generation.isoformat() if r.date_generation else None,
    }


@router.get("")
def api_list_rapports(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Liste de tous les rapports pédagogiques générés."""
    rapports = db.query(RapportModel).order_by(RapportModel.date_generation.desc()).all()
    if not rapports:
        now = datetime.utcnow()
        r1 = RapportModel(
            titre="Bilan Hebdomadaire d'Apprentissage ALTA",
            periode="Semaine en cours",
            date_debut=now - timedelta(days=7),
            date_fin=now,
            type_fichier="pdf",
            statut="genere",
            taille_fichier_octets=460800,
        )
        r2 = RapportModel(
            titre="Rapport Mensuel des Notions Critiques (SVT & Maths)",
            periode="Mois en cours",
            date_debut=now - timedelta(days=30),
            date_fin=now,
            type_fichier="pdf",
            statut="genere",
            taille_fichier_octets=840000,
        )
        r3 = RapportModel(
            titre="Export Analytique Brut des Interactions des Boîtiers",
            periode="Trimestre T1",
            date_debut=now - timedelta(days=90),
            date_fin=now,
            type_fichier="excel",
            statut="genere",
            taille_fichier_octets=1250000,
        )
        db.add_all([r1, r2, r3])
        db.commit()
        rapports = [r1, r2, r3]
    return [serialize_rapport(r) for r in rapports]


@router.post("/generer")
def api_generer_rapport(req: GenererRapportRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Déclenche la génération d'un nouveau rapport d'activité."""
    now = datetime.utcnow()
    taille = 520000 if req.typeFichier == "pdf" else 1150000
    r = RapportModel(
        titre=req.titre,
        periode=req.periode,
        date_debut=now - timedelta(days=7),
        date_fin=now,
        type_fichier=req.typeFichier,
        statut="genere",
        taille_fichier_octets=taille,
        etablissement_id=req.etablissementId,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return serialize_rapport(r)
