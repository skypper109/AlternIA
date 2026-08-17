"""
Routes API pour le chat pédagogique, streaming SSE, curriculum et profil apprenant.
"""

import asyncio
import json
from pathlib import Path
from typing import AsyncIterator
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from alternia.learner.manager import LearningInteraction
from alternia.rag.contextualizer import QueryContextualizer
from backend.src.models.chat import (
    ChatRequest,
    ChatResponse,
    ChatSource,
    InteractionRecord,
    ResetSessionRequest,
)
from backend.src.services.orchestrator_service import (
    get_orchestrator,
    normalize_student_class,
    state,
)
from backend.src.services.learning_service import record_student_interaction

router = APIRouter(tags=["Chat Pédagogique"])


@router.post("/api/chat", response_model=ChatResponse)
@router.post("/api/ask", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    """Endpoint principal de réponse pédagogique non-streamée."""
    orch = get_orchestrator()
    norm_class = normalize_student_class(req.student_class)
    session_id = req.session_id or f"session_{req.student_id}"

    # Contexte RAG avec contextualisation multi-tours
    context = None
    if req.enable_rag and orch.rag_service:
        rag_query = req.question
        session = orch.conversation_manager.get(session_id)
        if session and session.messages:
            student_past_msgs = [m.content for m in session.messages if m.role == "student"]
            rag_query = QueryContextualizer.contextualize(
                current_question=req.question,
                past_student_messages=student_past_msgs,
                current_topic=getattr(session, "current_topic", None),
            )
        try:
            context = orch.rag_service.retrieve(
                question=rag_query,
                student_class=norm_class,
                subject=req.subject,
                student_id=req.student_id,
            )
        except Exception:
            context = None

    # Exécution du pipeline
    result = orch.ask(
        question=req.question,
        context=context,
        student_class=norm_class,
        subject=req.subject,
        student_id=req.student_id,
        session_id=session_id,
    )

    # Conversion des sources RAG
    formatted_sources: list[ChatSource] = []
    if context and hasattr(context, "sources"):
        for s in context.sources:
            doc = getattr(s, "source_document", getattr(s, "source", "Manuel scolaire"))
            doc_name = Path(str(doc)).name
            formatted_sources.append(
                ChatSource(
                    chunk_id=getattr(s, "chunk_id", None),
                    document=doc_name,
                    chapter=getattr(s, "chapter", None),
                    lesson=getattr(s, "lesson", None),
                    score=float(getattr(s, "score", 0.0)),
                    content_preview=getattr(s, "content", "")[:180],
                )
            )

    # Enregistrement en direct dans la base de données réelle
    record_student_interaction(
        student_id=req.student_id,
        student_class=norm_class,
        subject=result.get("subject") or req.subject,
        question=req.question,
        answer=result["answer"],
        sources=formatted_sources,
        intent=result.get("intent", "explanation"),
        session_id=session_id,
    )

    return ChatResponse(
        answer=result["answer"],
        intent=result.get("intent", "explanation"),
        student_class=norm_class,
        subject=result.get("subject"),
        sources=formatted_sources,
        should_ask_followup=result.get("should_ask_followup", False),
        followup_question=result.get("followup_question"),
        metadata=result.get("metadata", {}),
    )


@router.post("/api/chat/stream")
@router.post("/api/ask/stream")
async def chat_stream_endpoint(req: ChatRequest):
    """Endpoint de streaming Server-Sent Events (SSE) token par token."""
    orch = get_orchestrator()
    norm_class = normalize_student_class(req.student_class)
    session_id = req.session_id or f"session_{req.student_id}"

    # Contexte RAG avec contextualisation multi-tours
    context = None
    if req.enable_rag and orch.rag_service:
        rag_query = req.question
        session = orch.conversation_manager.get(session_id)
        if session and session.messages:
            student_past_msgs = [m.content for m in session.messages if m.role == "student"]
            rag_query = QueryContextualizer.contextualize(
                current_question=req.question,
                past_student_messages=student_past_msgs,
                current_topic=getattr(session, "current_topic", None),
            )
        try:
            context = orch.rag_service.retrieve(
                question=rag_query,
                student_class=norm_class,
                subject=req.subject,
                student_id=req.student_id,
            )
        except Exception:
            context = None

    # Sources pour l'événement final
    formatted_sources = []
    if context and hasattr(context, "sources"):
        for s in context.sources:
            doc = getattr(s, "source_document", getattr(s, "source", "Manuel scolaire"))
            doc_name = Path(str(doc)).name
            formatted_sources.append({
                "document": doc_name,
                "chapter": getattr(s, "chapter", None),
                "lesson": getattr(s, "lesson", None),
                "score": float(getattr(s, "score", 0.0)),
            })

    generator = orch.ask_stream(
        question=req.question,
        context=context,
        student_class=norm_class,
        subject=req.subject,
        student_id=req.student_id,
        session_id=session_id,
    )

    async def sse_generator() -> AsyncIterator[str]:
        full_text = ""
        for chunk in generator:
            full_text += chunk
            payload = json.dumps({"chunk": chunk, "done": False}, ensure_ascii=False)
            yield f"data: {payload}\n\n"
            await asyncio.sleep(0)

        # Enregistrement en direct dans la base de données réelle
        record_student_interaction(
            student_id=req.student_id,
            student_class=norm_class,
            subject=req.subject,
            question=req.question,
            answer=full_text,
            sources=formatted_sources,
            session_id=session_id,
        )

        # Événement de fin avec métadonnées et sources RAG
        final_payload = json.dumps({
            "chunk": "",
            "done": True,
            "full_text": full_text,
            "student_class": norm_class,
            "sources": formatted_sources,
        }, ensure_ascii=False)
        yield f"data: {final_payload}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/api/curriculum")
