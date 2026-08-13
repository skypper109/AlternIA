from dataclasses import dataclass

from alternia.pedagogy.pedagogical_engine import (
    PedagogicalEngine,
)

from alternia.pedagogy.intent import (
    PedagogicalIntent,
)


@dataclass
class FakeSource:
    chunk_id: str


@dataclass
class FakeContext:
    context_text: str
    sources: list


def test_engine_detects_concept_explanation():

    engine = PedagogicalEngine()

    context = FakeContext(
        context_text=(
            "Une équation est une égalité "
            "contenant une inconnue."
        ),
        sources=[
            FakeSource("equation-001"),
        ],
    )

    response = engine.generate(
        question="Qu'est-ce qu'une équation ?",
        context=context,
        student_class="10eme",
        subject="mathematiques",
    )

    assert (
        response.intent
        == PedagogicalIntent.CONCEPT_EXPLANATION.value
    )

    assert "équation" in response.answer.lower()

    assert response.student_class == "10eme"

    assert response.subject == "mathematiques"

    assert len(response.sources) == 1


def test_engine_handles_problem_solving():

    engine = PedagogicalEngine()

    context = FakeContext(
        context_text=(
            "Pour résoudre une équation, "
            "on cherche la valeur de l'inconnue."
        ),
        sources=[],
    )

    response = engine.generate(
        question="Comment résoudre une équation ?",
        context=context,
        student_class="10eme",
        subject="mathematiques",
    )

    assert (
        response.intent
        == PedagogicalIntent.PROBLEM_SOLVING.value
    )

    assert "étape" in response.answer.lower()


def test_engine_handles_unknown_question():

    engine = PedagogicalEngine()

    context = FakeContext(
        context_text="",
        sources=[],
    )

    response = engine.generate(
        question="Bonjour",
        context=context,
        student_class="10eme",
        subject="mathematiques",
    )

    assert (
        response.intent
        == PedagogicalIntent.UNKNOWN.value
    )

    assert response.answer


def test_engine_tracks_context_usage():

    engine = PedagogicalEngine()

    context = FakeContext(
        context_text="Contenu pédagogique.",
        sources=[
            FakeSource("chunk-001"),
            FakeSource("chunk-002"),
        ],
    )

    response = engine.generate(
        question="Qu'est-ce qu'un triangle ?",
        context=context,
        student_class="10eme",
        subject="mathematiques",
    )

    assert response.metadata["context_used"] is True

    assert response.metadata["source_count"] == 2
