"""
Schémas Pydantic pour la synthèse vocale et les informations appareil.
"""

from typing import Optional
from pydantic import BaseModel


class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = "vivienne"
