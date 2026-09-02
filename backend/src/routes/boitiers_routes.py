"""
Routes API pour la gestion et la synchronisation des boîtiers physiques.
"""

from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.src.db.database import get_db
from backend.src.models.boitier import BoitierCreateRequest, BoitierSyncRequest, BoitierWifiRequest
from backend.src.services.boitier_service import (
    configure_boitier_wifi,
    create_boitier,
    delete_boitier,
    get_boitier_detail,
    list_boitiers,
    sync_boitier,
)

router = APIRouter(prefix="/api/boitiers", tags=["Boîtiers Physiques"])


@router.get("")
def api_liste_boitiers(db: Session = Depends(get_db)):
    """Liste de tous les boîtiers physiques avec statut, batterie et stockage."""
    return list_boitiers(db)


@router.post("")
def api_creer_boitier(req: BoitierCreateRequest, db: Session = Depends(get_db)):
    """Enregistre un nouveau boîtier physique."""
    return create_boitier(db, req)


@router.get("/{boitier_id}")
def api_detail_boitier(boitier_id: str, db: Session = Depends(get_db)):
    """Détails d'un boîtier spécifique."""
    return get_boitier_detail(db, boitier_id)


@router.delete("/{boitier_id}")
def api_supprimer_boitier(boitier_id: str, db: Session = Depends(get_db)):
    """Supprime un boîtier de la flotte."""
    return delete_boitier(db, boitier_id)


@router.post("/{boitier_id}/sync")
def api_sync_boitier(boitier_id: str, req: Optional[BoitierSyncRequest] = None, db: Session = Depends(get_db)):
    """Déclenche la synchronisation pédagogique du boîtier."""
    return sync_boitier(db, boitier_id, req)


@router.post("/{boitier_id}/wifi")
def api_config_wifi_boitier(boitier_id: str, req: BoitierWifiRequest, db: Session = Depends(get_db)):
    """Met à jour les paramètres Wi-Fi du boîtier."""
    return configure_boitier_wifi(db, boitier_id, req)
