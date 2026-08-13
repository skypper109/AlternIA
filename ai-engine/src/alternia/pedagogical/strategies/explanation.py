from alternia.pedagogical.models import PedagogicalRequest


class ExplanationStrategy:
    """
    Stratégie utilisée lorsqu'un élève demande
    une explication ou cherche à comprendre une notion.
    """

    name = "explanation"

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
            "EXPLICATION PÉDAGOGIQUE\n\n"
            f"Question : {request.question}\n\n"
            "Voici les éléments du programme "
            "correspondant à ta question :\n\n"
            f"{context}\n\n"
            "L'explication détaillée sera construite "
            "à partir de ces éléments."
        )

    @staticmethod
    def _without_context(
        request: PedagogicalRequest,
    ) -> str:

        return (
            "EXPLICATION PÉDAGOGIQUE\n\n"
            f"Question : {request.question}\n\n"
            "Je ne dispose pas encore d'un contexte "
            "pédagogique suffisant pour répondre "
            "précisément à cette question."
        )
