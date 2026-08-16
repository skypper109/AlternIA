from pathlib import Path

from alternia.core.models import (
    KnowledgeChunk,
    StudentClass,
    Subject,
)

from alternia.core.pedagogical_chunk import (
    PedagogicalChunk,
)

from alternia.rag.embeddings import (
    EmbeddingService,
)

from alternia.rag.semantic_retriever import (
    SemanticRetriever,
)

from alternia.rag.vector_store import (
    LocalVectorStore,
)


class KnowledgeIndexer:
    """
    Indexeur principal d'AlternIA.

    Le découpage pédagogique est effectué en amont.

    Pipeline :

        PDF
          ↓
        DocumentStructureParser
          ↓
        PedagogicalChunker
          ↓
        PedagogicalChunk
          ↓
        KnowledgeIndexer
          ↓
        KnowledgeChunk
          ↓
        EmbeddingService
          ↓
        LocalVectorStore
    """

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        vector_store: LocalVectorStore | None = None,
    ):

        self.embedding_service = (
            embedding_service
            or EmbeddingService()
        )

        self.vector_store = (
            vector_store
            or LocalVectorStore()
        )

        self.retriever = SemanticRetriever(
            embedding_service=self.embedding_service,
            vector_store=self.vector_store,
        )

    # =========================================================
    # INDEXATION
    # =========================================================

    def add_pedagogical_chunks(
        self,
        chunks: list[PedagogicalChunk],
    ) -> list[KnowledgeChunk]:
        """
        Transforme les PedagogicalChunk en KnowledgeChunk,
        génère leurs embeddings et les ajoute au vector store.
        """

        if not chunks:
            return []

        documents = [
            self._to_knowledge_chunk(chunk)
            for chunk in chunks
        ]

        self.retriever.add_documents(
            documents
        )

        return documents

    # Alias pour compatibilité
    index_chunks = add_pedagogical_chunks

    @staticmethod
    def _to_knowledge_chunk(
        chunk: PedagogicalChunk,
    ) -> KnowledgeChunk:

        metadata = chunk.metadata

        if metadata.student_class is None:

            raise ValueError(
                "Classe absente du chunk : "
                f"{chunk.chunk_id}"
            )

        if metadata.subject is None:

            raise ValueError(
                "Matière absente du chunk : "
                f"{chunk.chunk_id}"
            )

        return KnowledgeChunk(
            chunk_id=chunk.chunk_id,

            content=chunk.content,

            student_class=StudentClass(
                metadata.student_class
            ),

            series=getattr(metadata, "series", None),

            subject=Subject(
                metadata.subject
            ),

            chapter=(
                metadata.chapter
                or "Non défini"
            ),

            lesson=metadata.lesson,

            section=metadata.section,

            title=chunk.title or metadata.lesson or metadata.chapter or "Sans titre",

            source=chunk.source_document,

            source_version=(
                getattr(
                    chunk,
                    "source_version",
                    None,
                )
            ),

            page_start=chunk.page_start,

            page_end=chunk.page_end,
        )


    # =========================================================
    # RECHERCHE
    # =========================================================

    def search(
        self,
        question,
        top_k: int = 5,
    ):

        return self.retriever.search(
            question,
            top_k=top_k,
        )

    # =========================================================
    # PERSISTANCE
    # =========================================================

    def save(self) -> None:

        self.vector_store.save()

    def load(self) -> bool:

        return self.vector_store.load()

    # =========================================================
    # INFORMATIONS
    # =========================================================

    @property
    def document_count(self) -> int:

        return self.vector_store.count

    # =========================================================
    # MAINTENANCE
    # =========================================================

    def clear(self) -> None:

        self.vector_store.clear()

    def remove_source(
        self,
        source: str | Path,
    ) -> int:
        """
        Supprime tous les chunks provenant
        d'un document donné.
        """

        return self.vector_store.remove_by_source(
            source
        )

    def has_source(
        self,
        source: str | Path,
    ) -> bool:
        """
        Vérifie si le document possède déjà
        des chunks dans l'index.
        """

        return self.vector_store.has_source(
            source
        )

    # =========================================================
    # ANCIEN PIPELINE
    # =========================================================

    def index_text(
        self,
        content: str,
        *,
        student_class: StudentClass,
        subject: Subject,
        chapter: str,
        title: str,
        source: str,
        source_version: str | None = None,
    ) -> list[KnowledgeChunk]:

        raise RuntimeError(
            "index_text() appartient à l'ancien pipeline. "
            "Utilisez maintenant le pipeline pédagogique "
            "avec PedagogicalChunker et "
            "add_pedagogical_chunks()."
        )

    def index_file(
        self,
        file_path: str | Path,
        **kwargs,
    ):

        raise RuntimeError(
            "index_file() appartient à l'ancien pipeline. "
            "Utilisez maintenant DocumentStructureParser "
            "et PedagogicalChunker."
        )