from alternia.pedagogical.models import PedagogicalRequest


class ExerciseStrategy:
    """
    Stratégie utilisée lorsqu'un élève demande
    un exercice ou souhaite s'entraîner.
    """

    name = "exercise"

    def generate(
        self,
        request: PedagogicalRequest,
    ) -> str:

        context = request.context.strip()

        if not context:
            return self._without_context(request)

        return self._with_context(
            request,
            context,
        )

    @staticmethod
    def _with_context(
        request: PedagogicalRequest,
        context: str,
    ) -> str:

        return (
            "EXERCICE D'ENTRAÎNEMENT\n\n"
            f"Classe : {request.profile.student_class}\n"
            f"Matière : "
            f"{request.analysis.subject or 'non définie'}\n"
            f"Chapitre : "
            f"{request.analysis.chapter or 'non défini'}\n\n"
            "Notions utilisées :\n"
            f"{context}\n\n"
            "À partir de ces notions, un exercice "
            "adapté au niveau de l'élève doit être proposé."
        )

    @staticmethod
    def _without_context(
        request: PedagogicalRequest,
    ) -> str:

        return (
            "EXERCICE D'ENTRAÎNEMENT\n\n"
            f"Classe : {request.profile.student_class}\n"
            f"Matière : "
            f"{request.analysis.subject or 'non définie'}\n\n"
            "Je ne dispose pas encore d'un contexte "
            "pédagogique suffisant pour générer "
            "un exercice conforme au programme."
        )
