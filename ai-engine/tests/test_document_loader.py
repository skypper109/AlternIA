from pathlib import Path

from alternia.ingestion.loaders.text import (
    TextDocumentLoader,
)


def test_text_document_loader(tmp_path):

    document = tmp_path / "programme.txt"

    document.write_text(
        "Mathématiques - Équations du premier degré",
        encoding="utf-8",
    )

    loader = TextDocumentLoader()

    result = loader.load(document)

    assert result.filename == "programme.txt"

    assert result.extension == ".txt"

    assert (
        "Équations du premier degré"
        in result.content
    )

    assert result.document_id