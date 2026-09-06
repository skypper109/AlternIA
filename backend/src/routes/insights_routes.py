"""
Routes API pour les insights pédagogiques et statistiques globales en temps réel.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.src.db.database import get_db
from backend.src.services.analytics_service import (
    get_realtime_insights,
    get_realtime_statistiques,
)

router = APIRouter(tags=["Insights & Statistiques"])


@router.get("/api/insights")
def api_insights(
    periode: str = Query("semaine", description="Filtre temporel: jour, semaine, mois, trimestre"),
    db: Session = Depends(get_db)
):
    """Insights et intelligence pédagogique en temps réel (connectés à alta_db)."""
    return get_realtime_insights(db, periode=periode)


@router.get("/api/statistiques")
def api_statistiques(
    periode: str = Query("semaine", description="Filtre temporel: jour, semaine, mois, trimestre"),
    etablissement_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Statistiques globales d'apprentissage en temps réel pour le portail d'administration."""
    return get_realtime_statistiques(db, periode=periode)
