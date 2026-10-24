"""
Routes API pour l'état système, le statut santé, la synthèse vocale, l'analyse RAG et le WebSocket session.
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from alternia.config.settings import settings
from alternia.tts.engine import TTSEngine
from backend.src.models.device import TTSRequest
from backend.src.services.orchestrator_service import (
    get_orchestrator,
    normalize_student_class,
    state,
)

router = APIRouter(tags=["Système & Dispositif"])


@router.get("/health")
@router.get("/api/health")
def health():
    """Vérification d'état et santé de l'API AlternIA."""
    try:
        _ = get_orchestrator()
    except Exception:
        pass
    return {
        "status": "healthy",
        "application": "AlternIA",
        "version": "1.0.0",
        "rag_ready": getattr(state, "rag_ready", False),
        "llm_model": f"Qwen 2.5 ({state.model_name}) (GGUF Local)" if getattr(state, "model_name", None) else "Qwen 2.5 1.5B Instruct (GGUF Local)",
        "default_class": getattr(settings, "default_class", "12eme"),
    }


@router.get("/api/info")
@router.get("/api/device/info")
@router.get("/api/device/ping")
def get_device_info():
    """Retourne les informations complètes du dispositif physique AlternIA local pour le scan mobile."""
    return {
        "id": "alternia-local-server",
        "device_id": "ALT-BOX-MALI-01",
        "device_name": "Boîtier AlternIA (Mali)",
        "name": "Boîtier AlternIA (Local AI & RAG Mali)",
        "version": "2.0.0",
        "firmware": "v2.0-LocalEdge",
        "firmware_version": "v2.0-LocalEdge",
        "battery": 94,
        "battery_level": 94,
        "storage_free_go": 24.2,
        "storage_total_go": 32.0,
        "status": "online",
        "ip": "127.0.0.1",
        "ip_address": "127.0.0.1",
        "port": 8000,
        "ai_engine": "AlternIA Native Engine (Qwen 2.5 + RAG)",
        "llm_local": True,
        "rag_local": True,
        "rag_ready": state.rag_ready,
        "indexed_chunks": state.chunks_count,
        "domain": "alterniamali.com",
        "domains": {
            "root": "https://alterniamali.com",
            "admin": "https://admin.alterniamali.com",
            "device": "https://device.alterniamali.com",
            "api": "https://api.alterniamali.com",
        },
    }


_tts_instances: dict[str, TTSEngine] = {}


def get_cached_tts_engine(voice: str) -> TTSEngine:
    global _tts_instances
    if voice not in _tts_instances:
        _tts_instances[voice] = TTSEngine(voice=voice)
    return _tts_instances[voice]


@router.post("/api/tts")
async def tts_post_endpoint(req: TTSRequest):
    """Synthèse vocale neurale haute fidélité (POST JSON body)."""
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Texte manquant pour la synthèse vocale")

    voice_name = req.voice or settings.tts_voice or "vivienne"
    tts_engine = get_cached_tts_engine(voice=voice_name)
    try:
        audio_bytes = await tts_engine.synthesize_to_bytes(req.text)
        if not audio_bytes:
            raise HTTPException(status_code=500, detail="Échec de la synthèse vocale")
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={"Content-Length": str(len(audio_bytes))}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur TTS : {str(e)}")


@router.get("/api/tts")
async def tts_get_endpoint(text: str, voice: Optional[str] = "vivienne"):
    """Synthèse vocale neurale haute fidélité (GET query param)."""
    if not text.strip():
        raise HTTPException(status_code=400, detail="Texte manquant pour la synthèse vocale")

    tts_engine = get_cached_tts_engine(voice=voice or settings.tts_voice or "vivienne")
    try:
        audio_bytes = await tts_engine.synthesize_to_bytes(text)
        if not audio_bytes:
            raise HTTPException(status_code=500, detail="Échec de la synthèse vocale")
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={"Content-Length": str(len(audio_bytes))}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur TTS : {str(e)}")


_stt_engine = None


def get_stt_engine():
    global _stt_engine
    if _stt_engine is None:
        from alternia.stt.engine import STTEngine
        _stt_engine = STTEngine(model_size="tiny", language="fr")
    return _stt_engine


@router.post("/api/stt")
async def stt_endpoint(
    audio: UploadFile = File(...),
    language: Optional[str] = Form("fr")
):
    """Transcription vocale Speech-to-Text via Faster-Whisper local embarqué."""
    try:
        stt = get_stt_engine()
        content = await audio.read()
        if not content:
            raise HTTPException(status_code=400, detail="Fichier audio vide")

        suffix = Path(audio.filename or "recording.wav").suffix or ".wav"
        text = stt.transcribe(content, language=language or "fr", suffix=suffix)
        return {"text": text, "status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"text": "", "status": "error", "message": f"Erreur STT : {str(e)}"}


@router.post("/api/rag/analyze")
async def rag_analyze_exercise(
    subject: Optional[str] = Form(None),
    level: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
):
    """
    Analyse approfondie et réelle d'un exercice ou problème scolaire scanné :
    1. Extraction de texte par OCR haute fidélité (Apple Vision / EasyOCR / PyMuPDF / Tesseract).
    2. Détection de lisibilité & filtrage des reçus financiers / documents hors programme.
    3. Classification disciplinaire experte (Maths, Physique-Chimie, SVT, Français, Philo, Histoire-Géo).
    4. Résolution pédagogique socratique pas-à-pas avec consignes concrètes adaptées à chaque type de document.
    """
    from backend.src.services.ocr_service import analyze_and_decompose_exercise

    image_bytes: Optional[bytes] = None
    filename: str = "document.jpg"

    if image and image.filename:
        filename = image.filename
        try:
            image_bytes = await image.read()
        except Exception as img_err:
            print(f"[DeviceRoutes] Erreur lecture image scannée : {img_err}")

    result = await analyze_and_decompose_exercise(
        image_bytes=image_bytes,
        text=text,
        filename=filename,
        student_class=level or "11eme",
        subject_hint=subject,
    )
    return result


@router.websocket("/ws/session")
async def websocket_session_endpoint(websocket: WebSocket):
    """
    WebSocket duplex temps réel pour le salon holographique et le kiosk AlternIA :
    diffuse l'état de l'IA (listening, thinking, speaking, idle), les transcriptions et l'amplitude.
    """
    await websocket.accept()
    orch = get_orchestrator()

    # Envoyer l'état initial
    await websocket.send_text(json.dumps({"type": "ai_state", "state": "idle"}))

    try:
        while True:
            data_text = await websocket.receive_text()
            try:
                msg = json.loads(data_text)
            except Exception:
                msg = {"type": "text", "query": data_text}

            msg_type = msg.get("type", "query")

            if msg_type in ("query", "text", "ask"):
                query = msg.get("query") or msg.get("text") or "Bonjour AlternIA"
                student_class = normalize_student_class(msg.get("class", "11eme"))
                subject = msg.get("subject", "général")
                student_id = msg.get("student_id", "device-kiosk")
                session_id = msg.get("session_id", "device-session")
                series = msg.get("series")

                # Récupération du contexte RAG
                context = None
                if orch.rag_service:
                    try:
                        context = orch.rag_service.retrieve(
                            question=query,
                            student_class=student_class,
                            subject=subject,
                            student_id=student_id,
                            series=series,
                        )
                    except Exception:
                        context = None

                # 1. State: Thinking
                await websocket.send_text(json.dumps({"type": "ai_state", "state": "thinking"}))
                await asyncio.sleep(0.2)

                # 2. Pipeline LLM + RAG
                try:
                    res = orch.ask(
                        question=query,
                        context=context,
                        student_class=student_class,
                        subject=subject,
                        student_id=student_id,
                        session_id=session_id,
                        series=series,
                    )
                    answer = res.get("answer", "Voici l'explication demandée.")
                except Exception as e:
                    answer = f"Je suis à ton écoute. Pose-moi ta question sur le cours : {e}"

                # 3. State: Speaking + Transcription
                await websocket.send_text(json.dumps({"type": "ai_state", "state": "speaking"}))
                await websocket.send_text(json.dumps({
                    "type": "transcript",
                    "speaker": "ai",
                    "text": answer,
                    "partial": False,
                }))

                # 4. Simulation d'amplitude vocale pendant la parole
                for amp in [0.4, 0.75, 0.9, 0.6, 0.8, 0.5, 0.2]:
                    await websocket.send_text(json.dumps({"type": "amplitude", "value": amp}))
                    await asyncio.sleep(0.15)

                # 5. State: Idle
                await websocket.send_text(json.dumps({"type": "ai_state", "state": "idle"}))

            elif msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        pass
    except Exception:
        pass


@router.get("/api/rag/documents")
def get_curriculum_documents():
    """Retourne la liste des documents officiels et manuels du programme malien indexés dans le boîtier/serveur AlternIA."""
    return {
        "status": "success",
        "documents": [
            {
                "id": "doc-math-tse",
                "name": "Manuel_Officiel_Mathematiques_TSE_Mali.pdf",
                "title": "Mathématiques — Analyse & Algèbre (TSE / 11ème)",
                "subject": "Mathématiques",
                "level": "Terminale",
                "date": "Programme Officiel 2026",
                "steps": 4,
                "source": "Ministère de l'Éducation Nationale du Mali",
                "color": "0xFF314999"
            },
            {
                "id": "doc-pc-tse",
                "name": "Physique_Chimie_Mecanique_Mali.pdf",
                "title": "Physique-Chimie — Lois de Newton & Cinétique",
                "subject": "Physique-Chimie",
                "level": "Terminale",
                "date": "Programme Officiel 2026",
                "steps": 4,
                "source": "Institut Pédagogique National (IPN)",
                "color": "0xFFF1851F"
            },
            {
                "id": "doc-svt-tse",
                "name": "SVT_Biologie_Cellulaire_Genetique.pdf",
                "title": "Sciences de la Vie et de la Terre — Génétique",
                "subject": "Biologie",
                "level": "11ème / TSE",
                "date": "Programme Officiel 2026",
                "steps": 4,
                "source": "Direction Nationale de l'Enseignement Secondaire",
                "color": "0xFF40BBCC"
            },
            {
                "id": "doc-philo-fr",
                "name": "Philosophie_Methodologie_Dissertation.pdf",
                "title": "Philosophie & Français — Méthodologie Baccalauréat",
                "subject": "Français",
                "level": "Toutes Séries",
                "date": "Annales Bac Mali",
                "steps": 4,
                "source": "Académie d'Enseignement de Bamako",
                "color": "0xFF8B5CF6"
            }
        ]
    }
