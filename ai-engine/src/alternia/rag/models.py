from dataclasses import dataclass

from alternia.core.models import KnowledgeChunk


@dataclass
class RetrievalResult:
    """
    Résultat d'une recherche sémantique RAG.

    Contient :
    - le chunk retrouvé ;
    - son score de similarité.
    """

    document: KnowledgeChunk

    score: float

    @property
    def chunk_id(self) -> str:
        return self.document.chunk_id

    @property
    def content(self) -> str:
        return self.document.content

    @property
    def chapter(self) -> str:
        return self.document.chapter

    @property
    def lesson(self) -> str | None:
        return self.document.lesson

    @property
    def section(self) -> str | None:
        return self.document.section

    @property
    def title(self) -> str:
        return self.document.title

    @property
    def source(self) -> str:
        return self.document.source