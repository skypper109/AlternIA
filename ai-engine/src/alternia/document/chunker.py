from dataclasses import dataclass


@dataclass
class DocumentChunk:
    chunk_id: str
    content: str
    chunk_index: int


class DocumentChunker:
    """
    Découpe les programmes scolaires en morceaux
    suffisamment petits pour le RAG et le LLM local.
    """

    def __init__(
        self,
        max_characters: int = 1200,
        overlap: int = 150,
    ):
        self.max_characters = max_characters
        self.overlap = overlap

    def chunk(
        self,
        text: str,
        document_id: str,
    ) -> list[DocumentChunk]:

        if not text.strip():
            return []

        paragraphs = [
            paragraph.strip()
            for paragraph in text.split("\n\n")
            if paragraph.strip()
        ]

        chunks = []

        current = ""

        for paragraph in paragraphs:

            candidate = (
                paragraph
                if not current
                else current + "\n\n" + paragraph
            )

            if len(candidate) <= self.max_characters:
                current = candidate
                continue

            if current:
                chunks.append(current)

            overlap_text = current[
                max(
                    0,
                    len(current) - self.overlap,
                ):
            ]

            current = (
                overlap_text
                + "\n\n"
                + paragraph
            ).strip()

        if current:
            chunks.append(current)

        return [
            DocumentChunk(
                chunk_id=f"{document_id}-{index:04d}",
                content=content,
                chunk_index=index,
            )
            for index, content in enumerate(chunks)
        ]
