from alternia.context.models import (
    ContextSource,
    PedagogicalContext,
)

from alternia.llm.fake_client import (
    FakeLLMClient,
)

from alternia.orchestration.orchestrator import (
    AlterniaOrchestrator,
)

from alternia.pedagogy.pedagogical_engine import (
    PedagogicalEngine,
)


def test_real_orchestration_pipeline():

    context = PedagogicalContext(
        query="Qu'est-ce qu'une équation ?",
        student_class="10eme",
        subject="mathematiques",
        sources=[
            ContextSource(
                chunk_id="test-equation",
                content=(
                    "Une équation du premier degré "
                    "est une égalité contenant "
                    "une inconnue."
                ),
                score=0.95,
                student_class="10eme",
                subject="mathematiques",
                chapter="algebre",
                lesson="equations",
                source_document="programme-mali-test.txt",
                metadata={},
            )
        ],
        context_text=(
            "CONTEXTE PÉDAGOGIQUE ALTERNIA\n\n"
            "Une équation du premier degré "
            "est une égalité contenant "
            "une inconnue.\n\n"
            "FIN DU CONTEXTE"
        ),
        max_sources=3,
    )

    engine = PedagogicalEngine()

    llm = FakeLLMClient()

    orchestrator = AlterniaOrchestrator(
        pedagogical_engine=engine,
        llm_client=llm,
    )

    response = orchestrator.ask(
        question="Qu'est-ce qu'une équation ?",
        context=context,
        student_class="10eme",
        subject="mathematiques",
    )

    assert response["answer"]

    assert (
        "équation"
        in response["answer"].lower()
    )

    assert (
        response["intent"]
        == "concept_explanation"
    )

    assert (
        response["student_class"]
        == "10eme"
    )

    assert (
        response["subject"]
        == "mathematiques"
    )

    assert (
        response["metadata"]["llm_used"]
        is True
    )

    assert (
        response["metadata"]["context_used"]
        is True
    )