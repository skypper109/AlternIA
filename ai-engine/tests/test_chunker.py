from alternia.core.models import StudentClass, Subject
from alternia.rag.chunker import TextChunker


def test_chunker():

    text = """
    Une équation du premier degré est une équation
    dans laquelle l'inconnue apparaît avec un exposant égal à un.
    Pour résoudre une équation, on cherche la valeur de l'inconnue.
    """

    chunker = TextChunker(
        chunk_size=100,
        overlap=20,
    )

    chunks = chunker.split(
        text,
        student_class=StudentClass.TEN,
        subject=Subject.MATHEMATIQUES,
        chapter="Equations",
        title="Equations du premier degré",
        source="programme_mali_10eme",
    )

    assert len(chunks) > 0
    assert chunks[0].student_class == StudentClass.TEN
    assert chunks[0].subject == Subject.MATHEMATIQUES