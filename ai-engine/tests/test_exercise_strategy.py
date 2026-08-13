from alternia.pedagogical.models import (
    StudentProfile,
    QuestionAnalysis,
    PedagogicalRequest,
)

from alternia.pedagogical.strategies.exercise import (
    ExerciseStrategy,
)


def make_request(context=""):

    profile = StudentProfile(
        student_class="10eme",
        preferred_language="fr",
    )

    analysis = QuestionAnalysis(
        original_question="Donne-moi un exercice sur les équations.",
        intent="exercise",
        student_class="10eme",
        subject="mathematiques",
        chapter="algebre",
        lesson="equations",
    )

    return PedagogicalRequest(
        question="Donne-moi un exercice sur les équations.",
        profile=profile,
        analysis=analysis,
        context=context,
    )


def test_exercise_with_rag_context():

    strategy = ExerciseStrategy()

    request = make_request(
        context=(
            "Une équation du premier degré "
            "est une égalité contenant "
            "une inconnue."
        )
    )

    answer = strategy.generate(request)

    assert "EXERCICE D'ENTRAÎNEMENT" in answer
    assert "10eme" in answer
    assert "mathematiques" in answer
    assert "équation du premier degré" in answer


def test_exercise_without_context():

    strategy = ExerciseStrategy()

    request = make_request()

    answer = strategy.generate(request)

    assert "EXERCICE D'ENTRAÎNEMENT" in answer
    assert "contexte pédagogique suffisant" in answer
