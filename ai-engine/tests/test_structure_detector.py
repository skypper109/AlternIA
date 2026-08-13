from alternia.ingestion.metadata.structure_detector import (
    StructureDetector,
)


def test_detect_student_class():

    detector = StructureDetector()

    text = """
    PROGRAMME DE MATHEMATIQUES

    CLASSE DE 10EME

    CHAPITRE I : ALGEBRE

    LEÇON 1 : EQUATIONS
    """

    metadata = detector.detect(text)

    assert metadata.student_class == "10eme"


def test_detect_chapter():

    detector = StructureDetector()

    chapter = detector.detect_chapter(
        "CHAPITRE I : ALGEBRE"
    )

    assert chapter == "algebre"


def test_detect_lesson():

    detector = StructureDetector()

    lesson = detector.detect_lesson(
        "LEÇON 1 : EQUATIONS"
    )

    assert lesson == "equations"