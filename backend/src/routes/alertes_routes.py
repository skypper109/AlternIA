"""
Routes API pour la consultation et la résolution des alertes pédagogiques en temps réel.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.src.db.database import get_db
from backend.src.services.alerte_service import list_alertes, resolve_alerte

router = APIRouter(prefix="/api/alertes", tags=["Alertes Pédagogiques"])


@router.get("")
def api_liste_alertes(db: Session = Depends(get_db)):
    """Liste des alertes pédagogiques déclenchées en temps réel."""
    return list_alertes(db)


@router.put("/{alerte_id}/resoudre")
def api_resoudre_alerte(alerte_id: str, db: Session = Depends(get_db)):
    """Marque une alerte comme résolue."""
    return resolve_alerte(db, alerte_id)
