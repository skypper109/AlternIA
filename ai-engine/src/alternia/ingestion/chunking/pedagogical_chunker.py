from alternia.core.pedagogical_chunk import PedagogicalChunk
from alternia.ingestion.metadata.structured_page import StructuredPage


class PedagogicalChunker:
    """
    Transforme les pages structurées en chunks pédagogiques.

    Le chunk conserve :

    - le contexte pédagogique ;
    - la classe ;
    - la matière ;
    - le chapitre ;
    - la leçon ;
    - la section ;
    - le titre du document ;
    - le document source ;
    - les pages concernées.

    Principe :

        StructuredPage
              ↓
        regroupement par contexte
              ↓
        taille maximale
              ↓
        PedagogicalChunk
    """

    def __init__(
        self,
        max_characters: int = 900,
        min_characters: int = 150,
        overlap_characters: int = 120,
    ):
        if max_characters <= 0:
            raise ValueError(
                "max_characters doit être supérieur à 0."
            )

        self.max_characters = max_characters
        self.min_characters = min_characters
        self.overlap_characters = overlap_characters

    def chunk(
        self,
        pages: list[StructuredPage],
        source_document: str,
        title: str | None = None,
        source_version: str | None = None,
    ) -> list[PedagogicalChunk]:

        raw_chunks: list[PedagogicalChunk] = []

        for page in pages:
            text = page.content.strip()
            if not text:
                continue

            metadata = page.metadata.copy()

            if len(text) <= self.max_characters:
                raw_chunks.append(
                    self._create_chunk(
                        content=text,
                        metadata=metadata,
                        source_document=source_document,
                        title=title,
                        source_version=source_version,
                        page_start=page.page_number,
                        page_end=page.page_number,
                        index=len(raw_chunks),
                    )
                )
            else:
                # Découpage sémantique fin par paragraphes et sections
                sub_chunks = self._split_text_semantically(
                    text=text,
                    max_chars=self.max_characters,
                    overlap=self.overlap_characters,
                )
                for sub_text in sub_chunks:
                    if len(sub_text.strip()) >= self.min_characters:
                        raw_chunks.append(
                            self._create_chunk(
                                content=sub_text.strip(),
                                metadata=metadata,
                                source_document=source_document,
                                title=title,
                                source_version=source_version,
                                page_start=page.page_number,
                                page_end=page.page_number,
                                index=len(raw_chunks),
                            )
                        )

        # Regroupement des chunks trop petits consécutifs s'ils partagent le même contexte
        merged_chunks: list[PedagogicalChunk] = []
        current: PedagogicalChunk | None = None

        for chunk_item in raw_chunks:
            if current is None:
                current = chunk_item
                continue

            same_ctx = (
                current.metadata.student_class == chunk_item.metadata.student_class
                and current.metadata.subject == chunk_item.metadata.subject
                and current.metadata.chapter == chunk_item.metadata.chapter
                and current.metadata.lesson == chunk_item.metadata.lesson
                and current.source_document == chunk_item.source_document
            )

            if same_ctx and (len(current.content) + len(chunk_item.content) + 2 <= self.max_characters):
                current.content = f"{current.content}\n\n{chunk_item.content}"
                current.page_end = chunk_item.page_end
            else:
                merged_chunks.append(current)
                current = chunk_item

        if current is not None:
            merged_chunks.append(current)

        # Réindexer les IDs de manière ordonnée
        for idx, item in enumerate(merged_chunks):
            item.chunk_id = self._build_chunk_id(
                metadata=item.metadata,
                source_document=item.source_document,
                index=idx,
            )

        return merged_chunks

    def _split_text_semantically(
        self,
        text: str,
        max_chars: int,
        overlap: int,
    ) -> list[str]:
        """Découpe un long texte en respectant les paragraphes et les retours de ligne."""
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""

        for p in paragraphs:
            p = p.strip()
            if not p:
                continue

            if len(p) > max_chars:
                # Si le paragraphe lui-même dépasse max_chars, découpage par phrases ou lignes
                lines = p.split("\n")
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    if len(current_chunk) + len(line) + 1 <= max_chars:
                        current_chunk = f"{current_chunk}\n{line}" if current_chunk else line
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = line
            else:
                if len(current_chunk) + len(p) + 2 <= max_chars:
                    current_chunk = f"{current_chunk}\n\n{p}" if current_chunk else p
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    # Overlap
                    if overlap > 0 and len(current_chunk) > overlap:
                        overlap_prefix = current_chunk[-overlap:].split(" ", 1)[-1]
                        current_chunk = f"{overlap_prefix}\n\n{p}"
                    else:
                        current_chunk = p

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _create_chunk(
        self,
        content,
        metadata,
        source_document,
        title,
        page_start,
        page_end,
        index,
        source_version=None,
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
            title=title or "Document sans titre",
            source_version=source_version,
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