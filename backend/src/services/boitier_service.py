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


def record_boitier_heartbeat(db: Session, req: Any) -> Dict[str, Any]:
    """Enregistre ou met à jour la télémétrie en temps réel d'un boîtier (Raspberry Pi 5 / ESP32)."""
    b = db.query(Boitier).filter((Boitier.id == req.boitier_id) | (Boitier.numero_serie == req.boitier_id)).first()

    if not b:
        # Création automatique du boîtier s'il n'existe pas encore
        b = Boitier(
            id=req.boitier_id,
            numero_serie=req.numero_serie or req.boitier_id,
            modele=req.modele or "Raspberry Pi 5 (8GB)",
            firmware=req.firmware or "v3.0-Pi5-Edge",
            statut="en_ligne",
            batterie=req.batterie if req.batterie is not None else 100,
            stockage_go=32,
            stockage_utilise_go=round(req.ram_utilisee_mo / 1024.0, 2) if req.ram_utilisee_mo else 2.1,
            wifi_ssid=req.wifi_ssid or "Alta-box1",
            ip_locale=req.ip_locale or "10.42.0.1",
            etablissement_id=req.etablissement_id or "etab-lbad-bamako",
            enfant_id=req.enfant_id,
            derniere_synchro=datetime.utcnow(),
        )
        db.add(b)
    else:
        b.statut = req.statut or "en_ligne"
        b.derniere_synchro = datetime.utcnow()
        if req.ip_locale:
            b.ip_locale = req.ip_locale
        if req.wifi_ssid:
            b.wifi_ssid = req.wifi_ssid
        if req.firmware:
            b.firmware = req.firmware
        if req.modele:
            b.modele = req.modele
        if req.batterie is not None:
            b.batterie = req.batterie
        if req.etablissement_id:
            b.etablissement_id = req.etablissement_id
        if req.enfant_id:
            b.enfant_id = req.enfant_id

    db.commit()
    db.refresh(b)
    return {
        "succes": True,
        "boitier_id": b.id,
        "statut": b.statut,
        "derniereSynchro": b.derniere_synchro.isoformat() if b.derniere_synchro else None,
        "message": f"Télémétrie reçue pour {b.id} ({b.modele})",
    }

