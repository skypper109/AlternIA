from alternia.learner.evaluator import (
    LearningEvaluator,
)


def test_evaluator_accepts_correct_answer():

    evaluator = LearningEvaluator()

    result = evaluator.evaluate(
        expected_answer="x = 5",
        student_answer="x = 5",
    )

    assert result.success is True
    assert result.score == 1.0


def test_evaluator_rejects_wrong_answer():

    evaluator = LearningEvaluator()

    result = evaluator.evaluate(
        expected_answer="x = 5",
        student_answer="x = 3",
    )

    assert result.success is False
    assert result.score == 0.0


def test_evaluator_handles_empty_answer():

    evaluator = LearningEvaluator()

    result = evaluator.evaluate(
        expected_answer="x = 5",
        student_answer="",
    )

    assert result.success is False
    assert result.score == 0.0
