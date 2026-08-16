from pathlib import Path

from pypdf import PdfReader


class PDFDocument:
    """
    Représente le contenu extrait d'un PDF.
    """

    def __init__(
        self,
        text: str,
        source: str,
        pages: int,
    ):
        self.text = text
        self.source = source
        self.pages = pages


class PDFLoader:
    """
    Charge un fichier PDF et extrait son texte.

    Cette classe ne fait volontairement aucun nettoyage
    ni découpage.

    Pipeline :

        PDF
         ↓
        PDFLoader
         ↓
        texte brut
    """

    def load(
        self,
        pdf_path: str | Path,
    ) -> PDFDocument:

        path = Path(pdf_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Fichier PDF introuvable : {path}"
            )

        if path.suffix.lower() != ".pdf":
            raise ValueError(
                f"Le fichier n'est pas un PDF : {path}"
            )

        reader = PdfReader(str(path))

        pages = []

        for page_number, page in enumerate(
            reader.pages,
            start=1,
        ):

            try:
                text = page.extract_text() or ""
            except Exception as exc:
                print(
                    f"[PDF] Impossible de lire "
                    f"la page {page_number} : {exc}"
                )
                text = ""

            if text.strip():
                pages.append(
                    f"\n--- PAGE {page_number} ---\n"
                    f"{text}"
                )

        full_text = "\n".join(pages)

        if not full_text.strip():
            raise ValueError(
                f"Aucun texte exploitable trouvé dans : "
                f"{path}"
            )

        return PDFDocument(
            text=full_text,
            source=str(path),
            pages=len(reader.pages),
        )