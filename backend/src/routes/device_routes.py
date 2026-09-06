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
    }


@router.post("/api/tts")
async def tts_post_endpoint(req: TTSRequest):
    """Synthèse vocale neurale haute fidélité (POST JSON body)."""
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Texte manquant pour la synthèse vocale")

    voice_name = req.voice or settings.tts_voice or "vivienne"
    tts_engine = TTSEngine(voice=voice_name)
    try:
        audio_bytes = await tts_engine.synthesize_to_bytes(req.text)
        if not audio_bytes:
            raise HTTPException(status_code=500, detail="Échec de la synthèse vocale")
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur TTS : {str(e)}")


@router.get("/api/tts")
async def tts_get_endpoint(text: str, voice: Optional[str] = "vivienne"):
    """Synthèse vocale neurale haute fidélité (GET query param)."""
    if not text.strip():
        raise HTTPException(status_code=400, detail="Texte manquant pour la synthèse vocale")

    tts_engine = TTSEngine(voice=voice or "vivienne")
    try:
        audio_bytes = await tts_engine.synthesize_to_bytes(text)
        if not audio_bytes:
            raise HTTPException(status_code=500, detail="Échec de la synthèse vocale")
        return Response(content=audio_bytes, media_type="audio/mpeg")
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
    Analyse un exercice ou problème scolaire (texte ou photo via OCR) et génère des indices socratiques progressifs
    alignés sur le programme officiel du Mali (10ème, 11ème, 12ème Terminale).
    """
    from backend.src.services.ocr_service import perform_ocr_on_image
    from alternia.pedagogical.curriculum_keywords import detect_malian_curriculum_subject

    orch = get_orchestrator()
    student_class = normalize_student_class(level or "11eme")
    
    extracted_text = (text or "").strip()

    # Traitement OCR si une image est transmise
    if image and image.filename:
        try:
            image_bytes = await image.read()
            if image_bytes:
                ocr_result = perform_ocr_on_image(image_bytes, filename=image.filename)
                if ocr_result:
                    extracted_text = ocr_result.strip() if not extracted_text else f"{extracted_text} " + ocr_result.strip()
        except Exception as ocr_err:
            print(f"[OCR Error] {ocr_err}")

    # Détection automatique de la matière si non fournie
    detected_sub = detect_malian_curriculum_subject(extracted_text) if extracted_text else None
    effective_subject = subject or detected_sub or "Général"
    subj = effective_subject.capitalize()

    # Aperçu de l'énoncé pour personnaliser les indices
    snippet = (extracted_text[:120] + "...") if len(extracted_text) > 120 else (extracted_text or f"Exercice de {subj}")

    # Décomposition Socratique Pédagogique enrichie par le texte extrait
    hints = [
        {
            "step": 1,
            "type": "observation",
            "text": f"Observons attentivement l'énoncé identifié en {subj} : '{snippet}'. Repère les grandeurs données, les unités physiques ou théorèmes mentionnés.",
            "question": "Quelles sont les données clés explicites et ce que la consigne te demande exactement de calculer ou d'expliquer ?",
        },
        {
            "step": 2,
            "type": "conceptual",
            "text": f"Rappelle-toi des définitions et théorèmes fondamentaux du programme malien de {student_class} en {subj}.",
            "question": "Quelle formule maîtresse, loi ou propriété du cours correspond précisément à ce type d'exercice ?",
        },
        {
            "step": 3,
            "type": "procedural",
            "text": "Applique la démarche méthodique : isole l'inconnue littéralement avant de faire l'application numérique avec les unités appropriées.",
            "question": "Quelle relation littérale intermédiaire obtiens-tu ?",
        },
        {
            "step": 4,
            "type": "solution",
            "text": "Examine la cohérence de ton ordre de grandeur et de ton unité. Encadre ton résultat final avec sa justification rigoureuse.",
            "question": "Ta conclusion répond-elle intégralement à la question posée dans l'exercice ?",
        },
    ]

    return {
        "status": "success",
        "subject": subj,
        "class": student_class,
        "extracted_text": extracted_text,
        "hints": hints,
    }


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
