from dataclasses import dataclass
from typing import Optional

from alternia.ingestion.metadata.structure import (
    PedagogicalMetadata,
)


@dataclass
class PedagogicalChunk:
    """
    Unité de connaissance pédagogique indexée
    dans le RAG d'AlternIA.

    Un chunk conserve :
    - son identifiant ;
    - son contenu ;
    - ses métadonnées pédagogiques ;
    - son document source ;
    - son titre ;
    - les pages concernées.

    Le titre est optionnel afin de rester compatible
    avec les anciens consommateurs du modèle.
    """

    chunk_id: str

    content: str

    metadata: PedagogicalMetadata

    source_document: str

    page_start: int

    page_end: int

    title: Optional[str] = None

    source_version: Optional[str] = None