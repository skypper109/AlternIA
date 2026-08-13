from alternia.core.models import (
    KnowledgeChunk,
    StudentQuestion,
)

from alternia.rag.embeddings import EmbeddingService
from alternia.rag.vector_store import LocalVectorStore


class SemanticRetriever:

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: LocalVectorStore,
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def add_documents(
        self,
        documents: list[KnowledgeChunk],
    ) -> None:

        texts = [
            document.content
            for document in documents
        ]

        vectors = self.embedding_service.encode_many(
            texts
        )

        self.vector_store.add_many(
            documents,
            vectors,
        )

    def search(
        self,
        question: StudentQuestion,
        top_k: int = 5,
    ) -> list[tuple[KnowledgeChunk, float]]:

        query_vector = self.embedding_service.encode(
            question.question
        )

        return self.vector_store.search(
            query_vector=query_vector,
            top_k=top_k,
            student_class=question.student_class,
            subject=question.subject,
        )