def get_curriculum():
    """Retourne la structure des classes et matières du programme malien indexé."""
    return {
        "country": "Mali",
        "classes": [
            {
                "id": "10eme",
                "label": "10ème Année",
                "series": ["10ème Commune", "10ème Technique"],
                "subjects": ["mathematiques", "physique", "chimie", "francais", "anglais", "svt"],
            },
            {
                "id": "11eme",
                "label": "11ème Année",
                "series": ["11ème Sciences", "11ème Lettres", "11ème Sciences Économiques", "11ème STI"],
                "subjects": ["mathematiques", "physique", "chimie", "francais", "anglais", "biologie", "geologie", "histoire", "geographie"],
            },
            {
                "id": "12eme",
                "label": "12ème Année (Terminale)",
                "series": ["TSE (Sciences Exactes)", "TSExp (Sciences Expérimentales)", "TSS (Sciences Sociales)", "TSEco (Sciences Économiques)", "TLL (Lettres & Langues)"],
                "subjects": ["mathematiques", "physique", "chimie", "francais", "anglais", "biologie", "geologie", "histoire", "geographie", "philosophie", "economie"],
            },
        ],
        "indexed_chunks_count": state.chunks_count,
        "rag_ready": state.rag_ready,
    }


@router.get("/api/learner/{student_id}")
def get_learner_profile(student_id: str):
    """Retourne le profil d'apprentissage d'un élève."""
    orch = get_orchestrator()
    profile = orch.learner_manager.get_or_create(student_id)
    return {
        "student_id": profile.student_id,
        "student_class": profile.student_class,
        "mastered_topics": profile.mastered_topics,
        "topics_to_review": profile.topics_to_review,
        "total_interactions": len(profile.recent_interactions),
    }


@router.post("/api/learner/{student_id}/interaction")
def record_learner_interaction_endpoint(student_id: str, record: InteractionRecord):
    """Enregistre un résultat de quiz ou d'exercice dans le carnet de l'élève."""
    orch = get_orchestrator()
    interaction = LearningInteraction(
        question="Évaluation d'exercice",
        intent=record.intent,
        subject=record.subject,
        topic=record.topic,
        difficulty=record.difficulty,
        success=record.success,
    )
    orch.learner_manager.register_interaction(student_id, interaction)

    record_student_interaction(
        student_id=student_id,
        subject=record.subject,
        topic=record.topic,
        question=f"Exercice sur {record.topic or record.subject}",
        answer="Résultat d'évaluation enregistré",
        intent=record.intent,
        difficulty=record.difficulty or "moyen",
        success=record.success if record.success is not None else True,
    )
    return {"status": "recorded", "student_id": student_id}


@router.post("/api/session/reset")
def reset_session(req: ResetSessionRequest):
    """Efface l'historique d'une session de conversation."""
    orch = get_orchestrator()
    if orch.conversation_manager.has_session(req.session_id):
        orch.conversation_manager.clear_session(req.session_id)
    return {"status": "cleared", "session_id": req.session_id}
