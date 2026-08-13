from unittest.mock import Mock

from alternia.core.pedagogical_chunk import (
    PedagogicalChunk,
)

from alternia.indexing.knowledge_indexer import (
    KnowledgeIndexer,
)


def make_chunk() -> PedagogicalChunk:

    metadata = Mock()

    metadata.student_class = "10eme"
    metadata.subject = "mathematiques"
    metadata.chapter = "algebre"
    metadata.lesson = "equations"
    metadata.section = "resolution"

    return PedagogicalChunk(
        chunk_id="math-10-equations-001",
        content=(
            "Pour résoudre une équation "
            "du premier degré, on isole "
            "l'inconnue."
        ),
        metadata=metadata,
        source_document="maths_10eme.pdf",
        page_start=10,
        page_end=11,
    )


def test_build_embedding_text():

    embedding_service = Mock()
    vector_store = Mock()

    indexer = KnowledgeIndexer(
        embedding_service,
        vector_store,
    )

    chunk = make_chunk()

    text = indexer._build_embedding_text(
        chunk
    )

    assert "10eme" in text
    assert "mathematiques" in text
    assert "algebre" in text
    assert "equations" in text
    assert "resolution" in text
    assert "isole l'inconnue" in text


def test_index_chunk():

    embedding_service = Mock()

    embedding_service.encode.return_value = [
        0.1,
        0.2,
        0.3,
    ]

    vector_store = Mock()

    indexer = KnowledgeIndexer(
        embedding_service,
        vector_store,
    )

    chunk = make_chunk()

    indexer.index_chunk(chunk)

    embedding_service.encode.assert_called_once()

    vector_store.add.assert_called_once_with(
        chunk,
        [0.1, 0.2, 0.3],
    )


def test_index_chunks():

    embedding_service = Mock()

    embedding_service.encode_many.return_value = [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
    ]

    vector_store = Mock()

    indexer = KnowledgeIndexer(
        embedding_service,
        vector_store,
    )

    chunks = [
        make_chunk(),
        make_chunk(),
    ]

    count = indexer.index_chunks(
        chunks
    )

    assert count == 2

    embedding_service.encode_many.assert_called_once()

    vector_store.add_many.assert_called_once()