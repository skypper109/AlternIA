from alternia.core.models import (
    KnowledgeChunk,
    StudentQuestion,
)

from alternia.rag.retriever import Retriever


class LocalRetriever(Retriever):

    def __init__(self):
        self.documents: list[KnowledgeChunk] = []

    def add_documents(
        self,
        documents: list[KnowledgeChunk],
    ) -> None:

        self.documents.extend(documents)

    def search(
        self,
        question: StudentQuestion,
        top_k: int = 5,
    ) -> list[KnowledgeChunk]:

        candidates = [
            document
            for document in self.documents
            if document.student_class == question.student_class
        ]

        if question.subject:
            candidates = [
                document
                for document in candidates
                if document.subject == question.subject
            ]

        return candidates[:top_k]