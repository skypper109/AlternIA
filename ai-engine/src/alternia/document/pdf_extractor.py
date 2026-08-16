from pathlib import Path

from pypdf import PdfReader


class PDFExtractor:
    """
    Extraction de texte depuis les PDF pédagogiques AlternIA.
    """

    def extract(
        self,
        pdf_path: str | Path,
    ) -> str:

        path = Path(pdf_path)

        if not path.exists():
            raise FileNotFoundError(
                f"PDF introuvable : {path}"
            )

        if path.suffix.lower() != ".pdf":
            raise ValueError(
                f"Le fichier n'est pas un PDF : {path}"
            )

        reader = PdfReader(
            str(path)
        )

        pages = []

        for page in reader.pages:

            text = page.extract_text()

            if text:
                pages.append(
                    text
                )

        return "\n\n".join(
            pages
        ).strip()