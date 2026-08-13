from alternia.pedagogical.models import (
    StudentProfile,
    QuestionAnalysis,
    PedagogicalRequest,
)

from alternia.pedagogical.strategies.explanation import (
    ExplanationStrategy,
)


def make_request(context=""):

    profile = StudentProfile(
        student_class="10eme",
        preferred_language="fr",
    )

    analysis = QuestionAnalysis(
        original_question="Comment résoudre une équation ?",
        intent="explanation",
        student_class="10eme",
        subject="mathematiques",
        chapter="algebre",
        lesson="equations",
    )

    return PedagogicalRequest(
        question="Comment résoudre une équation ?",
        profile=profile,
        analysis=analysis,
        context=context,
    )


def test_explanation_with_rag_context():

    strategy = ExplanationStrategy()

    request = make_request(
        context=(
            "Une équation du premier degré "
            "est une égalité contenant "
            "une inconnue."
        )
    )

    answer = strategy.generate(request)

    assert "EXPLICATION PÉDAGOGIQUE" in answer
    assert "équation du premier degré" in answer
    assert "10eme" not in answer or answer != ""


def test_explanation_without_context():

    strategy = ExplanationStrategy()

    request = make_request()

    answer = strategy.generate(request)

    assert "EXPLICATION PÉDAGOGIQUE" in answer
    assert "contexte pédagogique suffisant" in answer
