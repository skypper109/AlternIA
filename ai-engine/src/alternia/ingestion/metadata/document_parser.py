from alternia.ingestion.loaders.base import (
    LoadedDocument,
)

from .structure import PedagogicalMetadata
from .structured_page import StructuredPage


class DocumentStructureParser:
    """
    Transforme un document chargé en pages enrichies
    avec des métadonnées pédagogiques propagées.
    """

    def __init__(
        self,
        structure_detector,
        subject_resolver=None,
    ):
        self.structure_detector = structure_detector
        self.subject_resolver = subject_resolver

    def parse(
        self,
        document: LoadedDocument,
    ) -> list[StructuredPage]:

        context = PedagogicalMetadata()

        # Résolution globale de la matière.
        if self.subject_resolver:

            context.subject = (
                self.subject_resolver.resolve(
                    document.content,
                    filename=document.filename,
                )
            )

        structured_pages: list[StructuredPage] = []

        for page in document.pages:

            page_metadata = self._process_page(
                page.content,
                context,
            )

            structured_pages.append(
                StructuredPage(
                    page_number=page.page_number,
                    content=page.content,
                    metadata=page_metadata,
                )
            )

            context = page_metadata.copy()

        return structured_pages

    def _process_page(
        self,
        content: str,
        context: PedagogicalMetadata,
    ) -> PedagogicalMetadata:

        metadata = context.copy()

        detected = self.structure_detector.detect(
            content
        )

        if detected.student_class:

            metadata.student_class = (
                detected.student_class
            )

        if detected.chapter:

            metadata.chapter = detected.chapter

            metadata.lesson = None

            metadata.section = None

        if detected.lesson:

            metadata.lesson = detected.lesson

            metadata.section = None

        return metadata