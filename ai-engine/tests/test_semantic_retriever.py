from alternia.core.models import (
    KnowledgeChunk,
    StudentClass,
    StudentQuestion,
    Subject,
)

from alternia.rag.embeddings import EmbeddingService
from alternia.rag.semantic_retriever import SemanticRetriever
from alternia.rag.vector_store import LocalVectorStore


def test_semantic_retrieval():

    embedding_service = EmbeddingService()

    vector_store = LocalVectorStore()

    retriever = SemanticRetriever(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )

    documents = [

        KnowledgeChunk(
            chunk_id="math-10-001",
            content=(
                "Une équation du premier degré "
                "est une équation dans laquelle "
                "l'inconnue est à la puissance un."
            ),
            student_class=StudentClass.TEN,
            subject=Subject.MATHEMATIQUES,
            chapter="Equations",
            title="Equations du premier degré",
            source="test",
        ),

        KnowledgeChunk(
            chunk_id="physics-10-001",
            content=(
                "La loi d'Ohm relie la tension, "
                "la résistance et l'intensité."
            ),
            student_class=StudentClass.TEN,
            subject=Subject.PHYSIQUE,
            chapter="Electricité",
            title="Loi d'Ohm",
            source="test",
        ),

        KnowledgeChunk(
            chunk_id="math-11-001",
            content=(
                "Les équations du second degré "
                "utilisent notamment le discriminant."
            ),
            student_class=StudentClass.ELEVEN,
            subject=Subject.MATHEMATIQUES,
            chapter="Equations",
            title="Second degré",
            source="test",
        ),
    ]

    retriever.add_documents(documents)

    question = StudentQuestion(
        student_id="student_001",
        student_class=StudentClass.TEN,
        subject=Subject.MATHEMATIQUES,
        question="Comment résoudre une équation ?",
    )

    results = retriever.search(
        question,
        top_k=3,
    )

    assert len(results) > 0

    for document, score in results:

        assert document.student_class == StudentClass.TEN

        assert document.subject == Subject.MATHEMATIQUES

        assert -1.0 <= score <= 1.0

def test_retriever_does_not_mix_classes():

    embedding_service = EmbeddingService()

    vector_store = LocalVectorStore()

    retriever = SemanticRetriever(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )

    documents = [

        KnowledgeChunk(
            chunk_id="10-equation",
            content=(
                "Pour résoudre une équation du premier degré, "
                "on isole l'inconnue."
            ),
            student_class=StudentClass.TEN,
            subject=Subject.MATHEMATIQUES,
            chapter="Equations",
            title="Premier degré",
            source="programme-10eme",
        ),

        KnowledgeChunk(
            chunk_id="11-equation",
            content=(
                "Une équation du second degré "
                "peut être résolue avec le discriminant."
            ),
            student_class=StudentClass.ELEVEN,
            subject=Subject.MATHEMATIQUES,
            chapter="Equations",
            title="Second degré",
            source="programme-11eme",
        ),
    ]

    retriever.add_documents(documents)

    question = StudentQuestion(
        student_id="student_001",
        student_class=StudentClass.TEN,
        subject=Subject.MATHEMATIQUES,
        question="Comment résoudre une équation ?",
    )

    results = retriever.search(
        question,
        top_k=5,
    )

    assert len(results) == 1

    document, score = results[0]

    assert document.student_class == StudentClass.TEN

    assert document.source == "programme-10eme"