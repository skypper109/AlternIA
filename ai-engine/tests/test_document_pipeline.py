from alternia.document.chunker import DocumentChunker
from alternia.document.cleaner import DocumentCleaner


def test_cleaner():

    cleaner = DocumentCleaner()

    text = """
    Bonjour     monde.


    Ceci est un cours.
    """

    result = cleaner.clean(text)

    assert "Bonjour monde." in result
    assert "Ceci est un cours." in result


def test_chunker():

    chunker = DocumentChunker(
        max_characters=100,
        overlap=10,
    )

    text = (
        "Premier paragraphe.\n\n"
        "Deuxième paragraphe.\n\n"
        "Troisième paragraphe."
    )

    chunks = chunker.chunk(
        text,
        document_id="test",
    )

    assert len(chunks) > 0

    assert chunks[0].chunk_id == "test-0000"
