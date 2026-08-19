import re
from typing import Any
from alternia.pedagogical.models import PedagogicalRequest
from alternia.pedagogical.curriculum_scope import CurriculumScopeChecker


class PedagogicalPromptBuilder:
    """
    Construit le prompt final et les messages de conversation multi-tours pour le LLM.
    Optimisé pour une latence minimale sur Raspberry Pi 4/5 et processeurs embarqués.
    """

    # System prompt compact et positif (~180 tokens) :
    # Élimine toute phrase négative modèle qui parasitait le début des réponses du LLM.
    SYSTEM_PROMPT = (
        "Tu es ALTA, tuteur pédagogique intelligent d'AlternIA pour les élèves du secondaire au Mali "
        "(10ème, 11ème, 12ème Terminale).\n"
        "RÈGLES STRICTES :\n"
        "1. LANGUE : Exprime-toi TOUJOURS et EXCLUSIVEMENT en FRANÇAIS pur. Jamais d'anglais, chinois, ni de balises '***'.\n"
        "2. ANCRAGE DU COURS : Appuie-toi RIGOUREUSEMENT sur les extraits du cours officiel fournis ci-dessous pour donner les définitions, formules et méthodes exactes.\n"
        "3. DIRECTIVITÉ ET CONCISION : Réponds DIRECTEMENT dès le premier mot en 2 à 4 phrases claires, denses et pédagogiques (50 à 80 mots). Pas de salutations répétitives ni de bavardage.\n"
        "4. QUESTIONS FERMÉES : Si l'élève pose une question fermée, commence par 'Oui', 'Non', 'Vrai' ou 'Faux' dès le premier mot puis justifie en 1 à 2 phrases.\n"
        "5. ADAPTATION : Adapte le vocabulaire et les méthodes au niveau scolaire indiqué.\n"
        "6. IDENTITÉ : Si demandé, présente-toi comme ALTA, le tuteur pédagogique d'AlternIA."
    )

    @classmethod
    def detect_question_guidance(cls, question: str) -> str | None:
        """Détecte l'intention structurelle de la question et fournit une consigne impérative."""
        q = question.strip().lower()

        # Questions fermées (Oui / Non / Vrai / Faux)
        closed_pattern = r"^(est-ce que|est ce que|est-il|est-elle|est il|est elle|peut-on|peut on|faut-il|faut il|a-t-on|a t on|existe-t-il|existe t il|es-tu|es tu|peux-tu|peux tu|vrai ou faux|y a-t-il|y a t il|doit-on|doit on|sont-ils|sont-elles)"
        if re.search(closed_pattern, q) or q.startswith("est ce ") or q.startswith("est-ce "):
            return "CONSIGNE QUESTION FERMÉE : Commence ta réponse par 'Oui', 'Non', 'Vrai' ou 'Faux' dès le premier mot, puis justifie précisément en 1 à 2 phrases selon le cours officiel."

        # Questions de comparaison / distinction
        comp_pattern = r"(différence|différencier|distinguer|distinction|comparer|comparaison|par rapport à|versus|\bvs\b)"
        if re.search(comp_pattern, q):
            return "CONSIGNE COMPARAISON : Structure clairement la distinction entre les notions en nommant les deux concepts et en précisant leurs critères distinctifs selon le programme scolaire officiel."

        # Demandes d'approfondissement / réexplication
        reexplain_pattern = r"(réexplique|reexplique|en détail|en detail|approfondir|développe|developpe|pourquoi|donne un exemple|plus de détails|plus d'explication)"
        if re.search(reexplain_pattern, q):
            return "CONSIGNE RÉEXPLICATION : L'élève demande d'approfondir. INTERDICTION STRICTE de répéter textuellement la réponse précédente. Fournis une analogie concrète, un exemple de la vie courante ou décompose le mécanisme étape par étape."

        # Vulgarisation / Enfant
        child_pattern = r"(comme un enfant|à un enfant|a un enfant|vulgaris|plus simple|simplement|facilement|pour un enfant)"
        if re.search(child_pattern, q):
            return "CONSIGNE VULGARISATION : L'élève demande une explication très simple. Utilise un ton chaleureux, des mots extrêmement simples et une métaphore évidente de la vie courante. NE SOIS PAS académique, sois très accessible."

        # Formule ou calcul
        calc_pattern = r"(formule de|comment calculer|quelle est la formule|calculer|équation de|valeur de)"
        if re.search(calc_pattern, q):
            return "CONSIGNE FORMULE : Donne directement la formule officielle du cours avec la signification des lettres et les unités du Système International (SI)."

        # Demande directe de notion / mot-clé isolé (ex: "la photosynthèse", "photosynthèse", "sociologie végétale")
        words = q.split()
        if len(words) <= 5 and not any(w in q for w in ["exercice", "résoudre", "pourquoi", "quand", "aide"]):
            return "CONSIGNE NOTION DU COURS : Définis cette notion très simplement avec tes propres mots en t'appuyant sur le cours. Ne fais pas de longues listes. Si possible, donne un exemple très court pour illustrer."

        return None

    def build_messages(
        self,
        request: PedagogicalRequest,
        strategy_instruction: str,
        session_messages: list[Any] | None = None,
    ) -> list[dict[str, str]]:
        """
        Construit une séquence de messages multi-tours native (ChatML / OpenAI format)
        avec ancrage fort du RAG et contraintes linguistiques strictes.
        """
        profile = request.profile
        analysis = request.analysis
        context = request.context.strip()

        scope_checker = CurriculumScopeChecker()
        scope_result = scope_checker.check_scope(
            question=request.question,
            student_class=profile.student_class,
            subject=analysis.subject,
        )

        system_parts = [self.system_prompt()]

        series_label = f" (Série : {profile.series})" if getattr(profile, "series", None) else ""
        system_parts.append(f"NIVEAU SCOLAIRE DE L'ÉLÈVE : Classe de {profile.student_class}{series_label} | Matière : {analysis.subject or 'Général'}")

        if scope_result.is_higher_level and scope_result.pedagogical_guidance:
            system_parts.append(f"CADRAGE PÉDAGOGIQUE : {scope_result.pedagogical_guidance.strip()}")

        clean_strategy = strategy_instruction.split("Contexte pédagogique :")[0].strip() if strategy_instruction else ""
        if clean_strategy:
            system_parts.append(f"OBJECTIF PÉDAGOGIQUE :\n{clean_strategy}")

        messages: list[dict[str, str]] = [
            {"role": "system", "content": "\n\n".join(system_parts)}
        ]

        # Insertion de l'historique multi-tours natif
        if session_messages:
            for msg in session_messages:
                role = "user" if getattr(msg, "role", "") == "student" else "assistant"
                content = getattr(msg, "content", "").strip()
                if content:
                    messages.append({"role": role, "content": content})

        # Construction du message utilisateur avec le contexte RAG ancré
        user_parts = []
        if context:
            user_parts.append(f"EXTRAITS DU COURS OFFICIEL DU PROGRAMME MALIEN (RAG) :\n{context}")

        specific_guidance = self.detect_question_guidance(request.question)
        if specific_guidance:
            user_parts.append(f"DIRECTIVE DE STRUCTURE : {specific_guidance}")

        user_parts.append(f"QUESTION DE L'ÉLÈVE :\n{request.question.strip()}")

        if context:
            user_parts.append("Réponds en t'appuyant strictement sur les extraits du cours officiel fournis ci-dessus.")

        messages.append({"role": "user", "content": "\n\n".join(user_parts)})

        return messages

    def build(
        self,
        request: PedagogicalRequest,
        strategy_instruction: str,
    ) -> str:
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
        return "\n\n".join(parts)

    @classmethod
    def system_prompt(cls) -> str:
        return cls.SYSTEM_PROMPT