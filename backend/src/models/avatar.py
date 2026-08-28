from typing import Any, Dict, List, Optional
from pydantic import BaseModel


# 8 visèmes standard pour l'animation Sprite-Sheet
VISEME_IDS = ["REST", "CLOSED", "OPEN_SMALL", "OPEN_WIDE", "ROUND_O", "ROUND_U", "TEETH", "SMILE"]


class AvatarCreateRequest(BaseModel):
    nom: str
    matiere: str
    style_pedagogique: Optional[str] = "Bienveillant et interactif"
    voix_tts: Optional[str] = "vivienne"
    photo_url: Optional[str] = None
    video_url: Optional[str] = None
    audio_sample_url: Optional[str] = None
    audio_file_name: Optional[str] = None
    par_defaut: Optional[bool] = False
    landmarks: Optional[Dict[str, Any]] = None
    viseme_photos: Optional[Dict[str, str]] = None  # {"REST": "/api/avatars/images/xxx.jpg", ...}


class AvatarUpdateRequest(BaseModel):
    nom: Optional[str] = None
    matiere: Optional[str] = None
    style_pedagogique: Optional[str] = None
    voix_tts: Optional[str] = None
    photo_url: Optional[str] = None
    video_url: Optional[str] = None
    actif: Optional[bool] = None
    par_defaut: Optional[bool] = None
    landmarks: Optional[Dict[str, Any]] = None
    viseme_photos: Optional[Dict[str, str]] = None


class AvatarDetectLandmarksRequest(BaseModel):
    photo_url: Optional[str] = None
    file_name: Optional[str] = None


class StudioVocalTestRequest(BaseModel):
    phrase: str
    voix: Optional[str] = "vivienne"
    vitesse: Optional[float] = 1.0
    tonalite: Optional[float] = 0.0

