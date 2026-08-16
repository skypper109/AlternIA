from alternia.learner.adaptation import (
    LearningAdaptationService,
)
from alternia.learner.manager import (
    LearnerManager,
)


def test_adaptation_detects_topic_to_review():

    manager = LearnerManager()

    profile = manager.create_profile(
        student_id="student-001",
        student_class="10eme",
    )

    profile.topics_to_review.append(
        "equations"
    )

    service = LearningAdaptationService()

    context = service.build_adaptation_context(
        profile,
        topic="equations",
    )

    assert (
        "NOTIONS À REVOIR"
        in context
    )

    assert (
        "equations"
        in context
    )

    assert (
        "Reprendre les bases"
        in context
    )


def test_adaptation_detects_mastered_topic():

    manager = LearnerManager()

    profile = manager.create_profile(
        student_id="student-001",
        student_class="10eme",
    )

    profile.mastered_topics.append(
        "fractions"
    )

    service = LearningAdaptationService()

    context = service.build_adaptation_context(
        profile,
        topic="fractions",
    )

    assert (
        "NOTIONS MAÎTRISÉES"
        in context
    )

    assert (
        "fractions"
        in context
    )

    assert (
        "maîtrise déjà cette notion"
        in context
    )