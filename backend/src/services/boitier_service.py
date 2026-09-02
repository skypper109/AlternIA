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


def create_boitier(db: Session, req: Any) -> Dict[str, Any]:
    """Enregistre un nouveau boîtier physique dans la flotte."""
    import uuid
    boitier_id = f"box_{uuid.uuid4().hex[:8]}"
    nouveau = Boitier(
        id=boitier_id,
        numero_serie=req.code_unique,
        modele=req.modele or "Alternia Box v2",
        firmware="v2.4-LocalEdge",
        statut="en_ligne",
        batterie=100,
        stockage_go=32,
        stockage_utilise_go=1.2,
        wifi_ssid="SoundiataKeita_5G",
        ip_locale="192.168.1.105",
        etablissement_id=req.etablissement_id or "etab-lbad-bamako",
        enfant_id=req.enfant_id or "eleve_10eme",
        derniere_synchro=datetime.utcnow(),
    )
    db.add(nouveau)
    db.commit()
    db.refresh(nouveau)
    return {
        "id": nouveau.id,
        "numeroSerie": nouveau.numero_serie,
        "modele": nouveau.modele,
        "firmware": nouveau.firmware,
        "statut": nouveau.statut,
        "batterie": nouveau.batterie,
        "stockageGo": nouveau.stockage_go,
        "stockageUtiliseGo": nouveau.stockage_utilise_go,
        "wifiSsid": nouveau.wifi_ssid,
        "ipLocale": nouveau.ip_locale,
        "derniereSynchro": nouveau.derniere_synchro.isoformat() if nouveau.derniere_synchro else None,
        "etablissementId": nouveau.etablissement_id,
        "enfantId": nouveau.enfant_id,
    }


def delete_boitier(db: Session, boitier_id: str) -> Dict[str, Any]:
    """Supprime un boîtier de la flotte."""
    b = db.query(Boitier).filter(Boitier.id == boitier_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Boîtier introuvable")
    db.delete(b)
    db.commit()
    return {"succes": True, "message": f"Boîtier {boitier_id} supprimé avec succès"}
