from alternia.pedagogical.models import PedagogicalRequest


class ExerciseStrategy:
    """
    Stratégie pédagogique utilisée lorsqu'un élève
    demande un exercice ou souhaite s'entraîner.
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
            f"Matière : {request.analysis.subject or 'non définie'}\n"
            f"Chapitre : {request.analysis.chapter or 'non défini'}\n"
            f"Question : {request.question}\n\n"
            f"Contexte pédagogique :\n{context}\n\n"
            "Objectif :\nProposer un exercice adapté à la classe et aux notions présentes dans le contexte."
        )

    @staticmethod
    def _without_context(
        request: PedagogicalRequest,
    ) -> str:
        return (
            "EXERCICE D'ENTRAÎNEMENT\n\n"
            f"Classe : {request.profile.student_class}\n"
            f"Matière : {request.analysis.subject or 'non définie'}\n"
            f"Question : {request.question}\n\n"
            "Objectif :\nProposer un exercice adapté au niveau de l'élève.\n\n"
            "Contexte :\nJe ne dispose pas encore d'un contexte pédagogique suffisant pour cette question spécifique."
        )