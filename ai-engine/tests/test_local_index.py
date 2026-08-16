from pathlib import Path

from alternia.core.models import (
    KnowledgeChunk,
    StudentClass,
    Subject,
)

from alternia.rag.embeddings import EmbeddingService
from alternia.rag.local_index import LocalRAGIndex


def make_document():

    return KnowledgeChunk(
        chunk_id="math-10-001",
        content=(
            "Une équation du premier degré "
            "est une égalité contenant une inconnue."
        ),
        student_class=StudentClass.TEN,
        subject=Subject.MATHEMATIQUES,
        chapter="Equations",
        title="Équations du premier degré",
        source="test",
    )


def test_local_index_save_and_load(
    tmp_path: Path,
):

    embedding_service = EmbeddingService()

    index_path = (
        tmp_path
        / "alternia-index.json"
    )

    index = LocalRAGIndex(
        index_path=index_path,
        embedding_service=embedding_service,
    )

    index.add_documents(
        [make_document()]
    )

    assert index.size == 1

    index.save()

    assert index_path.exists()

    restored = LocalRAGIndex(
        index_path=index_path,
        embedding_service=embedding_service,
    )

    restored.load()

    assert restored.size == 1

    document = (
        restored.vector_store.records[0].document
    )

    assert document.chunk_id == "math-10-001"

    assert (
        document.student_class
        == StudentClass.TEN
    )

    assert (
        document.subject
        == Subject.MATHEMATIQUES
    )