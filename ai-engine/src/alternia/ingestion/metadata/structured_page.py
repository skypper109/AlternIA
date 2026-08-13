from dataclasses import dataclass

from .structure import PedagogicalMetadata


@dataclass
class StructuredPage:
    """
    Page d'un document enrichie avec son contexte pédagogique.
    """

    page_number: int
    content: str
    metadata: PedagogicalMetadata