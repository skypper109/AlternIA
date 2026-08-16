import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, AsyncIterator, Optional

os.environ["TOKENIZERS_PARALLELISM"] = "false"

# pyrefly: ignore [missing-import]
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Ajout du chemin ai-engine/src au PYTHONPATH si nécessaire
ROOT_DIR = Path(__file__).resolve().parents[2]
AI_ENGINE_SRC = ROOT_DIR / "ai-engine" / "src"
if str(AI_ENGINE_SRC) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_SRC))

from alternia.config.settings import PROJECT_ROOT, settings
from alternia.core.models import StudentClass, Subject
from alternia.llm.local_client import LocalLLMClient
from alternia.orchestration.orchestrator import AlterniaOrchestrator
from alternia.pedagogical.engine import PedagogicalEngine
from alternia.rag.embeddings import EmbeddingService
from alternia.rag.semantic_retriever import SemanticRetriever
from alternia.rag.vector_store import LocalVectorStore
from alternia.rag.service import RAGService
from alternia.learner.manager import LearnerManager
from alternia.learner.models import LearningInteraction
from alternia.conversation.manager import ConversationManager
from alternia.tts.engine import TTSEngine


# ==============================================================================
# SCHÉMAS PYDANTIC
# ==============================================================================

class ChatMessagePayload(BaseModel):
    role: str = "user"
    text: str


class ChatRequest(BaseModel):
    question: str
    student_class: str = "12eme"
    subject: Optional[str] = None
    student_id: str = "eleve_mobile"
    student_name: Optional[str] = "Élève"
    session_id: Optional[str] = None
    enable_rag: bool = True
    history: Optional[list[ChatMessagePayload]] = None


class ChatSource(BaseModel):
    chunk_id: Optional[str] = None
    document: str
    chapter: Optional[str] = None
    lesson: Optional[str] = None
    score: float = 0.0
    content_preview: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    intent: str
    student_class: str
    subject: Optional[str] = None
    sources: list[ChatSource] = Field(default_factory=list)
    should_ask_followup: bool = False
    followup_question: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class InteractionRecord(BaseModel):
    intent: str
    subject: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    success: Optional[bool] = None


class ResetSessionRequest(BaseModel):
    session_id: str


# ==============================================================================
# GESTIONNAIRE D'ÉTAT SINGLETON
# ==============================================================================

class AppState:
    orchestrator: Optional[AlterniaOrchestrator] = None
    vector_store: Optional[LocalVectorStore] = None
    learner_manager: Optional[LearnerManager] = None
    conversation_manager: Optional[ConversationManager] = None
    rag_ready: bool = False
    chunks_count: int = 0


state = AppState()


def get_orchestrator() -> AlterniaOrchestrator:
    """Initialise de façon paresseuse l'orchestrateur avec le modèle GGUF et la base RAG."""
    if state.orchestrator is not None:
        return state.orchestrator

    model_1_5b = PROJECT_ROOT / "ai-engine" / "models" / "llm" / "qwen2.5-1.5b-instruct-q4_k_m.gguf"
    model_3b = PROJECT_ROOT / "ai-engine" / "models" / "llm" / "qwen2.5-3b-instruct-q4_k_m.gguf"
    model_path = model_1_5b if model_1_5b.exists() else model_3b

    llm_client = LocalLLMClient(
        model_path=str(model_path),
        n_ctx=4096,
        n_batch=512,
        # Pas de max_tokens : le modèle s'arrête naturellement sur <|im_end|>
    )

    embedding_service = EmbeddingService()
    vector_store = LocalVectorStore()
    loaded = vector_store.load()

    state.vector_store = vector_store
    state.chunks_count = vector_store.count if loaded else 0
    state.rag_ready = loaded

    retriever = SemanticRetriever(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )

    rag_service = RAGService(
        retriever=retriever,
        top_k=2,
    )

    pedagogical_engine = PedagogicalEngine()
    learner_manager = LearnerManager()
    conversation_manager = ConversationManager()

    state.learner_manager = learner_manager
    state.conversation_manager = conversation_manager

    state.orchestrator = AlterniaOrchestrator(
        pedagogical_engine=pedagogical_engine,
        llm_client=llm_client,
        rag_service=rag_service,
        learner_manager=learner_manager,
        conversation_manager=conversation_manager,
    )

    return state.orchestrator


