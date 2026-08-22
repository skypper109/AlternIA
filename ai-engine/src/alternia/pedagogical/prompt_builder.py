import re
import time
from typing import Any
from alternia.pedagogical.models import PedagogicalRequest
from alternia.pedagogical.curriculum_scope import CurriculumScopeChecker


class PedagogicalPromptBuilder:
    """
    Construit le prompt final et les messages de conversation multi-tours pour le LLM.
    Optimisé pour une latence minimale sur Raspberry Pi 4/5 et processeurs embarqués.
    """

    SYSTEM_PROMPT = (
        "Tu es ALTA, tuteur pédagogique d'AlternIA pour le secondaire au Mali.\n"
        "RÈGLES : Réponds directement en 2 à 4 phrases claires en français, fondé sur le cours officiel. Pas de bavardage."
    )

    @classmethod
    def detect_question_guidance(cls, question: str) -> str | None:
        """Détecte l'intention structurelle de la question et fournit une consigne impérative."""
        q = question.strip().lower()

        # Questions fermées (Oui / Non / Vrai / Faux)
        closed_pattern = r"^(est-ce que|est ce que|est-il|est-elle|est il|est elle|peut-on|peut on|faut-il|faut il|a-t-on|a t on|existe-t-il|existe t il|es-tu|es tu|peux-tu|peux tu|vrai ou faux|y a-t-il|y a t il|doit-on|doit on|sont-ils|sont-elles)"
        if re.search(closed_pattern, q) or q.startswith("est ce ") or q.startswith("est-ce "):
            return "Commence par Oui/Non/Vrai/Faux dès le 1er mot puis justifie en 1 à 2 phrases selon le cours."

        # Questions de comparaison / distinction
        comp_pattern = r"(différence|différencier|distinguer|distinction|comparer|comparaison|par rapport à|versus|\bvs\b)"
        if re.search(comp_pattern, q):
            return "Distingue clairement les deux notions selon le programme officiel."

        # Demandes d'approfondissement / réexplication
        reexplain_pattern = r"(réexplique|reexplique|en détail|en detail|approfondir|développe|developpe|pourquoi|donne un exemple|plus de détails|plus d'explication)"
        if re.search(reexplain_pattern, q):
            return "Fournis un exemple concret ou décompose le mécanisme étape par étape."

        # Vulgarisation / Enfant
        child_pattern = r"(comme un enfant|à un enfant|a un enfant|vulgaris|plus simple|simplement|facilement|pour un enfant)"
        if re.search(child_pattern, q):
            return "Explique très simplement avec une analogie de la vie courante."

        # Formule ou calcul
        calc_pattern = r"(formule de|comment calculer|quelle est la formule|calculer|équation de|valeur de)"
        if re.search(calc_pattern, q):
            return "Donne la formule officielle avec unités SI."

        return None

    def build_messages(
        self,
        request: PedagogicalRequest,
        strategy_instruction: str,
        session_messages: list[Any] | None = None,
        scope_result: Any = None,
    ) -> list[dict[str, str]]:
        """
        Construit une séquence de messages multi-tours native (ChatML) ultra-compacte.
        """
        t0 = time.perf_counter()
        profile = request.profile
        analysis = request.analysis
        context = request.context.strip()

        if scope_result is None:
            scope_checker = CurriculumScopeChecker()
            scope_result = scope_checker.check_scope(
                question=request.question,
                student_class=profile.student_class,
                subject=analysis.subject,
            )

        series_label = f" {profile.series}" if getattr(profile, "series", None) else ""
        system_content = f"{self.system_prompt()}\nNiveau : {profile.student_class}{series_label} | {analysis.subject or 'Général'}"

        if scope_result.is_higher_level and scope_result.pedagogical_guidance:
            system_content += f"\n{scope_result.pedagogical_guidance.strip()}"

        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_content}
        ]

        # Insertion de l'historique récent (élagué pour économiser les tokens)
        if session_messages:
            for msg in session_messages[-2:]:
                role = "user" if getattr(msg, "role", "") == "student" else "assistant"
                content = getattr(msg, "content", "").strip()
                if role == "assistant" and len(content) > 150:
                    content = content[:150].rstrip() + "..."
                if content:
                    messages.append({"role": role, "content": content})

        # Construction du message utilisateur avec le contexte RAG ciblé
        user_parts = []
        if context:
            user_parts.append(f"EXTRAITS DU COURS :\n{context}")

        specific_guidance = self.detect_question_guidance(request.question)
        if specific_guidance:
            user_parts.append(f"CONSIGNE : {specific_guidance}")

        user_parts.append(f"QUESTION : {request.question.strip()}")
        messages.append({"role": "user", "content": "\n\n".join(user_parts)})

        dt = time.perf_counter() - t0
        total_chars = sum(len(m.get("content", "")) for m in messages)
        print(f"\033[36m⏱️  [prompt_builder.py]\033[0m Messages ChatML compacts ({len(messages)} msgs, {total_chars} chars) en \033[1;33m{dt:.4f}s\033[0m")

        return messages

    def build(
        self,
        request: PedagogicalRequest,
        strategy_instruction: str,
    ) -> str:
        t0 = time.perf_counter()
        profile = request.profile
        analysis = request.analysis
        context = request.context.strip()
        conv_ctx = request.conversation_context.strip()

        scope_checker = CurriculumScopeChecker()
        scope_result = scope_checker.check_scope(
            question=request.question,
            student_class=profile.student_class,
            subject=analysis.subject,
        )

        parts = []

        # 1. Historique des échanges précédents (mémoire conversationnelle)
        if conv_ctx:
            parts.append(conv_ctx)

        # 2. Informations de classe et matière
        series_label = f" (Série : {profile.series})" if getattr(profile, "series", None) else ""
        parts.append(f"NIVEAU SCOLAIRE : Classe de {profile.student_class}{series_label} | Matière : {analysis.subject or 'Général'}")

        # 3. Cadrage curriculaire si dépassement de niveau
        if scope_result.is_higher_level and scope_result.pedagogical_guidance:
            parts.append(scope_result.pedagogical_guidance.strip())

        # 4. Extraits du cours (RAG) avec obligation d'usage
        if context:
            parts.append(f"EXTRAITS DU COURS OFFICIEL DU PROGRAMME MALIEN (RAG) :\n{context}")

        # 5. Directive de type de question
        specific_guidance = self.detect_question_guidance(request.question)
        if specific_guidance:
            parts.append(f"DIRECTIVE STRUCTURELLE :\n{specific_guidance}")

        # 6. Objectif didactique
        clean_strategy = strategy_instruction.split("Contexte pédagogique :")[0].strip() if strategy_instruction else ""
        if clean_strategy:
            parts.append(f"OBJECTIF DIDACTIQUE :\n{clean_strategy}")

        # 7. Question actuelle posée par l'élève
        parts.append(f"QUESTION DE L'ÉLÈVE :\n{request.question.strip()}")

        parts.append("RÉPONSE D'ALTA (en FRANÇAIS exclusivement, fondée sur le cours officiel malien ci-dessus, réponds directement sans salutation ni triple astérisque '***') :")
        full_prompt = "\n\n".join(parts)

        dt = time.perf_counter() - t0
        print(f"\033[36m⏱️  [prompt_builder.py]\033[0m Prompt texte brut assemblé ({len(full_prompt)} chars) en \033[1;33m{dt:.4f}s\033[0m")
        return full_prompt

    @classmethod
    def system_prompt(cls) -> str:
        return cls.SYSTEM_PROMPT