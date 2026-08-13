from dataclasses import dataclass
from pathlib import Path


@dataclass
class DocumentPage:
    """
    Représente une page extraite d'un document.
    """

    page_number: int
    content: str


@dataclass
class LoadedDocument:
    """
    Document chargé depuis une source originale.
    """

    document_id: str
    source_path: str
    filename: str
    extension: str
    content: str
    pages: list[DocumentPage]


class DocumentLoader:
    """
    Interface de base pour les chargeurs de documents.

    Chaque type de document (TXT, PDF, DOCX, etc.)
    devra implémenter la méthode load().
    """

    def load(
        self,
        path: str | Path,
    ) -> LoadedDocument:

        raise NotImplementedError