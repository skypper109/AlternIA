from alternia.ingestion.chunking.pedagogical_chunker import (
    PedagogicalChunker,
)

from alternia.ingestion.metadata.structure import (
    PedagogicalMetadata,
)

from alternia.ingestion.metadata.structured_page import (
    StructuredPage,
)


def test_pedagogical_chunker():

    metadata = PedagogicalMetadata(
        student_class="10eme",
        subject="mathematiques",
        chapter="algebre",
        lesson="equations",
        section="definition",
    )

    pages = [
        StructuredPage(
            page_number=1,
            content="Une équation est une égalité.",
            metadata=metadata,
        ),
        StructuredPage(
            page_number=2,
            content="Elle contient une inconnue.",
            metadata=metadata,
        ),
    ]

    chunker = PedagogicalChunker(
        max_characters=1800,
    )

    chunks = chunker.chunk(
        pages=pages,
        source_document="maths_10eme.pdf",
    )

    assert len(chunks) == 1

    chunk = chunks[0]

    assert (
        chunk.metadata.student_class
        == "10eme"
    )

    assert (
        chunk.metadata.subject
        == "mathematiques"
    )

    assert (
        chunk.metadata.chapter
        == "algebre"
    )

    assert (
        chunk.metadata.lesson
        == "equations"
    )

    assert (
        chunk.metadata.section
        == "definition"
    )

    assert chunk.page_start == 1

    assert chunk.page_end == 2

    assert (
        "Une équation est une égalité."
        in chunk.content
    )

    assert (
        "Elle contient une inconnue."
        in chunk.content
    )

def test_chunker_separates_pedagogical_context():

    metadata_1 = PedagogicalMetadata(
        student_class="10eme",
        subject="mathematiques",
        chapter="algebre",
        lesson="equations",
        section="definition",
    )

    metadata_2 = PedagogicalMetadata(
        student_class="10eme",
        subject="mathematiques",
        chapter="geometrie",
        lesson="triangles",
        section="definition",
    )

    pages = [
        StructuredPage(
            page_number=1,
            content="Définition d'une équation.",
            metadata=metadata_1,
        ),
        StructuredPage(
            page_number=2,
            content="Définition d'un triangle.",
            metadata=metadata_2,
        ),
    ]

    chunker = PedagogicalChunker()

    chunks = chunker.chunk(
        pages=pages,
        source_document="maths_10eme.pdf",
    )

    assert len(chunks) == 2

    assert (
        chunks[0].metadata.chapter
        == "algebre"
    )

    assert (
        chunks[1].metadata.chapter
        == "geometrie"
    )