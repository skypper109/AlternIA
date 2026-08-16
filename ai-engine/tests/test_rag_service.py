from alternia.core.models import (
    KnowledgeChunk,
    StudentClass,
    Subject,
)

from alternia.rag.embeddings import EmbeddingService
from alternia.rag.semantic_retriever import SemanticRetriever
from alternia.rag.vector_store import LocalVectorStore
from alternia.rag.service import RAGService


def test_rag_service_builds_context():

    embedding_service = EmbeddingService()

    vector_store = LocalVectorStore()

    retriever = SemanticRetriever(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )

    document = KnowledgeChunk(
        chunk_id="math-10-equation",
        content=(
            "Une équation du premier degré "
            "est une égalité contenant une inconnue."
        ),
        student_class=StudentClass.TEN,
        subject=Subject.MATHEMATIQUES,
        chapter="Algèbre",
        title="Équations du premier degré",
        source="programme-10eme",
    )

    retriever.add_documents(
        [document]
    )

    rag = RAGService(
        retriever=retriever,
        top_k=3,
    )

    context = rag.retrieve(
        question="Qu'est-ce qu'une équation ?",
        student_class="10eme",
        subject="mathematiques",
    )

    assert context.query == (
        "Qu'est-ce qu'une équation ?"
    )

    assert context.student_class == "10eme"

    assert context.subject == "mathematiques"

    assert len(context.sources) == 1

    assert (
        "équation"
        in context.context_text.lower()
    )