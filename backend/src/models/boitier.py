"""
Schémas Pydantic pour la gestion des boîtiers physiques.
"""

from typing import Optional
from pydantic import BaseModel


class BoitierSyncRequest(BaseModel):
    force: bool = False


class BoitierWifiRequest(BaseModel):
    ssid: str
    mot_de_passe: Optional[str] = None


class BoitierCreateRequest(BaseModel):
    nom: str
    code_unique: str
    modele: Optional[str] = "Alternia Box v2"
    etablissement_id: Optional[str] = "etab-lbad-bamako"
    enfant_id: Optional[str] = None


class BoitierHeartbeatRequest(BaseModel):
    boitier_id: str
    numero_serie: Optional[str] = None
    modele: Optional[str] = "Raspberry Pi 5 (8GB)"
    firmware: Optional[str] = "v3.0-Pi5-Edge"
    ip_locale: Optional[str] = "10.42.0.1"
    wifi_ssid: Optional[str] = "Alta-box1"
    eleves_connectes: Optional[int] = 0
    cpu_temp: Optional[float] = None
    ram_utilisee_mo: Optional[float] = None
    ram_totale_mo: Optional[float] = None
    batterie: Optional[int] = 100
    statut: Optional[str] = "en_ligne"
    etablissement_id: Optional[str] = "etab-lbad-bamako"
    enfant_id: Optional[str] = None

