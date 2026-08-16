from alternia.pedagogical.engine import PedagogicalEngine
from alternia.pedagogical.models import (
    PedagogicalRequest,
    QuestionAnalysis,
    StudentProfile,
)


def make_request(
    *,
    intent="explanation",
    context="",
):
    profile = StudentProfile(
        student_id="student-test",
        student_class="10eme",
    )

    analysis = QuestionAnalysis(
        original_question="Qu'est-ce qu'une équation ?",
        intent=intent,
        student_class="10eme",
        subject="mathematiques",
        chapter="algebre",
        lesson="equations",
    )

    return PedagogicalRequest(
        question="Qu'est-ce qu'une équation ?",
        profile=profile,
        analysis=analysis,
        context=context,
    )


def test_engine_selects_explanation_strategy():

    engine = PedagogicalEngine()

    request = make_request(
        intent="explanation",
        context=(
            "Une équation du premier degré "
            "est une égalité contenant une inconnue."
        ),
    )

    response = engine.process(request)

    assert response.intent == "explanation"

    assert (
        "EXPLICATION PÉDAGOGIQUE"
        in response.answer
    )

    assert (
        "équation du premier degré"
        in response.answer
    )

    assert response.student_class == "10eme"

    assert response.subject == "mathematiques"


def test_engine_selects_exercise_strategy():

    engine = PedagogicalEngine()

    request = make_request(
        intent="exercise",
        context=(
            "Résolution des équations "
            "du premier degré."
        ),
    )

    response = engine.process(request)

    assert response.intent == "exercise"

    assert (
        "EXERCICE D'ENTRAÎNEMENT"
        in response.answer
    )

    assert "10eme" in response.answer

    assert (
        "Résolution des équations"
        in response.answer
    )


def test_engine_defaults_to_explanation():

    engine = PedagogicalEngine()

    request = make_request(
        intent="unknown_intent",
    )

    response = engine.process(request)

    assert response.intent == "explanation"


def test_engine_rejects_empty_question():

    engine = PedagogicalEngine()

    request = make_request()

    request.question = "   "

    try:
        engine.process(request)
        assert False
    except ValueError as exc:
        assert (
            "question"
            in str(exc).lower()
        )


def test_engine_follow_up_for_explanation():

    engine = PedagogicalEngine()

    request = make_request(
        intent="explanation",
    )

    response = engine.process(request)

    assert response.needs_follow_up is True

    assert response.follow_up_question


def test_engine_no_follow_up_for_exercise():

    engine = PedagogicalEngine()

    request = make_request(
        intent="exercise",
    )

    response = engine.process(request)

    assert response.needs_follow_up is False

    assert response.follow_up_question is None