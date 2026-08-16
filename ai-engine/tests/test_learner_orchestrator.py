from types import SimpleNamespace

from alternia.learner.manager import LearnerManager
from alternia.llm.fake_client import FakeLLMClient
from alternia.orchestration.orchestrator import (
    AlterniaOrchestrator,
)
from alternia.pedagogical.engine import (
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


def test_orchestrator_registers_learning_interaction():

    learner_manager = LearnerManager()

    learner_manager.create_profile(
        student_id="student-001",
        student_class="10eme",
    )

    orchestrator = AlterniaOrchestrator(
        pedagogical_engine=PedagogicalEngine(),
        llm_client=FakeLLMClient(
            response="Une équation contient une inconnue."
        ),
        learner_manager=learner_manager,
    )

    orchestrator.ask(
        question="Qu'est-ce qu'une équation ?",
        context=make_context(),
        student_class="10eme",
        subject="mathematiques",
        student_id="student-001",
    )

    profile = learner_manager.get_profile(
        "student-001"
    )

    assert profile.statistics.total_questions == 1

    assert len(
        profile.recent_interactions
    ) == 1

    interaction = (
        profile.recent_interactions[0]
    )

    assert (
        interaction.question
        == "Qu'est-ce qu'une équation ?"
    )

    assert (
        interaction.subject
        == "mathematiques"
    )

    assert interaction.success is None