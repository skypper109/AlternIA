from pathlib import Path

from pypdf import PdfReader


class PDFReader:
    """
    Lecture simple de documents PDF pour AlternIA.

    Le PDF est transformé en texte brut afin de pouvoir
    ensuite être découpé et indexé dans le RAG.
    """

    def extract(self, pdf_path: str | Path) -> str:

        path = Path(pdf_path)

        if not path.exists():
            raise FileNotFoundError(
                f"PDF introuvable : {path}"
            )

        if path.suffix.lower() != ".pdf":
            raise ValueError(
                "Le fichier doit être un PDF."
            )

        reader = PdfReader(str(path))

        pages = []

        for page in reader.pages:

            text = page.extract_text() or ""

            if text.strip():
                pages.append(text.strip())

        content = "\n\n".join(pages)

        if not content.strip():
            raise ValueError(
                "Aucun texte exploitable trouvé dans le PDF."
            )

        return content

    def extract_pages(
        self,
        pdf_path: str | Path,
    ) -> list[str]:

        path = Path(pdf_path)

        if not path.exists():
            raise FileNotFoundError(
                f"PDF introuvable : {path}"
            )

        reader = PdfReader(str(path))

        pages = []

        for page in reader.pages:
            pages.append(
                (page.extract_text() or "").strip()
            )

        return pages
