from alternia.learner.assessment import (
    LearningAssessmentService,
)
from alternia.learner.manager import (
    LearnerManager,
)
from alternia.learner.models import (
    LearningInteraction,
)


def make_service():

    manager = LearnerManager()

    manager.create_profile(
        student_id="student-001",
        student_class="10eme",
    )

    return (
        manager,
        LearningAssessmentService(
            learner_manager=manager,
        ),
    )


def test_assessment_registers_success():

    manager, service = make_service()

    interaction = LearningInteraction(
        question="Résous x + 2 = 5",
        intent="correction",
        subject="mathematiques",
        topic="equations",
    )

    result = service.assess(
        student_id="student-001",
        interaction=interaction,
        expected_answer="x = 3",
        student_answer="x = 3",
    )

    assert result.success is True
    assert result.score == 1.0

    profile = manager.get_profile(
        "student-001"
    )

    assert (
        profile.statistics
        .successful_interactions
        == 1
    )

    assert (
        profile.topic_progress[
            "equations"
        ].attempts
        == 1
    )


def test_assessment_registers_failure():

    manager, service = make_service()

    interaction = LearningInteraction(
        question="Résous x + 2 = 5",
        intent="correction",
        subject="mathematiques",
        topic="equations",
    )

    result = service.assess(
        student_id="student-001",
        interaction=interaction,
        expected_answer="x = 3",
        student_answer="x = 8",
    )

    assert result.success is False
    assert result.score == 0.0

    profile = manager.get_profile(
        "student-001"
    )

    assert (
        profile.statistics
        .failed_interactions
        == 1
    )

    progress = profile.topic_progress[
        "equations"
    ]

    assert progress.attempts == 1
    assert progress.failures == 1
    assert progress.mastery_score == 0.0

    assert (
        "equations"
        in profile.topics_to_review
    )