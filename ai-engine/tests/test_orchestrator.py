from types import SimpleNamespace

from alternia.llm.fake_client import FakeLLMClient
from alternia.orchestration.orchestrator import (
    AlterniaOrchestrator,
)
from alternia.pedagogy.pedagogical_engine import (
    PedagogicalEngine,
)


def make_context():

    return SimpleNamespace(
        context_text=(
            "Une équation est une égalité "
            "contenant une inconnue."
        ),
        sources=[],
    )


def test_orchestrator_generates_answer():

    llm = FakeLLMClient(
        response="Une équation contient une inconnue."
    )

    orchestrator = AlterniaOrchestrator(
        pedagogical_engine=PedagogicalEngine(),
        llm_client=llm,
    )

    response = orchestrator.ask(
        question="Qu'est-ce qu'une équation ?",
        context=make_context(),
        student_class="10eme",
        subject="mathematiques",
    )

    assert (
        response["answer"]
        == "Une équation contient une inconnue."
    )

    assert (
        response["intent"]
        == "concept_explanation"
    )

    assert response["student_class"] == "10eme"

    assert (
        response["subject"]
        == "mathematiques"
    )


def test_orchestrator_passes_context_to_llm():

    class InspectingLLM(FakeLLMClient):

        def generate(
            self,
            prompt,
            *,
            system_prompt=None,
        ):

            assert (
                "Une équation est une égalité"
                in prompt
            )

            assert (
                "Qu'est-ce qu'une équation ?"
                in prompt
            )

            return "Réponse test."

    orchestrator = AlterniaOrchestrator(
        pedagogical_engine=PedagogicalEngine(),
        llm_client=InspectingLLM(),
    )

    response = orchestrator.ask(
        question="Qu'est-ce qu'une équation ?",
        context=make_context(),
        student_class="10eme",
        subject="mathematiques",
    )

    assert response["answer"] == "Réponse test."


def test_orchestrator_marks_llm_usage():

    orchestrator = AlterniaOrchestrator(
        pedagogical_engine=PedagogicalEngine(),
        llm_client=FakeLLMClient(
            response="Réponse."
        ),
    )

    response = orchestrator.ask(
        question="Bonjour",
        context=make_context(),
        student_class="10eme",
        subject="mathematiques",
    )

    assert response["metadata"]["llm_used"] is True
