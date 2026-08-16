import json
from pathlib import Path

from alternia.core.models import KnowledgeChunk
from alternia.rag.embeddings import EmbeddingService
from alternia.rag.vector_store import LocalVectorStore


class LocalRAGIndex:
    """
    Index RAG local d'AlternIA.

    Architecture :

        KnowledgeChunk
              ↓
        EmbeddingService
              ↓
        LocalVectorStore
              ↓
        recherche sémantique

    L'index est sauvegardé localement afin d'éviter
    de recalculer les embeddings à chaque démarrage.
    """

    def __init__(
        self,
        index_path: str | Path,
        embedding_service: EmbeddingService,
    ):
        self.index_path = Path(index_path)
        self.embedding_service = embedding_service
        self.vector_store = LocalVectorStore()

    def add_documents(
        self,
        documents: list[KnowledgeChunk],
    ) -> None:

        if not documents:
            return

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

    def save(self) -> None:

        self.index_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        records = []

        for record in self.vector_store.records:

            records.append(
                {
                    "document": record.document.model_dump(
                        mode="json"
                    ),
                    "vector": record.vector,
                }
            )

        with self.index_path.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                records,
                file,
                ensure_ascii=False,
            )

    def load(self) -> None:

        if not self.index_path.exists():
            return

        with self.index_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            records = json.load(file)

        self.vector_store.records.clear()

        for record in records:

            document = KnowledgeChunk.model_validate(
                record["document"]
            )

            self.vector_store.add(
                document=document,
                vector=record["vector"],
            )

    @property
    def size(self) -> int:

        return len(
            self.vector_store.records
        )