import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
AI_ENGINE_DIR = ROOT_DIR / "ai-engine" / "src"

for p in (ROOT_DIR, AI_ENGINE_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from typing import Optional

from alternia.config.settings import PROJECT_ROOT, settings
from alternia.conversation.manager import ConversationManager
from alternia.learner.manager import LearnerManager
from alternia.llm.client import LLMClient
from alternia.llm.local_client import LocalLLMClient
from alternia.orchestration.orchestrator import AlterniaOrchestrator
from alternia.pedagogical.engine import PedagogicalEngine
from alternia.rag.embeddings import EmbeddingService
from alternia.rag.semantic_retriever import SemanticRetriever
from alternia.rag.service import RAGService
from alternia.rag.vector_store import LocalVectorStore


class AppState:
    orchestrator: Optional[AlterniaOrchestrator] = None
    vector_store: Optional[LocalVectorStore] = None
    learner_manager: Optional[LearnerManager] = None
    conversation_manager: Optional[ConversationManager] = None
    rag_ready: bool = False
    chunks_count: int = 0
    model_name: str = "qwen2.5-1.5b-instruct-q4_k_m.gguf"


state = AppState()


def get_orchestrator() -> AlterniaOrchestrator:
    """Initialise de façon paresseuse l'orchestrateur avec le modèle GGUF et la base RAG."""
    if state.orchestrator is not None:
        return state.orchestrator

    # Priorité absolue au modèle 1.5B en local pour être léger, rapide et fluide sur la machine
    model_1_5b = PROJECT_ROOT / "ai-engine" / "models" / "llm" / "qwen2.5-1.5b-instruct-q4_k_m.gguf"
    model_3b = PROJECT_ROOT / "ai-engine" / "models" / "llm" / "qwen2.5-3b-instruct-q4_k_m.gguf"
    model_path = model_1_5b if model_1_5b.exists() else model_3b

    state.model_name = model_path.name
    print(f"\033[32m[OrchestratorService] Chargement du modèle LLM local : {state.model_name}\033[0m")

    llm_client = LocalLLMClient(
        model_path=str(model_path),
        n_ctx=4096,
        n_batch=512,
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
    """Mappe les identifiants de classe malienne vers les valeurs supportées ('def', '10eme', '11eme', '12eme', 'culture')."""
    cid = class_id.strip().lower()
    if cid in {"culture", "culturelens", "patrimoine"}:
        return "culture"
    if cid in {"def", "9eme", "9e", "9", "fondamental", "troisieme", "3eme", "9eme-annee"}:
        return "def"
    if cid in {"10eme", "10e", "10", "10eme-cg", "10eme-ct", "seconde"}:
        return "10eme"
    if cid in {"11eme", "11e", "11", "11eme-sc", "11eme-ll", "11eme-se", "11eme-sti", "premiere"}:
        return "11eme"
    if cid in {"tss", "terminale_sciences_sociales", "terminale_sciences_sociale", "sciences_sociales"}:
        return "tss"
    if cid in {"12eme", "12e", "12", "tse", "tsexp", "tll", "tseco", "terminale", "bac"}:
        return "12eme"
    return "12eme"


def get_llm_client() -> LLMClient:
    """Récupère l'instance unique du client LLM (chargée via get_orchestrator)."""
    orch = get_orchestrator()
    return orch.llm_client

