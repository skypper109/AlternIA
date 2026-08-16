from alternia.learner.evaluator import (
    LearningEvaluation,
    LearningEvaluator,
)
from alternia.learner.manager import (
    LearnerManager,
)
from alternia.learner.models import (
    LearningInteraction,
)


class LearningAssessmentService:
    """
    Service central d'évaluation de l'apprentissage.

    Responsabilités :

    1. évaluer la réponse de l'élève ;
    2. enregistrer le résultat ;
    3. mettre à jour la progression de la notion ;
    4. retourner l'évaluation pédagogique.
    """

    def __init__(
        self,
        learner_manager: LearnerManager,
        evaluator: LearningEvaluator | None = None,
    ):
        self.learner_manager = (
            learner_manager
        )

        self.evaluator = (
            evaluator
            or LearningEvaluator()
        )

    def assess(
        self,
        *,
        student_id: str,
        interaction: LearningInteraction,
        expected_answer: str,
        student_answer: str,
    ) -> LearningEvaluation:
        """
        Évalue une tentative et l'enregistre
        dans le profil apprenant.
        """

        evaluation = self.evaluator.evaluate(
            expected_answer=expected_answer,
            student_answer=student_answer,
        )

        interaction.success = (
            evaluation.success
        )

        self.learner_manager.register_interaction(
            student_id=student_id,
            interaction=interaction,
        )

        return evaluation