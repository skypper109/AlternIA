"""
Routes API pour le Défi National Scolaire du Mali (Module B).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Dict, Optional

from backend.src.db.database import get_db
from backend.src.services.defi_national_service import (
    get_classement_defi,
    get_defis_actifs,
    soumettre_reponses_defi,
)

router = APIRouter(prefix="/api/defi-national", tags=["Défi National Scolaire"])


class SoumettreDefiRequest(BaseModel):
    defi_id: str
    apprenant_id: str
    apprenant_nom: str
    apprenant_classe: str
    reponses: Dict[str, int] = Field(description="Ex: {'q1': 0, 'q2': 1}")
    temps_ecoule_sec: int = Field(ge=1, description="Temps total mis par l'élève en secondes")
    adversaire_nom: Optional[str] = Field(None, description="Nom du rival malien (fictif ou réel)")
    adversaire_score: Optional[int] = Field(None, description="Score simulé ou réel du rival")
    adversaire_temps_sec: Optional[int] = Field(None, description="Temps en secondes du rival")


@router.get("/actifs")
def get_defis(
    classe: Optional[str] = Query(None, description="Niveau de classe (ex: 12eme, 11eme, TSE)"),
    periode: Optional[str] = Query(None, description="Période scolaire (ex: trimestre_1, trimestre_2, trimestre_3)"),
    db: Session = Depends(get_db),
):
    """Retourne la liste des épreuves nationales en cours avec questions sans les réponses."""
    return get_defis_actifs(db, classe, periode)


@router.post("/soumettre")
def api_soumettre(req: SoumettreDefiRequest, db: Session = Depends(get_db)):
    """
    Validation serveur des réponses d'un Défi National :
    Calcule le score, permet de rejouer pour faire grimper son score,
    confronte l'élève à son rival et n'attribue des pièces qu'en cas de victoire.
    """
    try:
        return soumettre_reponses_defi(
            db=db,
            defi_id=req.defi_id,
            apprenant_id=req.apprenant_id,
            apprenant_nom=req.apprenant_nom,
            apprenant_classe=req.apprenant_classe,
            reponses=req.reponses,
            temps_ecoule_sec=req.temps_ecoule_sec,
            adversaire_nom=req.adversaire_nom,
            adversaire_score=req.adversaire_score,
            adversaire_temps_sec=req.adversaire_temps_sec,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la validation du défi : {e}")


@router.get("/{defi_id}/classement")
def get_classement(
    defi_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Classement national officiel pour une session de défi donnée."""
    return get_classement_defi(db, defi_id, limit)
