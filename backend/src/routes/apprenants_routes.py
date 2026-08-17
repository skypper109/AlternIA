"""
Routes API pour la consultation des apprenants et de leurs sessions d'apprentissage.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.src.db.database import get_db
from backend.src.services.apprenant_service import (
    get_apprenant_detail,
    list_apprenant_sessions,
    list_apprenants,
)

router = APIRouter(prefix="/api/apprenants", tags=["Apprenants"])


@router.get("")
def api_liste_apprenants(db: Session = Depends(get_db)):
    """Liste de tous les apprenants enregistrés avec leur taux de maîtrise."""
    return list_apprenants(db)


@router.get("/{apprenant_id}")
def api_detail_apprenant(apprenant_id: str, db: Session = Depends(get_db)):
    """Fiche détaillée d'un apprenant."""
    return get_apprenant_detail(db, apprenant_id)


@router.get("/{apprenant_id}/sessions")
def api_sessions_apprenant(apprenant_id: str, db: Session = Depends(get_db)):
    """Historique des sessions d'apprentissage d'un élève."""
    return list_apprenant_sessions(db, apprenant_id)
