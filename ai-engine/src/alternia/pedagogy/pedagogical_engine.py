from typing import Any

from alternia.pedagogy.intent import (
    IntentDetector,
    PedagogicalIntent,
)

from alternia.pedagogy.response import (
    PedagogicalResponse,
)


class PedagogicalEngine:
    """
    Moteur pédagogique central d'AlternIA.

    Il transforme une question d'élève et son contexte
    pédagogique en réponse structurée.

    Pour cette première version, le moteur ne dépend pas
    encore d'un LLM externe. Il prépare l'orchestration
    pédagogique et produit des réponses déterministes.
    """

    def __init__(
        self,
        intent_detector: IntentDetector | None = None,
    ):
        self.intent_detector = (
            intent_detector
            or IntentDetector()
        )

    def generate(
        self,
        question: str,
        context: Any,
        student_class: str,
        subject: str | None = None,
    ) -> PedagogicalResponse:

        intent = self.intent_detector.detect(
            question
        )

        sources = getattr(
            context,
            "sources",
            [],
        )

        context_text = getattr(
            context,
            "context_text",
            "",
        )

        answer = self._generate_answer(
            question=question,
            intent=intent,
            context_text=context_text,
        )

        should_ask_followup = (
            intent
            in {
                PedagogicalIntent.CONCEPT_EXPLANATION,
                PedagogicalIntent.REEXPLANATION,
            }
        )

        followup_question = None

        if should_ask_followup:
            followup_question = (
                "Veux-tu que je te donne "
                "un exemple pour mieux comprendre ?"
            )

        return PedagogicalResponse(
            answer=answer,
            intent=intent.value,
            student_class=student_class,
            subject=subject,
            sources=sources,
            should_ask_followup=should_ask_followup,
            followup_question=followup_question,
            metadata={
                "context_used": bool(
                    context_text.strip()
                ),
                "source_count": len(sources),
            },
        )

    def _generate_answer(
        self,
        question: str,
        intent: PedagogicalIntent,
        context_text: str,
    ) -> str:

        if intent == PedagogicalIntent.CONCEPT_EXPLANATION:
            return self._concept_answer(
                context_text
            )

        if intent == PedagogicalIntent.PROBLEM_SOLVING:
            return self._problem_answer(
                context_text
            )

        if intent == PedagogicalIntent.PRACTICE:
            return self._practice_answer(
                context_text
            )

        if intent == PedagogicalIntent.REEXPLANATION:
            return self._reexplanation_answer(
                context_text
            )

        if intent == PedagogicalIntent.CORRECTION:
            return self._correction_answer(
                context_text
            )

        if intent == PedagogicalIntent.REVISION:
            return self._revision_answer(
                context_text
            )

        return (
            "Je veux bien t'aider. "
            "Peux-tu préciser ta question ?"
        )

    @staticmethod
    def _concept_answer(
        context_text: str,
    ) -> str:

        if not context_text.strip():
            return (
                "Je peux t'expliquer ce concept, "
                "mais je n'ai pas encore trouvé "
                "de contenu pédagogique correspondant "
                "dans mes ressources."
            )

        return (
            "Voici ce que nous pouvons retenir "
            "à partir de ton cours :\n\n"
            + context_text
        )

    @staticmethod
    def _problem_answer(
        context_text: str,
    ) -> str:

        if not context_text.strip():
            return (
                "Je vais t'aider à résoudre le problème "
                "étape par étape."
            )

        return (
            "Commençons étape par étape.\n\n"
            + context_text
        )

    @staticmethod
    def _practice_answer(
        context_text: str,
    ) -> str:

        return (
            "Je vais te proposer un exercice adapté "
            "à ce que tu es en train d'apprendre.\n\n"
            + (
                context_text
                if context_text.strip()
                else "Aucune ressource pédagogique "
                     "spécifique n'a encore été trouvée."
            )
        )

    @staticmethod
    def _reexplanation_answer(
        context_text: str,
    ) -> str:

        if not context_text.strip():
            return (
                "Pas de problème. Je vais essayer "
                "de te l'expliquer d'une autre manière."
            )

        return (
            "D'accord. Reprenons autrement.\n\n"
            + context_text
        )

    @staticmethod
    def _correction_answer(
        context_text: str,
    ) -> str:

        return (
            "Regardons ta réponse ensemble "
            "et vérifions chaque étape.\n\n"
            + (
                context_text
                if context_text.strip()
                else "J'ai besoin de ta réponse "
                     "pour pouvoir la corriger."
            )
        )

    @staticmethod
    def _revision_answer(
        context_text: str,
    ) -> str:

        return (
            "Voici les éléments importants "
            "à retenir :\n\n"
            + (
                context_text
                if context_text.strip()
                else "Je n'ai pas encore trouvé "
                     "de contenu de révision correspondant."
            )
        )
