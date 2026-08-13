from typing import Any

from alternia.llm.client import LLMClient
from alternia.pedagogy.pedagogical_engine import PedagogicalEngine
from alternia.validation.validator import (
    PedagogicalResponseValidator,
)

class AlterniaOrchestrator:
    """
    Orchestre le pipeline principal d'AlternIA.

    Pipeline :

        question
            ↓
        RAG / contexte
            ↓
        moteur pédagogique
            ↓
        LLM
            ↓
        réponse finale
    """

    def __init__(
        self,
        pedagogical_engine: PedagogicalEngine,
        llm_client: LLMClient,
        validator: PedagogicalResponseValidator | None = None,
    ):
        self.pedagogical_engine = pedagogical_engine
        self.llm_client = llm_client
        self.validator = (
            validator
            or PedagogicalResponseValidator()
        )

    def ask(
        self,
        question: str,
        context: Any,
        student_class: str,
        subject: str | None = None,
    ):

        # -------------------------------------------------
        # 1. Analyse pédagogique
        # -------------------------------------------------

        pedagogical_response = (
            self.pedagogical_engine.generate(
                question=question,
                context=context,
                student_class=student_class,
                subject=subject,
            )
        )

        # -------------------------------------------------
        # 2. Construction du prompt
        # -------------------------------------------------

        prompt = self._build_prompt(
            question=question,
            pedagogical_response=pedagogical_response,
            context=context,
        )

        # -------------------------------------------------
        # 3. Génération LLM
        # -------------------------------------------------

        answer = self.llm_client.generate(
            prompt,
            system_prompt=self._system_prompt(),
        )
        answer = self.validator.validate(
            answer,
            question=question,
            context=context,
        )

        # -------------------------------------------------
        # 4. Retour structuré
        # -------------------------------------------------

        return {
            "answer": answer,
            "intent": pedagogical_response.intent,
            "student_class": student_class,
            "subject": subject,
            "sources": pedagogical_response.sources,
            "should_ask_followup": (
                pedagogical_response.should_ask_followup
            ),
            "followup_question": (
                pedagogical_response.followup_question
            ),
            "metadata": {
                **pedagogical_response.metadata,
                "llm_used": True,
            },
        }

    @staticmethod
    def _system_prompt() -> str:
        return (
            "Tu es AlternIA, un assistant pédagogique "
            "destiné aux élèves. "
            "Tu expliques les notions simplement, "
            "progressivement et avec bienveillance. "
            "Tu adaptes toujours ton explication au niveau "
            "de l'élève. "
            "Tu ne dois pas inventer de contenu présenté "
            "comme provenant du cours lorsque le contexte "
            "fourni ne le permet pas."
        )

    @staticmethod
    def _build_prompt(
        question: str,
        pedagogical_response: Any,
        context: Any,
    ) -> str:

        context_text = getattr(
            context,
            "context_text",
            "",
        )

        return (
            "QUESTION DE L'ÉLÈVE\n"
            f"{question}\n\n"

            "INTENTION PÉDAGOGIQUE\n"
            f"{pedagogical_response.intent}\n\n"

            "CLASSE\n"
            f"{pedagogical_response.student_class}\n\n"

            "MATIÈRE\n"
            f"{pedagogical_response.subject or 'non définie'}\n\n"

            "CONTEXTE PÉDAGOGIQUE\n"
            f"{context_text or 'Aucun contexte disponible.'}\n\n"

            "INSTRUCTION\n"
            "Réponds directement à l'élève. "
            "Utilise le contexte pédagogique lorsqu'il "
            "est disponible. "
            "Explique de manière claire et adaptée."
        )
