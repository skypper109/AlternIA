from alternia.context.context_builder import ContextBuilder
from alternia.context.models import PedagogicalContext
from alternia.core.models import (
    StudentClass,
    StudentQuestion,
    Subject,
)
from alternia.rag.semantic_retriever import SemanticRetriever


class RAGService:
    """
    Façade du pipeline RAG local d'AlternIA.

    Pipeline :

        question
            ↓
        StudentQuestion
            ↓
        SemanticRetriever
            ↓
        (KnowledgeChunk, score)
            ↓
        ContextBuilder
            ↓
        PedagogicalContext
    """

    def __init__(
        self,
        retriever: SemanticRetriever,
        context_builder: ContextBuilder | None = None,
        top_k: int = 5,
    ):
        self.retriever = retriever

        self.context_builder = (
            context_builder
            or ContextBuilder(
                max_sources=top_k
            )
        )

        self.top_k = top_k

    def retrieve(
        self,
        question: str,
        student_class: str,
        subject: str | None = None,
        student_id: str = "anonymous",
        series: str | None = None,
    ) -> PedagogicalContext:

        if not question.strip():
            raise ValueError(
                "La question ne peut pas être vide."
            )

        if not student_class:
            raise ValueError(
                "La classe de l'élève est obligatoire."
            )

        student_question = StudentQuestion(
            student_id=student_id,
            student_class=StudentClass(
                student_class
            ),
            series=series,
            question=question.strip(),
            subject=Subject.from_str(subject),
        )

        # -----------------------------------------------------
        # Recherche sémantique
        # -----------------------------------------------------

        retrieval_results = self.retriever.search(
            question=student_question,
            top_k=self.top_k,
        )

        # -----------------------------------------------------
        # Adaptation vers ContextBuilder
        #
        # SemanticRetriever retourne :
        #
        #     (KnowledgeChunk, score)
        #
        # ContextBuilder attend :
        #
        #     result.payload
        #     result.score
        # -----------------------------------------------------

        context_results = []

        for item in retrieval_results:

            if not isinstance(item, tuple):
                continue

            if len(item) != 2:
                continue

            document, score = item

            context_results.append(
                _RetrievalResult(
                    payload={
                        "chunk_id": document.chunk_id,
                        "content": document.content,
                        "student_class": (
                            document.student_class.value
                        ),
                        "subject": (
                            document.subject.value
                        ),
                        "chapter": document.chapter,
                        "lesson": document.title,
                        "source_document": document.source,
                        "page_start": document.page_start,
                        "page_end": document.page_end,
                    },
                    score=float(score),
                )
            )

        # -----------------------------------------------------
        # Construction du contexte pédagogique
        # -----------------------------------------------------

        return self.context_builder.build(
            query=question.strip(),
            results=context_results,
            student_class=student_class,
            subject=subject,
        )


class _RetrievalResult:
    """
    Adaptateur interne entre le SemanticRetriever
    et le ContextBuilder.
    """

    def __init__(
        self,
        payload: dict,
        score: float,
    ):
        self.payload = payload
        self.score = score