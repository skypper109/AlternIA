from pathlib import Path

from alternia.core.pedagogical_chunk import (
    PedagogicalChunk,
)

from alternia.ingestion.chunking.pedagogical_chunker import (
    PedagogicalChunker,
)

from alternia.ingestion.loaders.pdf import (
    PDFDocumentLoader,
)

from alternia.ingestion.metadata.document_parser import (
    DocumentStructureParser,
)

from alternia.ingestion.metadata.structure_detector import (
    StructureDetector,
)

from alternia.ingestion.metadata.subject_resolver import (
    SubjectResolver,
)


class DocumentIngestionPipeline:
    """
    Pipeline canonique d'ingestion AlternIA.

    Pipeline :

        PDF
         ↓
        PDFDocumentLoader
         ↓
        LoadedDocument
         ↓
        DocumentStructureParser
         ↓
        StructuredPage
         ↓
        PedagogicalChunker
         ↓
        PedagogicalChunk
    """

    def __init__(
        self,
        max_chunk_characters: int = 1800,
    ):

        self.loader = PDFDocumentLoader()

        self.structure_detector = (
            StructureDetector()
        )

        self.subject_resolver = (
            SubjectResolver()
        )

        self.structure_parser = (
            DocumentStructureParser(
                structure_detector=(
                    self.structure_detector
                ),
                subject_resolver=(
                    self.subject_resolver
                ),
            )
        )

        self.chunker = (
            PedagogicalChunker(
                max_characters=(
                    max_chunk_characters
                )
            )
        )

    def process_file(
        self,
        pdf_path: str | Path,
        source_version: str | None = None,
    ) -> list[PedagogicalChunk]:

        path = Path(pdf_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Fichier PDF introuvable : {path}"
            )

        document = self.loader.load(
            path
        )

        structured_pages = (
            self.structure_parser.parse(
                document
            )
        )

        chunks = self.chunker.chunk(
            pages=structured_pages,
            source_document=str(path),
            title=path.stem,
            source_version=source_version,
        )

        return chunks

    def process_directory(
        self,
        directory: str | Path,
    ) -> list[PedagogicalChunk]:

        root = Path(directory)

        if not root.exists():
            raise FileNotFoundError(
                f"Dossier introuvable : {root}"
            )

        pdf_files = sorted(
            root.rglob("*.pdf")
        )

        all_chunks: list[
            PedagogicalChunk
        ] = []

        for pdf_path in pdf_files:

            print(
                f"[INGESTION] {pdf_path}"
            )

            chunks = self.process_file(
                pdf_path
            )

            print(
                f"[INGESTION] "
                f"{len(chunks)} chunks"
            )

            all_chunks.extend(chunks)

        return all_chunks