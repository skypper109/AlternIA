from alternia.pedagogy.intent import (
    IntentDetector,
    PedagogicalIntent,
)


def test_detect_concept_explanation():

    detector = IntentDetector()

    intent = detector.detect(
        "Qu'est-ce qu'une équation ?"
    )

    assert intent == (
        PedagogicalIntent.CONCEPT_EXPLANATION
    )


def test_detect_problem_solving():

    detector = IntentDetector()

    intent = detector.detect(
        "Comment résoudre 2x + 5 = 15 ?"
    )

    assert intent == (
        PedagogicalIntent.PROBLEM_SOLVING
    )


def test_detect_practice():

    detector = IntentDetector()

    intent = detector.detect(
        "Donne-moi un exercice sur les équations."
    )

    assert intent == (
        PedagogicalIntent.PRACTICE
    )


def test_detect_reexplanation():

    detector = IntentDetector()

    intent = detector.detect(
        "Je n'ai pas compris, explique encore."
    )

    assert intent == (
        PedagogicalIntent.REEXPLANATION
    )


def test_detect_correction():

    detector = IntentDetector()

    intent = detector.detect(
        "Corrige mon exercice."
    )

    assert intent == (
        PedagogicalIntent.CORRECTION
    )


def test_detect_revision():

    detector = IntentDetector()

    intent = detector.detect(
        "Donne-moi un résumé à retenir."
    )

    assert intent == (
        PedagogicalIntent.REVISION
    )


def test_empty_question_is_unknown():

    detector = IntentDetector()

    intent = detector.detect("")

    assert intent == (
        PedagogicalIntent.UNKNOWN
    )
