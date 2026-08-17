"""
Routes API pour l'état système, le statut santé, la synthèse vocale et les infos matériel.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Response

from alternia.config.settings import settings
from alternia.tts.engine import TTSEngine
from backend.src.models.device import TTSRequest
from backend.src.services.orchestrator_service import get_orchestrator, state

router = APIRouter(tags=["Système & Dispositif"])


@router.get("/")
@router.get("/health")
@router.get("/api/health")
def health():
    """Vérification d'état et santé de l'API AlternIA."""
    _ = get_orchestrator()
    return {
        "status": "healthy",
        "application": "AlternIA",
        "version": "1.0.0",
        "rag_ready": state.rag_ready,
        "rag_chunks_count": state.chunks_count,
        "llm_model": "Qwen 2.5 3B Instruct (GGUF Local)",
        "default_class": settings.default_class,
    }


@router.post("/api/tts")
@router.get("/api/tts")
async def tts_endpoint(text: Optional[str] = None, req: Optional[TTSRequest] = None):
    """Synthèse vocale neurale haute fidélité (voix Vivienne par défaut)."""
    raw_text = (req.text if req else None) or text or ""
    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="Texte manquant pour la synthèse vocale")

    voice_name = (req.voice if req else None) or settings.tts_voice or "vivienne"
    tts_engine = TTSEngine(voice=voice_name)
    try:
        audio_bytes = await tts_engine.synthesize_to_bytes(raw_text)
        if not audio_bytes:
            raise HTTPException(status_code=500, detail="Échec de la synthèse vocale")
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur TTS : {str(e)}")


@router.get("/api/device/info")
def get_device_info():
    """Retourne les informations du dispositif physique AlternIA local."""
    return {
        "device_id": "alternia-device-01",
        "device_name": "AlternIA Box (Mali)",
        "firmware": "v2.0-LocalEdge",
        "ai_engine": "AlternIA Native Engine",
        "llm_local": True,
        "rag_local": True,
        "indexed_chunks": state.chunks_count,
    }
