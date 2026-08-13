from dataclasses import dataclass

from alternia.ingestion.metadata.structure import (
    PedagogicalMetadata,
)


@dataclass
class PedagogicalChunk:
    """
    Unité de connaissance indexée dans le RAG d'AlternIA.
    """

    chunk_id: str

    content: str

    metadata: PedagogicalMetadata

    source_document: str

    page_start: int

    page_end: int