from typing import List

from alternia.core.models import KnowledgeChunk


class TextChunker:
    """
    Découpe un contenu pédagogique en morceaux
    utilisables par le système RAG.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        overlap: int = 150,
    ):
        if chunk_size <= 0:
            raise ValueError(
                "chunk_size doit être supérieur à 0."
            )

        if overlap < 0:
            raise ValueError(
                "overlap ne peut pas être négatif."
            )

        if overlap >= chunk_size:
            raise ValueError(
                "overlap doit être inférieur à chunk_size."
            )

        self.chunk_size = chunk_size
        self.overlap = overlap

    def split(
        self,
        content: str,
        *,
        student_class,
        subject,
        chapter: str,
        title: str,
        source: str,
        source_version: str | None = None,
    ) -> List[KnowledgeChunk]:

        if not content.strip():
            return []

        chunks = []

        start = 0
        chunk_number = 0

        while start < len(content):

            end = start + self.chunk_size

            chunk_content = content[start:end].strip()

            if chunk_content:

                chunk = KnowledgeChunk(
                    chunk_id=(
                        f"{source}-{chunk_number}"
                    ),
                    content=chunk_content,
                    student_class=student_class,
                    subject=subject,
                    chapter=chapter,
                    title=title,
                    source=source,
                    source_version=source_version,
                )

                chunks.append(chunk)

            chunk_number += 1

            next_start = end - self.overlap

            if next_start <= start:
                break

            start = next_start

        return chunks


# Alias de compatibilité.
#
# Certains modules utilisent encore le nom Chunker.
# On conserve donc les deux noms.
Chunker = TextChunker