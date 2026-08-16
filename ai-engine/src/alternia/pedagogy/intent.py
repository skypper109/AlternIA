from enum import Enum


class PedagogicalIntent(str, Enum):
    """
    Intention pédagogique détectée dans la question
    de l'élève.
    """

    CONCEPT_EXPLANATION = "concept_explanation"

    PROBLEM_SOLVING = "problem_solving"

    PRACTICE = "practice"

    REEXPLANATION = "reexplanation"

    CORRECTION = "correction"

    REVISION = "revision"

    SUMMARY = "summary"

    UNKNOWN = "unknown"


class IntentDetector:
    """
    Détecte l'intention pédagogique principale
    exprimée dans la question de l'élève.

    L'ordre des règles est volontaire :
    certaines intentions sont prioritaires lorsqu'une
    même question contient plusieurs mots-clés.

    Priorité :

    1. correction
    2. exercice / entraînement
    3. réexplication
    4. résolution de problème
    5. résumé
    6. révision
    7. explication de concept
    8. inconnue
    """

    def detect(self, question: str) -> PedagogicalIntent:

        text = (
            question
            .lower()
            .strip()
            .replace("’", "'")
        )

        if not text:
            return PedagogicalIntent.UNKNOWN

        # ==================================================
        # 1. CORRECTION
        # ==================================================

        correction_indicators = (
            "corrige",
            "corriger",
            "corrigé",
            "corrige-moi",
            "corrige moi",
            "peux-tu corriger",
            "peux tu corriger",
            "pourrais-tu corriger",
            "pourrais tu corriger",
            "correction",
            "corriger mon exercice",
            "corrige mon exercice",
            "corriger cet exercice",
            "corrige cet exercice",
            "corriger ma réponse",
            "corrige ma réponse",
            "corriger ma reponse",
            "corrige ma reponse",
            "est-ce que ma réponse",
            "est ce que ma réponse",
            "est-ce que ma reponse",
            "est ce que ma reponse",
            "ma réponse est-elle",
            "ma reponse est-elle",
        )

        if any(
            indicator in text
            for indicator in correction_indicators
        ):
            return PedagogicalIntent.CORRECTION

        # ==================================================
        # 2. EXERCICE / ENTRAÎNEMENT
        # ==================================================

        practice_indicators = (
            "donne-moi un exercice",
            "donne moi un exercice",
            "donne-moi des exercices",
            "donne moi des exercices",
            "propose-moi un exercice",
            "propose moi un exercice",
            "propose-moi des exercices",
            "propose moi des exercices",
            "exercice sur",
            "exercices sur",
            "un exercice sur",
            "des exercices sur",
            "entraine-moi",
            "entraine moi",
            "entraîne-moi",
            "entraîne moi",
            "faire un exercice",
            "faire des exercices",
            "pour m'entraîner",
            "pour m'entrainer",
        )

        if any(
            indicator in text
            for indicator in practice_indicators
        ):
            return PedagogicalIntent.PRACTICE

        # ==================================================
        # 3. RÉEXPLICATION
        # ==================================================

        reexplanation_indicators = (
            "je n'ai pas compris",
            "je n ai pas compris",
            "je comprends pas",
            "je ne comprends pas",
            "je ne comprend pas",
            "explique encore",
            "explique-moi encore",
            "explique moi encore",
            "réexplique",
            "reexplique",
            "réexplique-moi",
            "réexplique moi",
            "reexplique-moi",
            "reexplique moi",
            "peux-tu réexpliquer",
            "peux tu réexpliquer",
            "peux-tu reexpliquer",
            "peux tu reexpliquer",
        )

        if any(
            indicator in text
            for indicator in reexplanation_indicators
        ):
            return PedagogicalIntent.REEXPLANATION

        # ==================================================
        # 4. RÉSOLUTION DE PROBLÈME
        # ==================================================

        problem_indicators = (
            "comment résoudre",
            "comment resoudre",
            "résous",
            "resous",
            "résoudre",
            "resoudre",
            "calcule",
            "calculer",
            "trouve",
            "trouver",
            "détermine",
            "determiner",
        )

        if any(
            indicator in text
            for indicator in problem_indicators
        ):
            return PedagogicalIntent.PROBLEM_SOLVING

        # ==================================================
        # 5. RÉSUMÉ
        # ==================================================

        # ==================================================
        # 5. RÉSUMÉ
        # ==================================================

        summary_indicators = (
            "résume-moi",
            "résume moi",
            "resume-moi",
            "resume moi",
            "résume le",
            "résume ce",
            "résume cette",
            "resume le",
            "resume ce",
            "resume cette",
            "résumer le",
            "résumer ce",
            "résumer cette",
            "fais-moi un résumé",
            "fais moi un résumé",
            "fais-moi un resume",
            "fais moi un resume",
            "faire un résumé",
            "faire un resume",
            "fais une synthèse",
            "fais une synthese",
            "synthétise",
            "synthetise",
        )

        if any(
            indicator in text
            for indicator in summary_indicators
        ):
            return PedagogicalIntent.SUMMARY

        # ==================================================
        # 6. RÉVISION
        # ==================================================

        revision_indicators = (
            "révise",
            "revise",
            "réviser",
            "reviser",
            "révision",
            "revision",
            "rappelle-moi",
            "rappelle moi",
            "à retenir",
            "a retenir",
        )

        if any(
            indicator in text
            for indicator in revision_indicators
        ):
            return PedagogicalIntent.REVISION

        # ==================================================
        # 7. EXPLICATION DE CONCEPT
        # ==================================================

        concept_indicators = (
            "qu'est-ce que",
            "qu'est-ce qu'un",
            "qu'est-ce qu'une",
            "qu est ce que",
            "qu est ce qu'un",
            "qu est ce qu'une",
            "quest-ce que",
            "quest-ce qu'un",
            "quest-ce qu'une",
            "quest ce que",
            "quest ce qu'un",
            "quest ce qu'une",
            "c'est quoi",
            "c est quoi",
            "définition",
            "definition",
            "définis",
            "definis",
            "explique",
            "explique-moi",
            "explique moi",
            "signifie",
            "que signifie",
            "quel est",
            "quelle est",
            "quels sont",
            "quelles sont",
        )

        if any(
            indicator in text
            for indicator in concept_indicators
        ):
            return PedagogicalIntent.CONCEPT_EXPLANATION

        # ==================================================
        # 8. INTENTION INCONNUE
        # ==================================================

        return PedagogicalIntent.UNKNOWN