from alternia.ingestion.cleaners.text_cleaner import (
    TextCleaner,
)


def test_text_cleaner():

    raw_text = """
PROGRAMME DE MATHEMATIQUES


Classe : 10ème


CHAPITRE I


EQUATIONS


Les équations du premier degré


Une équation est une égalité...


12


"""

    cleaner = TextCleaner()

    result = cleaner.clean(raw_text)

    assert "PROGRAMME DE MATHEMATIQUES" in result

    assert "Classe : 10ème" in result

    assert "CHAPITRE I" in result

    assert "EQUATIONS" in result

    assert "Les équations du premier degré" in result

    assert "Une équation est une égalité..." in result

    # Le numéro de page doit avoir disparu.
    assert "\n12\n" not in result
    