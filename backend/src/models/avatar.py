"""
Schémas Pydantic pour les avatars pédagogiques et le studio vocal.
"""

from typing import Optional
from pydantic import BaseModel


class AvatarCreateRequest(BaseModel):
    nom: str
    matiere: str
    style_pedagogique: Optional[str] = "Bienveillant et interactif"
    voix_tts: Optional[str] = "vivienne"
    photo_url: Optional[str] = None
    audio_sample_url: Optional[str] = None
    audio_file_name: Optional[str] = None


class StudioVocalTestRequest(BaseModel):
    phrase: str
    voix: Optional[str] = "vivienne"
    vitesse: Optional[float] = 1.0
    tonalite: Optional[float] = 0.0
