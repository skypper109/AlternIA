from alternia.pedagogical.models import (
    PedagogicalRequest,
    PedagogicalResponse,
)


class PedagogicalEngine:
    """
    Cerveau pédagogique d'AlternIA.

    Il reçoit une requête déjà enrichie par le contexte RAG
    et détermine la stratégie pédagogique à utiliser.
    """

    SUPPORTED_INTENTS = {
        "explanation",
        "exercise",
        "correction",
        "revision",
        "summary",
    }

    def process(
        self,
        request: PedagogicalRequest,
    ) -> PedagogicalResponse:

        intent = self._resolve_intent(
            request.analysis.intent
        )

        answer = self._build_placeholder_response(
            request,
            intent,
        )

        return PedagogicalResponse(
            answer=answer,
            student_class=request.profile.student_class,
            subject=request.analysis.subject,
            intent=intent,
        )

    def _resolve_intent(
        self,
        intent: str,
    ) -> str:

        normalized = (
            intent.strip().lower()
            if intent
            else "explanation"
        )

        if normalized in self.SUPPORTED_INTENTS:
            return normalized

        return "explanation"

    @staticmethod
    def _build_placeholder_response(
        request: PedagogicalRequest,
        intent: str,
    ) -> str:

        return (
            f"Stratégie pédagogique : {intent}\n"
            f"Classe : {request.profile.student_class}\n"
            f"Matière : "
            f"{request.analysis.subject or 'non définie'}\n"
            f"Question : {request.question}"
        )
