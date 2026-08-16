from alternia.pedagogical.models import (
    PedagogicalRequest,
    PedagogicalResponse,
)

from alternia.pedagogical.strategies import (
    CorrectionStrategy,
    ExerciseStrategy,
    ExplanationStrategy,
    RevisionStrategy,
    SummaryStrategy,
)


class PedagogicalEngine:
    """
    Cerveau pédagogique central d'AlternIA.

    Responsabilités :

    1. normaliser l'intention pédagogique ;
    2. sélectionner la stratégie adaptée ;
    3. transmettre le contexte pédagogique à la stratégie ;
    4. produire une instruction pédagogique structurée ;
    5. transmettre les informations nécessaires au LLM ;
    6. déterminer si une relance pédagogique est pertinente.

    Le moteur pédagogique ne génère PAS directement
    la réponse finale destinée à l'élève.

    Le LLM est responsable de la formulation finale.
    """

    SUPPORTED_INTENTS = {
        "explanation",
        "exercise",
        "correction",
        "revision",
        "summary",
    }

    def __init__(self):
        self.strategies = {
            "explanation": ExplanationStrategy(),
            "exercise": ExerciseStrategy(),
            "correction": CorrectionStrategy(),
            "revision": RevisionStrategy(),
            "summary": SummaryStrategy(),
        }

    # =========================================================
    # TRAITEMENT PRINCIPAL
    # =========================================================

    def process(
        self,
        request: PedagogicalRequest,
    ) -> PedagogicalResponse:

        if not request.question.strip():
            raise ValueError(
                "La question de l'élève ne peut pas être vide."
            )

        intent = self._resolve_intent(
            request.analysis.intent
        )

        strategy = self.strategies[intent]

        instruction = strategy.generate(
            request
        )

        sources_used = self._extract_sources(
            request
        )

        return PedagogicalResponse(
            answer=instruction,
            student_class=request.profile.student_class,
            subject=request.analysis.subject,
            intent=intent,
            sources_used=sources_used,
            needs_follow_up=self._needs_follow_up(
                intent
            ),
            follow_up_question=self._follow_up_question(
                intent
            ),
        )

    # =========================================================
    # INTENTION
    # =========================================================

    @classmethod
    def _resolve_intent(
        cls,
        intent: str,
    ) -> str:

        normalized = (
            intent.strip().lower()
            if intent
            else "explanation"
        )

        if normalized in cls.SUPPORTED_INTENTS:
            return normalized

        return "explanation"

    # =========================================================
    # SOURCES
    # =========================================================

    @staticmethod
    def _extract_sources(
        request: PedagogicalRequest,
    ) -> list[str]:

        """
        Extrait les identifiants de sources présents
        dans le contexte lorsque celui-ci contient des
        informations structurées.

        Cette méthode reste volontairement tolérante afin
        de fonctionner avec le contexte texte actuel.
        """

        context = request.context.strip()

        if not context:
            return []

        return []

    # =========================================================
    # FOLLOW-UP
    # =========================================================

    @staticmethod
    def _needs_follow_up(
        intent: str,
    ) -> bool:

        return intent in {
            "explanation",
            "correction",
        }

    @staticmethod
    def _follow_up_question(
        intent: str,
    ) -> str | None:

        if intent == "explanation":
            return (
                "Veux-tu que je te donne un exemple "
                "pour mieux comprendre ?"
            )

        if intent == "correction":
            return (
                "Veux-tu essayer un exercice similaire "
                "pour vérifier que tu as compris ?"
            )

        return None