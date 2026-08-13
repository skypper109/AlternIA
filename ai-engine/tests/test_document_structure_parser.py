from alternia.ingestion.loaders.base import (
    DocumentPage,
    LoadedDocument,
)

from alternia.ingestion.metadata.document_parser import (
    DocumentStructureParser,
)

from alternia.ingestion.metadata.structure_detector import (
    StructureDetector,
)


def create_document():

    pages = [

        DocumentPage(
            page_number=1,
            content="""
            CLASSE DE 10EME

            MATHEMATIQUES

            CHAPITRE I : ALGEBRE
            """,
        ),

        DocumentPage(
            page_number=2,
            content="""
            LEÇON 1 : EQUATIONS
            """,
        ),

        DocumentPage(
            page_number=3,
            content="""
            1. Définition

            Une équation est une égalité.
            """,
        ),

        DocumentPage(
            page_number=4,
            content="""
            2. Méthode de résolution

            Pour résoudre une équation...
            """,
        ),
    ]

    return LoadedDocument(
        document_id="test-document",
        source_path="test.pdf",
        filename="test.pdf",
        extension=".pdf",
        content="\n".join(
            page.content
            for page in pages
        ),
        pages=pages,
    )


def test_structure_context_propagation():

    document = create_document()

    detector = StructureDetector()

    parser = DocumentStructureParser(
        structure_detector=detector,
    )

    pages = parser.parse(document)

    assert len(pages) == 4

    # Page 1
    assert (
        pages[0].metadata.student_class
        == "10eme"
    )

    assert (
        pages[0].metadata.chapter
        == "algebre"
    )

    # Page 2
    assert (
        pages[1].metadata.student_class
        == "10eme"
    )

    assert (
        pages[1].metadata.chapter
        == "algebre"
    )

    assert (
        pages[1].metadata.lesson
        == "equations"
    )

    # Page 3
    assert (
        pages[2].metadata.chapter
        == "algebre"
    )

    assert (
        pages[2].metadata.lesson
        == "equations"
    )

    # Page 4
    assert (
        pages[3].metadata.chapter
        == "algebre"
    )

    assert (
        pages[3].metadata.lesson
        == "equations"
    )