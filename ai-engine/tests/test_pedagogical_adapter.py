from types import SimpleNamespace

from alternia.pedagogical.legacy_adapter import (
    PedagogicalEngineAdapter,
)


def make_context():
    return SimpleNamespace(
        context_text=(
            "Une équation du premier degré "
            "est une égalité contenant "
            "une inconnue."
        ),
        sources=[],
    )


def test_adapter_generates_pedagogical_response():

    adapter = PedagogicalEngineAdapter()

    response = adapter.generate(
        question="Qu'est-ce qu'une équation ?",
        context=make_context(),
        student_class="10eme",
        subject="mathematiques",
    )

    assert response.answer

    assert (
        response.intent
        == "explanation"
    )

    assert (
        response.student_class
        == "10eme"
    )

    assert (
        response.subject
        == "mathematiques"
    )


def test_adapter_passes_rag_context():

    adapter = PedagogicalEngineAdapter()

    response = adapter.generate(
        question="Qu'est-ce qu'une équation ?",
        context=make_context(),
        student_class="10eme",
        subject="mathematiques",
    )

    assert (
        "équation du premier degré"
        in response.answer
    )


def test_adapter_detects_exercise():

    adapter = PedagogicalEngineAdapter()

    response = adapter.generate(
        question="Donne-moi un exercice "
        "sur les équations.",
        context=make_context(),
        student_class="10eme",
        subject="mathematiques",
    )

    assert (
        response.intent
        == "exercise"
    )


def test_adapter_detects_correction():

    adapter = PedagogicalEngineAdapter()

    response = adapter.generate(
        question="Peux-tu corriger mon exercice ?",
        context=make_context(),
        student_class="10eme",
        subject="mathematiques",
    )

    assert (
        response.intent
        == "correction"
    )


def test_adapter_detects_revision():

    adapter = PedagogicalEngineAdapter()

    response = adapter.generate(
        question="Je veux réviser les équations.",
        context=make_context(),
        student_class="10eme",
        subject="mathematiques",
    )

    assert (
        response.intent
        == "revision"
    )


def test_adapter_detects_summary():

    adapter = PedagogicalEngineAdapter()

    response = adapter.generate(
        question="Résume-moi le cours.",
        context=make_context(),
        student_class="10eme",
        subject="mathematiques",
    )

    assert (
        response.intent
        == "summary"
    )


def test_adapter_handles_empty_context():

    adapter = PedagogicalEngineAdapter()

    response = adapter.generate(
        question="Qu'est-ce qu'une équation ?",
        context=SimpleNamespace(
            context_text="",
            sources=[],
        ),
        student_class="10eme",
        subject="mathematiques",
    )

    assert response.answer

    assert (
        response.metadata["context_used"]
        is False
    )