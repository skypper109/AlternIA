import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
AI_ENGINE_DIR = ROOT_DIR / "ai-engine" / "src"

for p in (ROOT_DIR, AI_ENGINE_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from typing import Any, Dict, List
from fastapi import HTTPException, Response
from sqlalchemy.orm import Session

from alternia.tts.engine import TTSEngine
from backend.src.db.models import AvatarPedagogique
from backend.src.models.avatar import AvatarCreateRequest, StudioVocalTestRequest


def list_avatars(db: Session) -> List[Dict[str, Any]]:
    """Retourne la liste des avatars pédagogiques configurés."""
    avatars = db.query(AvatarPedagogique).all()
    return [
        {
            "id": av.id,
            "nom": av.nom,
            "matiere": av.matiere,
            "stylePedagogique": av.style_pedagogique,
            "voixTts": av.voix_tts,
            "photoUrl": av.photo_url,
            "audioUrl": av.audio_sample_url,
            "audioFileName": av.audio_file_name,
            "actif": av.actif,
            "parDefaut": av.par_defaut,
        }
        for av in avatars
    ]


def create_avatar(db: Session, req: AvatarCreateRequest) -> Dict[str, Any]:
    """Crée un nouvel avatar pédagogique."""
    av = AvatarPedagogique(
        nom=req.nom,
        matiere=req.matiere,
        style_pedagogique=req.style_pedagogique or "Bienveillant et interactif",
        voix_tts=req.voix_tts or "vivienne",
        photo_url=req.photo_url,
        audio_sample_url=req.audio_sample_url,
        audio_file_name=req.audio_file_name,
        actif=True,
    )
    db.add(av)
    db.commit()
    db.refresh(av)
    return {
        "id": av.id,
        "nom": av.nom,
        "matiere": av.matiere,
        "stylePedagogique": av.style_pedagogique,
        "voixTts": av.voix_tts,
        "photoUrl": av.photo_url,
        "actif": av.actif,
    }


def delete_avatar(db: Session, avatar_id: str) -> Dict[str, Any]:
    """Supprime un avatar pédagogique."""
    av = db.query(AvatarPedagogique).filter(AvatarPedagogique.id == avatar_id).first()
    if av:
        db.delete(av)
        db.commit()
    return {"succes": True, "id": avatar_id}


async def test_voice_audio(req: StudioVocalTestRequest) -> Response:
    """Génère un test audio pour le Studio Vocal."""
    tts_engine = TTSEngine(voice=req.voix or "vivienne")
    try:
        audio_bytes = await tts_engine.synthesize_to_bytes(req.phrase)
        if not audio_bytes:
            raise HTTPException(status_code=500, detail="Échec de la synthèse audio de test")
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur Studio Vocal TTS : {exc}")
