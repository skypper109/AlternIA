"""
Routes API pour le chat pédagogique, streaming SSE, curriculum et profil apprenant.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import AsyncIterator
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from alternia.learner.manager import LearningInteraction
from alternia.rag.contextualizer import QueryContextualizer
from alternia.pedagogical.curriculum_keywords import detect_malian_curriculum_subject
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


def _make_no_context_response(
    subject: str | None,
    student_class: str,
) -> ChatResponse:
    """
    Réponse de refus structurée quand le RAG ne trouve aucun contenu
    pertinent pour la question posée. Évite tout appel au LLM.
    """
    subject_label = subject or "la matière sélectionnée"
    answer = (
        f"Je n'ai pas trouvé d'information sur ce sujet dans le programme officiel "
        f"de {student_class} pour {subject_label}. "
        f"Pose-moi une question sur {subject_label} conforme au programme de ta classe "
        f"pour que je puisse t'aider."
    )
    return ChatResponse(
        answer=answer,
        intent="out_of_scope",
        student_class=student_class,
        subject=subject,
        sources=[],
        should_ask_followup=False,
        followup_question=None,
        metadata={"rag_sources": 0, "out_of_scope": True},
    )


@router.post("/api/chat", response_model=ChatResponse)
@router.post("/api/ask", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    """Endpoint principal de réponse pédagogique non-streamée."""
    t0_req = time.perf_counter()
    orch = get_orchestrator()
    norm_class = normalize_student_class(req.student_class)
    session_id = req.session_id or f"session_{req.student_id}"

    print(f"\n\033[36m⏱️  [chat_routes.py]\033[0m Requête API reçue : \"{req.question}\" (Classe: {norm_class}, Élève: {req.student_id})")

    # Détection automatique de matière selon le programme malien si mode général
    effective_subject = req.subject
    if effective_subject in {None, "", "général", "general", "toutes", "tous"}:
        effective_subject = detect_malian_curriculum_subject(req.question)

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
                subject=effective_subject,
                student_id=req.student_id,
            )
        except Exception:
            context = None

    # Filtrage des sources RAG non pertinentes
    if context and hasattr(context, "sources"):
        sources_list = getattr(context, "sources", [])
        _max_score = max((getattr(s, "score", 0.0) for s in sources_list), default=0.0)
        if len(sources_list) == 0 or _max_score < 0.35:
            context = None

    # Exécution du pipeline
    result = orch.ask(
        question=req.question,
        context=context,
        student_class=norm_class,
        subject=effective_subject,
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

    dt_total = time.perf_counter() - t0_req
    print(f"\033[36m⏱️  [chat_routes.py]\033[0m Réponse API synchrone générée en \033[1;32m{dt_total:.2f}s\033[0m\n")

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
    t0_req = time.perf_counter()
    orch = get_orchestrator()
    norm_class = normalize_student_class(req.student_class)
    session_id = req.session_id or f"session_{req.student_id}"

    print(f"\n\033[36m⏱️  [chat_routes.py]\033[0m Requête SSE reçue : \"{req.question}\" (Classe: {norm_class}, Élève: {req.student_id})")

    # Détection automatique de matière selon le programme malien si mode général
    effective_subject = req.subject
    if effective_subject in {None, "", "général", "general", "toutes", "tous"}:
        effective_subject = detect_malian_curriculum_subject(req.question)

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
                subject=effective_subject,
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

    # Filtrage des sources RAG non pertinentes
    if context and hasattr(context, "sources"):
        sources_list = getattr(context, "sources", [])
        _max_score = max((getattr(s, "score", 0.0) for s in sources_list), default=0.0)
        if len(sources_list) == 0 or _max_score < 0.35:
            context = None
            formatted_sources = []

    generator = orch.ask_stream(
        question=req.question,
        context=context,
        student_class=norm_class,
        subject=effective_subject,
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

        dt_total = time.perf_counter() - t0_req
        print(f"\033[36m⏱️  [chat_routes.py]\033[0m Stream SSE terminé en \033[1;32m{dt_total:.2f}s\033[0m ({len(full_text)} caractères)\n")

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
