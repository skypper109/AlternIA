"""
Routes API pour le programme de Parrainage Éducatif AlterniA (Module A).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional

from backend.src.db.database import get_db
from backend.src.services.parrainage_service import (
    associer_et_valider_parrainage,
    get_referral_summary,
)

router = APIRouter(prefix="/api/parrainage", tags=["Parrainage & Récompenses"])


class ValiderParrainageRequest(BaseModel):
    filleul_id: str
    code_parrainage: str = Field(min_length=4, max_length=20)


@router.get("/summary")
def get_parrainage_summary(
    student_id: str = Query("eleve_defaut", description="ID de l'élève parrain"),
    student_name: str = Query("Élève", description="Nom affiché"),
    db: Session = Depends(get_db),
):
    """Retourne le code unique, le lien, le nombre de filleuls et la progression vers l'abonnement Premium."""
    return get_referral_summary(db, student_id, student_name)


@router.post("/valider")
def api_valider_parrainage(
    req: ValiderParrainageRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Valide l'utilisation d'un code de parrainage par un nouvel élève.
    Crédite les pièces côté serveur et déclenche l'activation Premium si seuil atteint.
    """
    client_ip = request.client.host if request.client else None
    try:
        res = associer_et_valider_parrainage(
            db=db,
            filleul_id=req.filleul_id,
            code_parrainage=req.code_parrainage,
            ip_client=client_ip,
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la validation du parrainage : {e}")
