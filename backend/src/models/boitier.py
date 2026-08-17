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
