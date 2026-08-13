from typing import List

from alternia.core.models import KnowledgeChunk


class TextChunker:
    """
    Découpe un contenu pédagogique en morceaux
    utilisables par le système RAG.
    """

    def __init__(self, chunk_size: int = 1000, overlap: int = 150):
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
                    chunk_id=f"{source}-{chunk_number}",
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

            start = end - self.overlap

        return chunks