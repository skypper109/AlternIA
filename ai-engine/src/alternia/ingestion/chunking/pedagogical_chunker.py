from alternia.core.pedagogical_chunk import PedagogicalChunk
from alternia.ingestion.metadata.structured_page import StructuredPage


class PedagogicalChunker:
    """
    Transforme les pages structurées en chunks pédagogiques.

    Principe :
    - conserve le contexte pédagogique ;
    - regroupe plusieurs pages si nécessaire ;
    - conserve les numéros de pages ;
    - produit des identifiants stables.
    """

    def __init__(
        self,
        max_characters: int = 1800,
    ):
        self.max_characters = max_characters

    def chunk(
        self,
        pages: list[StructuredPage],
        source_document: str,
    ) -> list[PedagogicalChunk]:

        chunks: list[PedagogicalChunk] = []

        current_content = ""
        current_metadata = None
        current_page_start = None
        current_page_end = None

        for page in pages:

            if not page.content.strip():
                continue

            if current_metadata is None:

                current_metadata = page.metadata.copy()

                current_content = page.content.strip()

                current_page_start = page.page_number
                current_page_end = page.page_number

                continue

            same_context = (
                current_metadata.student_class
                == page.metadata.student_class
                and current_metadata.subject
                == page.metadata.subject
                and current_metadata.chapter
                == page.metadata.chapter
                and current_metadata.lesson
                == page.metadata.lesson
                and current_metadata.section
                == page.metadata.section
            )

            combined_length = (
                len(current_content)
                + len(page.content)
                + 2
            )

            if (
                same_context
                and combined_length
                <= self.max_characters
            ):

                current_content += (
                    "\n\n"
                    + page.content.strip()
                )

                current_page_end = page.page_number

            else:

                chunks.append(
                    self._create_chunk(
                        content=current_content,
                        metadata=current_metadata,
                        source_document=source_document,
                        page_start=current_page_start,
                        page_end=current_page_end,
                        index=len(chunks),
                    )
                )

                current_metadata = page.metadata.copy()

                current_content = page.content.strip()

                current_page_start = page.page_number
                current_page_end = page.page_number

        if current_content:

            chunks.append(
                self._create_chunk(
                    content=current_content,
                    metadata=current_metadata,
                    source_document=source_document,
                    page_start=current_page_start,
                    page_end=current_page_end,
                    index=len(chunks),
                )
            )

        return chunks

    def _create_chunk(
        self,
        content,
        metadata,
        source_document,
        page_start,
        page_end,
        index,
    ) -> PedagogicalChunk:

        chunk_id = self._build_chunk_id(
            metadata=metadata,
            source_document=source_document,
            index=index,
        )

        return PedagogicalChunk(
            chunk_id=chunk_id,
            content=content,
            metadata=metadata,
            source_document=source_document,
            page_start=page_start,
            page_end=page_end,
        )

    @staticmethod
    def _build_chunk_id(
        metadata,
        source_document,
        index,
    ):

        student_class = (
            metadata.student_class
            or "unknown-class"
        )

        subject = (
            metadata.subject
            or "unknown-subject"
        )

        chapter = (
            metadata.chapter
            or "unknown-chapter"
        )

        lesson = (
            metadata.lesson
            or "unknown-lesson"
        )

        return (
            f"{student_class}-"
            f"{subject}-"
            f"{chapter}-"
            f"{lesson}-"
            f"{index:04d}"
        )