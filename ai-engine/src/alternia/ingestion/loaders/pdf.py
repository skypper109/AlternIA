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

            for index, page in enumerate(pdf):

                content = page.get_text("text")

                pages.append(
                    DocumentPage(
                        page_number=index + 1,
                        content=content,
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