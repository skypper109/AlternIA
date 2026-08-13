import fitz

from alternia.ingestion.loaders.pdf import (
    PDFDocumentLoader,
)


def test_pdf_document_loader(tmp_path):

    pdf_path = tmp_path / "programme.pdf"

    pdf = fitz.open()

    page = pdf.new_page()

    page.insert_text(
        (72, 72),
        "Programme de Mathématiques\n"
        "Classe de 10ème\n"
        "Chapitre : Equations",
    )

    pdf.save(pdf_path)

    pdf.close()

    loader = PDFDocumentLoader()

    result = loader.load(pdf_path)

    assert result.filename == "programme.pdf"

    assert result.extension == ".pdf"

    assert len(result.pages) == 1

    assert (
        "Programme de Mathématiques"
        in result.content
    )

    assert (
        "Classe de 10ème"
        in result.pages[0].content
    )

    assert result.pages[0].page_number == 1

    assert result.document_id