from alternia.learner.models import (
    LearningInteraction,
)
from alternia.learner.profile import (
    LearningProfile,
)


def test_learning_profile_creation():

    profile = LearningProfile(
        student_id="student-001",
        student_class="10eme",
    )

    assert profile.student_id == "student-001"

    assert profile.student_class == "10eme"

    assert profile.statistics.total_questions == 0

    assert profile.mastered_topics == []
    assert profile.history == []



def test_register_successful_interaction():

    profile = LearningProfile(
        student_id="student-001",
        student_class="10eme",
    )

    interaction = LearningInteraction(
        question="Résous 2x + 5 = 15",
        intent="problem_solving",
        subject="mathematiques",
        topic="équations du premier degré",
        success=True,
    )

    profile.register_interaction(
        interaction
    )

    assert (
        profile.statistics.total_questions
        == 1
    )

    assert (
        profile.statistics.successful_interactions
        == 1
    )

    assert (
        profile.current_topic
        == "équations du premier degré"
    )


def test_topic_progress():

    profile = LearningProfile(
        student_id="student-001",
        student_class="10eme",
    )

    for success in [True, True]:

        profile.register_interaction(
            LearningInteraction(
                question="Exercice",
                intent="exercise",
                subject="mathematiques",
                topic="équations",
                success=success,
            )
        )

    progress = profile.topic_progress[
        "équations"
    ]

    assert progress.attempts == 2

    assert progress.successes == 2

    assert progress.mastery_score == 1.0

    assert (
        "équations"
        in profile.mastered_topics
    )

    assert (
        "équations"
        not in profile.topics_to_review
    )


def test_topic_to_review():

    profile = LearningProfile(
        student_id="student-001",
        student_class="10eme",
    )

    profile.register_interaction(
        LearningInteraction(
            question="Je n'arrive pas",
            intent="correction",
            subject="mathematiques",
            topic="fractions",
            success=False,
        )
    )

    assert (
        "fractions"
        in profile.topics_to_review
    )


def test_learner_manager():

    from alternia.learner.manager import (
        LearnerManager,
    )

    manager = LearnerManager()

    profile = manager.create_profile(
        student_id="student-001",
        student_class="10eme",
    )

    assert profile.student_id == "student-001"

    assert manager.has_profile(
        "student-001"
    )

    retrieved = manager.get_profile(
        "student-001"
    )

    assert retrieved is profile


def test_profile_context():

    from alternia.learner.manager import (
        LearnerManager,
    )

    manager = LearnerManager()

    profile = manager.create_profile(
        student_id="student-001",
        student_class="10eme",
    )

    profile.current_subject = (
        "mathematiques"
    )

    profile.current_topic = (
        "équations"
    )

    profile.mastered_topics.append(
        "calcul littéral"
    )

    profile.topics_to_review.append(
        "fractions"
    )

    context = manager.build_profile_context(
        "student-001"
    )

    assert "10eme" in context

    assert "mathematiques" in context

    assert "équations" in context

    assert "calcul littéral" in context

    assert "fractions" in context