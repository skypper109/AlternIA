"""
Routes API pour la gestion des Abonnements Scolaires et Droits d'Accès Premium (Module H).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.src.db.database import get_db
from backend.src.services.abonnement_service import (
    get_offres_disponibles,
    get_statut_abonnement_apprenant,
    souscrire_abonnement,
)

router = APIRouter(prefix="/api/abonnements", tags=["Abonnements & Premium"])


class SouscriptionRequest(BaseModel):
    apprenant_id: str
    offre_id: str
    moyen_paiement: str = "MOBILE_MONEY"


@router.get("/offres")
def get_offres(db: Session = Depends(get_db)):
    """Catalogue officiel des offres d'abonnement (mensuel, trimestriel, annuel)."""
    return get_offres_disponibles(db)


@router.get("/status")
def get_status(
    student_id: str = Query(..., description="ID de l'élève"),
    db: Session = Depends(get_db),
):
    """
    Source de vérité pour vérifier les droits d'accès d'un apprenant.
    Ne jamais autoriser de fonction Premium côté client sans la réponse de cet endpoint.
    """
    return get_statut_abonnement_apprenant(db, student_id)


@router.post("/souscrire")
def api_souscrire(req: SouscriptionRequest, db: Session = Depends(get_db)):
    """Souscrit à une offre d'abonnement scolaire."""
    try:
        return souscrire_abonnement(
            db=db,
            student_id=req.apprenant_id,
            offre_id=req.offre_id,
            moyen_paiement=req.moyen_paiement,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de souscription : {e}")