def normalize_student_class(class_id: str) -> str:
    """Mappe les identifiants de classe malienne vers les valeurs supportées ('10eme', '11eme', '12eme')."""
    cid = class_id.strip().lower()
    if cid in {"10eme", "10e", "10", "10eme-cg", "10eme-ct"}:
        return "10eme"
    if cid in {"11eme", "11e", "11", "11eme-sc", "11eme-ll", "11eme-se", "11eme-sti"}:
        return "11eme"
    if cid in {"12eme", "12e", "12", "tse", "tsexp", "tss", "tll", "tseco", "terminale"}:
        return "12eme"
    return "12eme"


# ==============================================================================
# CRÉATION DE L'APPLICATION FASTAPI
# ==============================================================================

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Précharge les moteurs au démarrage."""
    try:
        get_orchestrator()
    except Exception as e:
        print(f"[Startup Warning] Le préchargement immédiat a échoué: {e}")
    yield


app = FastAPI(
    title="AlternIA Backend API",
    description="API pédagogique intelligente connectant les dispositifs physiques et l'application mobile AlternIA.",
    version="1.0.0",
    lifespan=lifespan,
)

# Activation CORS totale pour l'application Flutter (iOS, Android, Web, Desktop)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# ==============================================================================
# ROUTES API
# ==============================================================================

@app.get("/")
@app.get("/health")
@app.get("/api/health")
def health():
    orch = get_orchestrator()
    return {
        "status": "healthy",
        "application": "AlternIA",
        "version": "1.0.0",
        "rag_ready": state.rag_ready,
        "rag_chunks_count": state.chunks_count,
        "llm_model": "Qwen 2.5 3B Instruct (GGUF Local)",
        "default_class": settings.default_class,
    }


@app.post("/api/chat", response_model=ChatResponse)
@app.post("/api/ask", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    """Endpoint principal de réponse pédagogique non-streamée."""
    orch = get_orchestrator()
    norm_class = normalize_student_class(req.student_class)
    session_id = req.session_id or f"session_{req.student_id}"

    # Récupération du contexte RAG
    context = None
    if req.enable_rag and orch.rag_service:
        try:
            context = orch.rag_service.retrieve(
                question=req.question,
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


@app.post("/api/chat/stream")
@app.post("/api/ask/stream")
async def chat_stream_endpoint(req: ChatRequest):
    """Endpoint de streaming Server-Sent Events (SSE) token par token."""
    orch = get_orchestrator()
    norm_class = normalize_student_class(req.student_class)
    session_id = req.session_id or f"session_{req.student_id}"

    # Contexte RAG
    context = None
    if req.enable_rag and orch.rag_service:
        try:
            context = orch.rag_service.retrieve(
                question=req.question,
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


@app.get("/api/curriculum")
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


@app.get("/api/learner/{student_id}")
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


@app.post("/api/learner/{student_id}/interaction")
def record_learner_interaction(student_id: str, record: InteractionRecord):
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
    return {"status": "recorded", "student_id": student_id}


@app.post("/api/session/reset")
def reset_session(req: ResetSessionRequest):
    """Efface l'historique d'une session de conversation."""
    orch = get_orchestrator()
    if orch.conversation_manager.has_session(req.session_id):
        orch.conversation_manager.clear_session(req.session_id)
    return {"status": "cleared", "session_id": req.session_id}



class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = "vivienne"


@app.post("/api/tts")
@app.get("/api/tts")
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


@app.get("/api/device/info")
def get_device_info():
    """Retourne des informations sur le dispositif AlternIA local."""
    return {
        "device_id": "alternia-device-01",
        "device_name": "AlternIA Box (Mali)",
        "firmware": "v2.0-LocalEdge",
        "ai_engine": "AlternIA Native Engine",
        "llm_local": True,
        "rag_local": True,
        "indexed_chunks": state.chunks_count,
    }


# ==============================================================================
# MONTAGE DE L'INTERFACE DISPOSITIF TACTILE (KIOSK RASPBERRY PI)
# ==============================================================================

DEVICE_FRONTEND_DIR = ROOT_DIR / "device" / "frontend"
if DEVICE_FRONTEND_DIR.exists():
    app.mount("/app", StaticFiles(directory=str(DEVICE_FRONTEND_DIR), html=True), name="device_app")
    app.mount("/device", StaticFiles(directory=str(DEVICE_FRONTEND_DIR), html=True), name="device_kiosk")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.backend_host, port=settings.backend_port)
