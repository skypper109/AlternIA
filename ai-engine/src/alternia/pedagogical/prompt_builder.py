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
        "Tu es ALTA, le tuteur pédagogique d'AlternIA pour le secondaire au Mali.\n\n"
        "RÈGLES IMPÉRATIVES ET ABSOLUES :\n"
        "1. LANGUE STRICTEMENT FRANÇAISE : Tu DOIS répondre TOUJOURS ET CATÉGORIQUEMENT EN FRANÇAIS. Aucune autre langue (anglais, etc.) n'est autorisée, SAUF si la question porte expressément sur la matière 'Anglais' du programme scolaire. Même pour les questions scientifiques, informatiques ou générales, réponds UNIQUEMENT en français pur.\n"
        "2. NOTIONS HORS PROGRAMME : Si l'élève pose une question sur un mot, une notion ou un concept qui ne figure pas au programme officiel de sa classe, commence par lui préciser avec bienveillance que cette notion ne fait pas partie du programme de sa classe, puis explique-lui ce que cela signifie brièvement et simplement en 1 à 2 phrases claires en français.\n"
        "3. PÉDAGOGIE : Réponds de manière concise (2 à 4 phrases), structurée, encourageante et rigoureusement adaptée au niveau scolaire de l'élève au Mali."
    )

    @classmethod
    def detect_question_guidance(cls, question: str) -> str | None:
        """Détecte l'intention structurelle de la question et fournit une consigne didactique impérative."""
        if not question:
            return None
        q = question.strip().lower()

        # 1. Salutations / Politesse / Présentation
        if re.search(r"^(bonjour|bonsoir|salut|qui es-tu|qui est-tu|présente-toi|presente toi|qui t'a créé)", q):
            return "Présente-toi brièvement et chaleureusement comme ALTA, le tuteur d'AlternIA, et propose ton aide sur une matière."

        # 2. Questions fermées (Oui / Non / Vrai / Faux)
        closed_pattern = r"^(est-ce que|est ce que|est-il|est-elle|est il|est elle|peut-on|peut on|faut-il|faut il|a-t-on|a t on|existe-t-il|existe t il|es-tu|es tu|peux-tu|peux tu|vrai ou faux|y a-t-il|y a t il|doit-on|doit on|sont-ils|sont-elles)"
        if re.search(closed_pattern, q) or q.startswith("est ce ") or q.startswith("est-ce "):
            return "Commence par Oui/Non/Vrai/Faux dès le 1er mot puis justifie en 1 à 2 phrases selon le cours."

        # 3. Définition directe / "C'est quoi" / Définir
        def_pattern = r"(c'est quoi|qu'est-ce que|qu'est ce que|définis|definis|définition de|definition de|définir|definir|qu'entend-on par|que signifie|veut dire)"
        if re.search(def_pattern, q):
            return "Donne la définition officielle exacte et concise du programme dès la 1ère phrase."

        # 4. Énoncé de Loi / Théorème / Propriété / Règle
        law_pattern = r"(énonce|enonce|énoncer|enoncer|loi de|théorème de|theoreme de|principe de|règle de|regle de|propriété de|propriete de)"
        if re.search(law_pattern, q):
            return "Énonce rigoureusement la loi ou le théorème officiel du programme avec ses conditions d'application."

        # 5. Formule mathématique / Relation physique / Équation
        calc_pattern = r"(formule de|formule pour|comment calculer|quelle est la formule|relation entre|équation de|equation de|équation-bilan|equation-bilan|formule brute|formule générale|valeur de)"
        if re.search(calc_pattern, q):
            return "Donne la formule mathématique/scientifique officielle en explicitant chaque terme et les unités SI."

        # 6. Méthode / Démarche de résolution / "Comment faire"
        method_pattern = r"(comment faire|comment résoudre|comment resoudre|méthode pour|methode pour|étapes pour|etapes pour|comment trouver|comment déterminer|comment determiner|comment montrer|comment prouver|comment équilibrer|comment equilibrer|comment dériver|comment deriver)"
        if re.search(method_pattern, q):
            return "Donne la démarche méthodique étape par étape de façon numérotée et limpide."

        # 7. Comparaison / Distinction / Différence
        comp_pattern = r"(différence|difference|différencier|differencier|distinguer|distinction|comparer|comparaison|par rapport à|par rapport a|versus|\bvs\b|points communs)"
        if re.search(comp_pattern, q):
            return "Distingue clairement les deux notions selon le programme officiel en soulignant leurs critères différentiels."

        # 8. Rôle / Fonction / Utilité / "À quoi sert"
        role_pattern = r"(à quoi sert|a quoi sert|quel est le rôle|quel est le role|quelle est la fonction|pourquoi utilise-t-on|pourquoi utilise t on|quelle est l'utilité|quelle est l'utilite|importance de)"
        if re.search(role_pattern, q):
            return "Explique le rôle principal et l'utilité concrète de la notion dans le cours en 1 à 2 phrases."

        # 9. Cause / Effet / "Pourquoi" / Conséquence
        cause_pattern = r"(\bpourquoi\b|quelles sont les causes|cause de|origine de|conséquence de|consequence de|quel est l'impact|qu'est-ce qui provoque|qu'est ce qui provoque)"
        if re.search(cause_pattern, q):
            return "Explique la cause scientifique/historique fondamentale et ses conséquences directes."

        # 10. Structure / Composition / Schéma / "De quoi est fait"
        struct_pattern = r"(de quoi est composé|de quoi est compose|composition de|structure de|de quoi est fait|quels sont les éléments|quels sont les elements|quelles sont les parties|schéma de|schema de|anatomie)"
        if re.search(struct_pattern, q):
            return "Énumère les composants essentiels et leur organisation selon le manuel officiel."

        # 11. Histoire / Biographie / Événement / Date (Histoire-Géo du Mali et du Monde)
        hist_pattern = r"(qui était|qui etait|qui est|qui a fait|en quelle année|en quelle annee|quand a eu lieu|où s'est déroulé|ou s'est deroule|raconte|biographie de|quel événement|quel evenement)"
        if re.search(hist_pattern, q):
            return "Précise le personnage, la date/période clé et l'impact historique majeur selon le programme malien."

        # 12. Exemple concret / Illustration
        example_pattern = r"(donne un exemple|donne-moi un exemple|donne moi un exemple|exemple de|illustre|illustration|cas concret|application pratique)"
        if re.search(example_pattern, q):
            return "Fournis un exemple scolaire concret et typique du programme officiel."

        # 13. Vulgarisation / Simplification
        child_pattern = r"(comme un enfant|à un enfant|a un enfant|vulgaris|plus simple|simplement|facilement|pour un enfant|en mots simples)"
        if re.search(child_pattern, q):
            return "Explique avec des mots simples et une analogie concrète de la vie courante."

        # 14. Demandes d'approfondissement / réexplication détaillée
        reexplain_pattern = r"(réexplique|reexplique|en détail|en detail|approfondir|développe|developpe|plus de détails|plus de details|plus d'explication)"
        if re.search(reexplain_pattern, q):
            return "Décompose le mécanisme étape par étape avec rigueur didactique."

        # 15. Méthodologie d'examen / Baccalauréat
        exam_pattern = r"(au bac|pour le bac|sujet de bac|comment réviser|comment reviser|conseil pour|piège à éviter|piege a eviter|méthodologie|methodologie|dissertation|commentaire composé)"
        if re.search(exam_pattern, q):
            return "Donne les conseils méthodologiques officiels du Baccalauréat malien et les erreurs classiques à éviter."

        # 16. Exercice / Calcul / Résolution directe
        exercise_pattern = r"(résous|resous|exercice|aide-moi à résoudre|aide moi a resoudre|calcule|détermine|determine|factorise|développe l'expression)"
        if re.search(exercise_pattern, q):
            return "Guide la résolution : donne le résultat final exact et la justification étape par étape."

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

        # Insertion de l'historique récent (multi-tours fluide)
        if session_messages:
            for msg in session_messages[-6:]:
                role = "user" if getattr(msg, "role", "") == "student" else "assistant"
                content = getattr(msg, "content", "").strip()
                if role == "assistant" and len(content) > 600:
                    content = content[:600].rstrip() + "..."
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