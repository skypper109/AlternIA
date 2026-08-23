"""
Schémas Pydantic pour la création et la gestion des apprenants.
"""

from typing import Optional
from pydantic import BaseModel


class ApprenantCreateRequest(BaseModel):
    nom: str
    prenom: str
    classe: str
    serie: Optional[str] = "generale"
    matricule: Optional[str] = None
    etablissement_id: Optional[str] = "etab-lbad-bamako"
    boitier_id: Optional[str] = None
