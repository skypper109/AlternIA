"""
Service de gestion des boîtiers physiques AlternIA Box.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.src.db.models import Boitier
from backend.src.models.boitier import BoitierSyncRequest, BoitierWifiRequest


def list_boitiers(db: Session) -> List[Dict[str, Any]]:
    """Retourne la liste de tous les boîtiers physiques."""
    boitiers = db.query(Boitier).all()
    return [
        {
            "id": b.id,
            "numeroSerie": b.numero_serie,
            "modele": b.modele,
            "firmware": b.firmware,
            "statut": b.statut,
            "batterie": b.batterie,
            "stockageGo": b.stockage_go,
            "stockageUtiliseGo": b.stockage_utilise_go,
            "wifiSsid": b.wifi_ssid,
            "ipLocale": b.ip_locale,
            "derniereSynchro": b.derniere_synchro.isoformat() if b.derniere_synchro else None,
            "etablissementId": b.etablissement_id,
            "enfantId": b.enfant_id,
        }
        for b in boitiers
    ]


def get_boitier_detail(db: Session, boitier_id: str) -> Dict[str, Any]:
    """Retourne les détails d'un boîtier spécifique."""
    b = db.query(Boitier).filter(Boitier.id == boitier_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Boîtier introuvable")
    return {
        "id": b.id,
        "numeroSerie": b.numero_serie,
        "modele": b.modele,
        "firmware": b.firmware,
        "statut": b.statut,
        "batterie": b.batterie,
        "stockageGo": b.stockage_go,
        "stockageUtiliseGo": b.stockage_utilise_go,
        "wifiSsid": b.wifi_ssid,
        "ipLocale": b.ip_locale,
        "derniereSynchro": b.derniere_synchro.isoformat() if b.derniere_synchro else None,
        "etablissementId": b.etablissement_id,
        "enfantId": b.enfant_id,
    }


def sync_boitier(db: Session, boitier_id: str, req: Optional[BoitierSyncRequest] = None) -> Dict[str, Any]:
    """Synchronise un boîtier avec la base de données centrale."""
    b = db.query(Boitier).filter(Boitier.id == boitier_id).first()
    if b:
        b.derniere_synchro = datetime.utcnow()
        b.statut = "en_ligne"
        db.commit()
    return {
        "succes": True,
        "statut": "synchronise",
        "timestamp": datetime.utcnow().isoformat(),
        "elementsSynchronises": 14,
    }


def configure_boitier_wifi(db: Session, boitier_id: str, req: BoitierWifiRequest) -> Dict[str, Any]:
    """Configure le réseau Wi-Fi d'un boîtier."""
    b = db.query(Boitier).filter(Boitier.id == boitier_id).first()
    if b:
        b.wifi_ssid = req.ssid
        db.commit()
    return {"succes": True, "ssid": req.ssid, "message": "Paramètres Wi-Fi mis à jour"}
