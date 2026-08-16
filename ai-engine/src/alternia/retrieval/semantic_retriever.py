from alternia.embeddings.service import EmbeddingService
from alternia.retrieval.qdrant_store import QdrantVectorStore


class SemanticRetriever:
    """
    Effectue la recherche sémantique dans la base
    de connaissances pédagogique d'AlternIA.

    Pipeline :

        Question
           ↓
        Embedding
           ↓
        Qdrant
           ↓
        Filtres pédagogiques
           ↓
        Top-K résultats
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: QdrantVectorStore,
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def retrieve(
        self,
        query: str,
        student_class: str,
        subject: str | None = None,
        top_k: int = 5,
    ):
        if not query or not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        if not student_class:
            raise ValueError(
                "Student class is required."
            )

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero."
            )

        query_embedding = (
            self.embedding_service.encode(
                query
            )
        )

        return self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            student_class=student_class,
            subject=subject,
        )

    search = retrieve