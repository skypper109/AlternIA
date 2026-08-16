from dataclasses import dataclass


@dataclass(frozen=True)
class LearningEvaluation:
    """
    Résultat pédagogique d'une tentative élève.
    """

    success: bool

    score: float | None = None

    feedback: str | None = None


class LearningEvaluator:
    """
    Évalue le résultat pédagogique d'une tentative.

    Cette première version reste volontairement
    déterministe.

    Le LLM pourra être branché plus tard pour
    l'évaluation sémantique.
    """

    def evaluate(
        self,
        *,
        expected_answer: str,
        student_answer: str,
    ) -> LearningEvaluation:

        expected = (
            expected_answer
            .strip()
            .lower()
        )

        student = (
            student_answer
            .strip()
            .lower()
        )

        if not expected:
            raise ValueError(
                "La réponse attendue ne peut pas être vide."
            )

        if not student:
            return LearningEvaluation(
                success=False,
                score=0.0,
                feedback=(
                    "Aucune réponse n'a été fournie."
                ),
            )

        if student == expected:
            return LearningEvaluation(
                success=True,
                score=1.0,
                feedback=(
                    "Bonne réponse."
                ),
            )

        return LearningEvaluation(
            success=False,
            score=0.0,
            feedback=(
                "La réponse est incorrecte."
            ),
        )