from alternia.core.pedagogical_chunk import PedagogicalChunk
from alternia.embeddings.service import EmbeddingService
from alternia.retrieval.qdrant_store import QdrantVectorStore


class KnowledgeIndexer:
    """
    Orchestre l'indexation des contenus pédagogiques
    dans la base vectorielle d'AlternIA.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: QdrantVectorStore,
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    @staticmethod
    def _build_embedding_text(
        chunk: PedagogicalChunk,
    ) -> str:

        metadata = chunk.metadata

        parts = [
            f"Classe : {metadata.student_class}",
            f"Matière : {metadata.subject}",
            f"Chapitre : {metadata.chapter}",
            f"Leçon : {metadata.lesson}",
            f"Section : {metadata.section}",
            "",
            "Contenu :",
            chunk.content,
        ]

        return "\n".join(parts)

    def index_chunk(
        self,
        chunk: PedagogicalChunk,
    ) -> None:

        text = self._build_embedding_text(
            chunk
        )

        embedding = self.embedding_service.encode(
            text
        )

        self.vector_store.add(
            chunk,
            embedding,
        )

    def index_chunks(
        self,
        chunks: list[PedagogicalChunk],
    ) -> int:

        if not chunks:
            return 0

        texts = [
            self._build_embedding_text(chunk)
            for chunk in chunks
        ]

        embeddings = (
            self.embedding_service.encode_many(
                texts
            )
        )

        items = list(
            zip(
                chunks,
                embeddings,
            )
        )

        self.vector_store.add_many(
            items
        )

        return len(chunks)