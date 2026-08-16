import re
from pathlib import Path
from uuid import uuid4

import pymupdf

from .base import (
    DocumentLoader,
    DocumentPage,
    LoadedDocument,
)


class PDFDocumentLoader(DocumentLoader):

    def load(
        self,
        path: str | Path,
    ) -> LoadedDocument:

        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(
                f"Document introuvable : {path}"
            )

        if path.suffix.lower() != ".pdf":
            raise ValueError(
                f"Le fichier n'est pas un PDF : {path}"
            )

        pages: list[DocumentPage] = []

        with pymupdf.open(path) as pdf:

            for index in range(len(pdf)):
                page = pdf[index]
                raw_content = str(page.get_text("text"))
                clean_content = self._clean_page_text(raw_content)

                if clean_content.strip():
                    pages.append(
                        DocumentPage(
                            page_number=index + 1,
                            content=clean_content,
                        )
                    )

        full_content = "\n\n".join(
            page.content
            for page in pages
        )

        return LoadedDocument(
            document_id=str(uuid4()),
            source_path=str(path),
            filename=path.name,
            extension=".pdf",
            content=full_content,
            pages=pages,
        )

    @staticmethod
    def _clean_page_text(text: str) -> str:
        """Nettoie le texte extrait du PDF pour éliminer les scories et en-têtes parasites."""
        if not text:
            return ""

        lines = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            # Élimination des numéros de téléphone / mails répétitifs des profs dans les en-têtes
            if re.search(r"\b(?:cel|tel|tél|téléphone)\s*:\s*[\d\s/]+", line, re.IGNORECASE):
                continue
            if re.search(r"\bmail\s*:\s*[\w\.-]+@[\w\.-]+", line, re.IGNORECASE):
                continue
            if re.search(r"^\s*m\.dabire\b", line, re.IGNORECASE):
                # Nettoyer la signature d'en-tête de certains manuels de physique/chimie
                line = re.sub(r"^\s*m\.dabire\s*(?:\d{2}/\d{2}/\d{4}\s*\d{2}:\d{2})?\s*", "", line, flags=re.IGNORECASE).strip()
                if not line:
                    continue

            # Supprimer les numéros de page isolés en bas ou haut de page
            if re.match(r"^\d{1,4}$", line):
                continue

            # Nettoyer les espaces multiples consécutifs
            line = re.sub(r"[ \t]+", " ", line)
            lines.append(line)

        cleaned = "\n".join(lines)
        # Remplacer plus de 2 retours à la ligne par 2
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()