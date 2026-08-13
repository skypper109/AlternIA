from alternia.ingestion.metadata.subject_resolver import (
    SubjectResolver,
)


def test_resolve_mathematics():

    resolver = SubjectResolver()

    result = resolver.resolve(
        """
        PROGRAMME DE MATHEMATIQUES
        CLASSE DE 10EME
        """
    )

    assert result == "mathematiques"


def test_resolve_physics():

    resolver = SubjectResolver()

    result = resolver.resolve(
        """
        PROGRAMME DE SCIENCES PHYSIQUES
        CLASSE DE 10EME
        """
    )

    assert result == "physique"


def test_resolve_from_filename():

    resolver = SubjectResolver()

    result = resolver.resolve(
        "Programme de français",
        filename="francais_10eme.pdf",
    )

    assert result == "francais"


def test_unknown_subject():

    resolver = SubjectResolver()

    result = resolver.resolve(
        "Programme d'une matière inconnue",
    )

    assert result is None