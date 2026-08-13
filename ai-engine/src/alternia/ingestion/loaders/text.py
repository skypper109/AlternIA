from pathlib import Path
from uuid import uuid4

from .base import DocumentLoader, DocumentPage, LoadedDocument


class TextDocumentLoader(DocumentLoader):

    def load(
        self,
        path: str | Path,
    ) -> LoadedDocument:

        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(
                f"Document introuvable : {path}"
            )

        content = path.read_text(
            encoding="utf-8"
        )

        return LoadedDocument(
            document_id=str(uuid4()),
            source_path=str(path),
            filename=path.name,
            extension=path.suffix.lower(),
            content=content,
            pages=[
                DocumentPage(
                    page_number=1,
                    content=content,
                )
            ],
        )