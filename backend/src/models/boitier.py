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
