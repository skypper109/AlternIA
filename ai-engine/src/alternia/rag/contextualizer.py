import re
from typing import Any


class QueryContextualizer:
    """
    Contextualise intelligemment les requêtes de suivi pour la recherche sémantique RAG.
    
    Permet de résoudre les anaphores ("son", "sa", "ce", "cette"), les demandes
    de réexplication ("réexplique en détail") et les questions elliptiques ("en biologie", "et pour X ?").
    """

    STOP_PHRASES = [
        r"^(c'est quoi|qu'est-ce que|qu'est ce que|qu'est-ce qu'|qu'est ce qu')",
        r"^(peux-tu m'expliquer|explique-moi|explique moi|parle-moi de|parle moi de)",
        r"^(donne-moi|donne moi|c'est quoi la définition de)",
        r"^(réexplique-moi|reexplique-moi|réexplique moi|reexplique moi|réexplique|reexplique)",
        r"^(en détail|en detail|de manière détaillée|plus d'explication|plus de détails)",
        r"^(est-ce que|est ce que|est-il|est il|peut-on|peut on|doit-on|doit on)",
        r"^(s'il te plaît|stp|s'il vous plaît|svp)",
    ]

    FOLLOW_UP_TRIGGERS = [
        "reexplique", "réexplique", "detail", "détail", "exemple", "pourquoi",
        "ensuite", "différence", "c'est-à-dire", "comment", "importance", "rôle",
        "role", "fonction", "cause", "conséquence", "consequence", "propriété",
        "propriete", "structure", "formule", "schéma", "schema", "son", "sa",
        "ses", "leurs", "leur", "aussi", "encore", "plus", "autre",
    ]

    @classmethod
    def clean_core_terms(cls, text: str) -> str:
        """Extrait les termes substantiels d'une question en retirant les formules introductives."""
        cleaned = text.strip()
        for pat in cls.STOP_PHRASES:
            cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"[?!.,;:«»\"']", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    @classmethod
    def is_follow_up(cls, question: str) -> bool:
        """Détermine si la question est une relance ou une question elliptique dépendante du contexte."""
        q = question.strip().lower()
        words = q.split()
        if len(words) <= 4:
            return True
        return any(trig in q for trig in cls.FOLLOW_UP_TRIGGERS)

    @classmethod
    def contextualize(
        cls,
        current_question: str,
        past_student_messages: list[str] | None = None,
        current_topic: str | None = None,
    ) -> str:
        """
        Génère une requête RAG enrichie et débarrassée du bruit conversationnel.
        """
        curr_clean = cls.clean_core_terms(current_question)
        if not past_student_messages and not current_topic:
            return current_question.strip()

        if not cls.is_follow_up(current_question):
            return current_question.strip()

        # Récupération du sujet précédent
        prev_topic = ""
        if current_topic:
            prev_topic = current_topic.strip()
        elif past_student_messages:
            for past_msg in reversed(past_student_messages):
                extracted = cls.clean_core_terms(past_msg)
                if len(extracted.split()) >= 1 and extracted.lower() not in {"quit", "aide", "/aide", "/classe", "merci", "salut", "bonjour"}:
                    prev_topic = extracted
                    break

        if not prev_topic:
            return current_question.strip()

        # Si l'élève demande juste "réexplique en détail" ou "donne un exemple"
        q_lower = current_question.strip().lower()
        if any(w in q_lower for w in ["reexplique", "réexplique", "detail", "détail", "encore"]):
            return f"{prev_topic} explication cours définition"

        # Si l'élève demande l'importance / rôle / structure
        if any(w in q_lower for w in ["importance", "rôle", "role", "fonction", "but"]):
            return f"{prev_topic} rôle importance définition"

        # Question de comparaison ou précision
        return f"{prev_topic} {curr_clean}".strip()
