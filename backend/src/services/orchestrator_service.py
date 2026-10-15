import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
AI_ENGINE_DIR = ROOT_DIR / "ai-engine" / "src"

for p in (ROOT_DIR, AI_ENGINE_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import os
from typing import Optional

from alternia.config.settings import PROJECT_ROOT, settings
from alternia.conversation.manager import ConversationManager
from alternia.learner.manager import LearnerManager
from alternia.llm.client import LLMClient
from alternia.llm.local_client import LocalLLMClient
from alternia.llm.groq_client import GroqLLMClient, LazyLocalLLMClient
from alternia.llm.gemini_client import GeminiLLMClient
from alternia.orchestration.orchestrator import AlterniaOrchestrator
from alternia.pedagogical.engine import PedagogicalEngine
from alternia.rag.embeddings import EmbeddingService
from alternia.rag.semantic_retriever import SemanticRetriever
from alternia.rag.service import RAGService
from alternia.rag.vector_store import LocalVectorStore, VectorStore


class AppState:
    orchestrator: Optional[AlterniaOrchestrator] = None
    vector_store: Optional[VectorStore] = None
    learner_manager: Optional[LearnerManager] = None
    conversation_manager: Optional[ConversationManager] = None
    rag_ready: bool = False
    chunks_count: int = 0
    model_name: str = "Multi-Cloud (Groq Qwen & Gemini 3 Flash)"


state = AppState()


def get_orchestrator() -> AlterniaOrchestrator:
    """Initialise l'orchestrateur avec le client Groq Cloud / Gemini 3 Flash et fallback local paresseux."""
    if state.orchestrator is not None:
        return state.orchestrator

    # 1. Fallback local paresseux (ne consomme aucune RAM tant que les API cloud fonctionnent)
    model_1_5b = PROJECT_ROOT / "ai-engine" / "models" / "llm" / "qwen2.5-1.5b-instruct-q4_k_m.gguf"
    model_3b = PROJECT_ROOT / "ai-engine" / "models" / "llm" / "qwen2.5-3b-instruct-q4_k_m.gguf"
    model_path = model_1_5b if model_1_5b.exists() else model_3b

    local_fallback = None
    if model_path.exists():
        local_fallback = LazyLocalLLMClient(
            model_path=str(model_path),
            n_ctx=4096,
            n_batch=512,
        )

    # 2. Client Gemini Cloud (Gemini 2.5 Flash / Gemini 3.8 Flash - Haute cadence)
    gemini_api_key = (
        getattr(settings, "gemini_api_key", None)
        or os.getenv("GEMINI_API_KEY")
        or "AQ.Ab8RN6JGzagbZCG-VcH1I4tTAUGUmN9bB9nwWLDUsP1xTs0r5w"
    )
    gemini_model = (
        getattr(settings, "gemini_model", None)
        or os.getenv("GEMINI_MODEL")
        or "gemini-3.1-flash-lite"
    )
    gemini_client = GeminiLLMClient(
        api_key=gemini_api_key,
        model=gemini_model,
        fallback_client=local_fallback,
    )

    # 3. Client Groq Cloud (Qwen 3.8 27B / GPT-OSS 120B)
    groq_api_key = (
        getattr(settings, "groq_api_key", None)
        or os.getenv("GROQ_API_KEY")
        or getattr(settings, "llm_api_key", None)
        or os.getenv("LLM_API_KEY")
        or "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"
    )
    groq_model = (
        getattr(settings, "groq_model", None)
        or os.getenv("GROQ_MODEL")
        or getattr(settings, "llm_model", None)
        or os.getenv("LLM_MODEL")
        or "qwen/qwen3.8-27b"
    )
    groq_client = GroqLLMClient(
        api_key=groq_api_key,
        model=groq_model,
        fallback_client=local_fallback,
    )

    # Chaîne de priorité intelligente :
    # Par défaut -> Gemini 2.5 Flash en premier (haute vitesse, pas de blocage), avec secours Groq Qwen
    # Si LLM_PROVIDER=groq -> Groq Qwen 27B en premier, avec secours Gemini
    provider = (os.getenv("LLM_PROVIDER") or getattr(settings, "llm_provider", "gemini")).lower().strip()
    if provider == "groq":
        groq_client.fallback_client = gemini_client
        gemini_client.fallback_client = local_fallback
        llm_client = groq_client
        state.model_name = f"Groq Cloud [{groq_model}] (Secours: Gemini & Local)"
        print(f"\033[1;32m🚀 [OrchestratorService] LLM Principal : Groq API ({groq_model}) | Secours : Gemini & Local\033[0m")
    else:
        gemini_client.fallback_client = groq_client
        groq_client.fallback_client = local_fallback
        llm_client = gemini_client
        state.model_name = f"Gemini Cloud [{gemini_model}] (Secours: Groq & Local)"
        print(f"\033[1;36m✨ [OrchestratorService] LLM Principal : Gemini Flash ({gemini_model}) | Secours : Groq & Local\033[0m")

    embedding_service = EmbeddingService()
    from alternia.rag.vector_store import get_vector_store
    vector_store = get_vector_store()
    loaded = vector_store.load()
    if not loaded:
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
    """Mappe les identifiants de classe malienne vers les valeurs supportées ('def', '10eme', '11eme', '12eme', 'culture')."""
    cid = class_id.strip().lower()
    if cid in {"culture", "culturelens", "patrimoine"}:
        return "culture"
    if cid in {"def", "9eme", "9e", "9", "fondamental", "troisieme", "3eme", "9eme-annee", "6eme", "6e", "7eme", "7e", "8eme", "8e"}:
        return "def"
    if cid in {"10eme", "10e", "10", "10eme-cg", "10eme-ct", "seconde"}:
        return "10eme"
    if cid in {"11eme", "11e", "11", "11eme-sc", "11eme-ll", "11eme-se", "11eme-sti", "premiere"}:
        return "11eme"
    if cid in {"12eme", "12e", "12", "tse", "tsexp", "tss", "tll", "tseco", "terminale", "bac", "terminale_sciences_sociales", "terminale_sciences_sociale", "sciences_sociales"}:
        return "12eme"
    return "12eme"


def get_llm_client() -> LLMClient:
    """Récupère l'instance unique du client LLM (chargée via get_orchestrator)."""
    orch = get_orchestrator()
    return orch.llm_client

