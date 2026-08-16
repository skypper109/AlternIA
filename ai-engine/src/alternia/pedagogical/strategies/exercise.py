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

            f"Classe : "
            f"{request.profile.student_class}\n"

            f"Matière : "
            f"{request.analysis.subject or 'non définie'}\n"

            f"Chapitre : "
            f"{request.analysis.chapter or 'non défini'}\n"

            f"Question : "
            f"{request.question}\n\n"

            "Contexte pédagogique :\n"
            f"{context}\n\n"

            "Objectif :\n"
            "Proposer un exercice adapté à la classe "
            "et aux notions présentes dans le contexte.\n\n"

            "Consignes :\n"
            "1. Utilise les notions présentes dans le "
            "contexte pédagogique.\n"
            "2. Adapte la difficulté au niveau de l'élève.\n"
            "3. Propose un exercice clair et progressif.\n"
            "4. Ne donne pas immédiatement la solution "
            "complète, sauf si elle est demandée."
        )

    @staticmethod
    def _without_context(
        request: PedagogicalRequest,
    ) -> str:

        return (
            "EXERCICE D'ENTRAÎNEMENT\n\n"

            f"Classe : "
            f"{request.profile.student_class}\n"

            f"Matière : "
            f"{request.analysis.subject or 'non définie'}\n"

            f"Question : "
            f"{request.question}\n\n"

            "Objectif :\n"
            "Proposer un exercice adapté au niveau "
            "de l'élève.\n\n"

            "Contexte :\n"
            "Je ne dispose pas encore d'un contexte "
            "pédagogique suffisant pour générer "
            "un exercice conforme au programme.\n\n"

            "Consigne :\n"
            "Un contexte pédagogique provenant du RAG "
            "est nécessaire pour proposer un exercice "
            "précisément aligné sur le programme."
        )