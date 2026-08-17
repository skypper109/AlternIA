"""
Routes API pour le programme de révision intelligente (connecté à la base de données).
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.src.db.database import get_db
from backend.src.db.models import SeanceRevisionModel

router = APIRouter(prefix="/api/programme-revision", tags=["Programme de Révision"])


class SeanceRevisionCreate(BaseModel):
    titre: str
    matiere: str
    jour: str
    heureDebut: str
    heureFin: str
    dureeMinutes: int = 45
    commentaire: Optional[str] = None
    statut: str = "PROGRAMMÉE"
    rappelMinutesAvant: int = 30


def serialize_seance(s: SeanceRevisionModel) -> Dict[str, Any]:
    return {
        "id": s.id,
        "titre": s.titre,
        "matiere": s.matiere,
        "jour": s.jour,
        "heureDebut": s.heure_debut,
        "heureFin": s.heure_fin,
        "dureeMinutes": s.duree_minutes,
        "commentaire": s.commentaire,
        "statut": s.statut,
        "rappelMinutesAvant": s.rappel_minutes_avant,
        "dateCreation": s.date_creation.isoformat() if s.date_creation else None,
    }


@router.get("")
def api_list_seances(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Liste des séances de révision personnalisées."""
    seances = db.query(SeanceRevisionModel).order_by(SeanceRevisionModel.jour.asc(), SeanceRevisionModel.heure_debut.asc()).all()
    if not seances:
        # Seed initial
        now_str = datetime.utcnow().strftime("%Y-%m-%d")
        s1 = SeanceRevisionModel(
            titre="Révision Équations du 2nd degré",
            matiere="MATHEMATIQUES",
            jour=now_str,
            heure_debut="17:00",
            heure_fin="17:45",
            duree_minutes=45,
            commentaire="Axer sur la méthode du discriminant et exercices pratiques.",
            statut="PROGRAMMÉE",
        )
        s2 = SeanceRevisionModel(
            titre="Quiz interactif Optique & Ondes",
            matiere="PHYSIQUE",
            jour=now_str,
            heure_debut="18:15",
            heure_fin="19:00",
            duree_minutes=45,
            commentaire="Session de questions courtes avec Vivienne.",
            statut="PROGRAMMÉE",
        )
        s3 = SeanceRevisionModel(
            titre="Zonation végétale & Écologie",
            matiere="SVT",
            jour=now_str,
            heure_debut="16:00",
            heure_fin="16:45",
            duree_minutes=45,
            commentaire="Révision des écosystèmes du Sahel.",
            statut="TERMINÉE",
        )
        db.add_all([s1, s2, s3])
        db.commit()
        seances = [s1, s2, s3]
    return [serialize_seance(s) for s in seances]


@router.post("")
def api_create_seance(req: SeanceRevisionCreate, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Crée une nouvelle séance de révision."""
    s = SeanceRevisionModel(
        titre=req.titre,
        matiere=req.matiere,
        jour=req.jour,
        heure_debut=req.heureDebut,
        heure_fin=req.heureFin,
        duree_minutes=req.dureeMinutes,
        commentaire=req.commentaire,
        statut=req.statut,
        rappel_minutes_avant=req.rappelMinutesAvant,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return serialize_seance(s)


@router.put("/{seance_id}")
def api_update_seance(seance_id: str, req: SeanceRevisionCreate, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Met à jour une séance de révision existante."""
    s = db.query(SeanceRevisionModel).filter(SeanceRevisionModel.id == seance_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Séance introuvable")
    s.titre = req.titre
    s.matiere = req.matiere
    s.jour = req.jour
    s.heure_debut = req.heureDebut
    s.heure_fin = req.heureFin
    s.duree_minutes = req.dureeMinutes
    s.commentaire = req.commentaire
    s.statut = req.statut
    s.rappel_minutes_avant = req.rappelMinutesAvant
    db.commit()
    db.refresh(s)
    return serialize_seance(s)


@router.delete("/{seance_id}")
def api_delete_seance(seance_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Supprime une séance de révision."""
    s = db.query(SeanceRevisionModel).filter(SeanceRevisionModel.id == seance_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Séance introuvable")
    db.delete(s)
    db.commit()
    return {"succes": True, "message": "Séance supprimée"}
