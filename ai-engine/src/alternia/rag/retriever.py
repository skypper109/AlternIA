from abc import ABC, abstractmethod

from alternia.core.models import (
    KnowledgeChunk,
    StudentQuestion,
)


class Retriever(ABC):

    @abstractmethod
    def add_documents(
        self,
        documents: list[KnowledgeChunk],
    ) -> None:
        pass

    @abstractmethod
    def search(
        self,
        question: StudentQuestion,
        top_k: int = 5,
    ) -> list[KnowledgeChunk]:
        pass
