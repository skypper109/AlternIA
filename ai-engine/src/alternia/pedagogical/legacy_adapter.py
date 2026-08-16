from types import SimpleNamespace
from typing import Any

from alternia.pedagogy.intent import (
    IntentDetector,
    PedagogicalIntent,
)

from alternia.pedagogical.engine import PedagogicalEngine
from alternia.pedagogical.models import (
    PedagogicalRequest,
    PedagogicalResponse,
    QuestionAnalysis,
    StudentProfile,
)


class PedagogicalEngineAdapter:
    """
    Adaptateur entre l'ancienne interface de l'orchestrateur
    et le nouveau moteur pédagogique.
    """

    def __init__(
        self,
        engine: PedagogicalEngine | None = None,
        intent_detector: IntentDetector | None = None,
    ):
        self.engine = engine or PedagogicalEngine()

        self.intent_detector = (
            intent_detector
            or IntentDetector()
        )

    def process(
        self,
        request: PedagogicalRequest,
    ) -> PedagogicalResponse:
        """
        Délègue directement au moteur pédagogique standard.
        """
        return self.engine.process(request)


    # =========================================================
    # API COMPATIBLE AVEC L'ANCIEN ORCHESTRATEUR
    # =========================================================

    def generate(
        self,
        question: str,
        context: Any,
        student_class: str,
        subject: str | None = None,
        profile=None,
    ):
        """
        Transforme l'ancienne requête en PedagogicalRequest.
        """

        context_text = self._extract_context(
            context
        )

        intent = self._resolve_intent(
            question
        )

        profile = (
            profile
            if profile is not None
            else StudentProfile(
                student_class=student_class,
            )
        )

        request = PedagogicalRequest(
            question=question,

            profile=profile,

            analysis=QuestionAnalysis(
                original_question=question,
                intent=intent,
                student_class=student_class,
                subject=subject,
            ),

            context=context_text,
        )

        response = self.engine.process(
            request
        )

        sources = self._extract_sources(
            context
        )

        return SimpleNamespace(
            answer=response.answer,

            intent=response.intent,

            student_class=(
                response.student_class
            ),

            subject=response.subject,

            sources=sources,

            should_ask_followup=(
                response.needs_follow_up
            ),

            followup_question=(
                response.follow_up_question
            ),

            metadata={
                "context_used": bool(
                    context_text.strip()
                ),

                "source_count": len(
                    sources
                ),

                "pedagogical_engine": (
                    "alternia.pedagogical"
                ),

                "intent_detector": (
                    "alternia.pedagogy"
                ),
            },
        )
    # =========================================================
    # INTENTION
    # =========================================================

    def _resolve_intent(
        self,
        question: str,
    ) -> str:
        """
        Utilise l'IntentDetector central d'AlternIA.

        Conversion :

            concept_explanation
                → explanation

            problem_solving
                → explanation

            practice
                → exercise

            reexplanation
                → explanation

            correction
                → correction

            revision
                → revision

            unknown
                → explanation
        """

        detected = self.intent_detector.detect(
            question
        )

        mapping = {
            PedagogicalIntent.CONCEPT_EXPLANATION:
                "explanation",

            PedagogicalIntent.PROBLEM_SOLVING:
                "explanation",

            PedagogicalIntent.PRACTICE:
                "exercise",

            PedagogicalIntent.REEXPLANATION:
                "explanation",

            PedagogicalIntent.CORRECTION:
                "correction",

            PedagogicalIntent.REVISION:
                "revision",

            PedagogicalIntent.SUMMARY:
                "summary",

            PedagogicalIntent.UNKNOWN:
                "explanation",
        }

        return mapping.get(
            detected,
            "explanation",
        )

    # =========================================================
    # CONTEXTE
    # =========================================================

    @staticmethod
    def _extract_context(
        context: Any,
    ) -> str:

        if context is None:
            return ""

        if isinstance(context, str):
            return context.strip()

        return str(
            getattr(
                context,
                "context_text",
                "",
            )
        ).strip()

    # =========================================================
    # SOURCES
    # =========================================================

    @staticmethod
    def _extract_sources(
        context: Any,
    ) -> list:

        if context is None:
            return []

        return list(
            getattr(
                context,
                "sources",
                [],
            )
        )