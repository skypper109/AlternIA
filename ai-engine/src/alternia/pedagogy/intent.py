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

    UNKNOWN = "unknown"


class IntentDetector:
    """
    Détecte l'intention pédagogique principale
    exprimée dans la question de l'élève.
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

        # -----------------------------------------
        # Correction
        # -----------------------------------------

        correction_indicators = (
            "corrige",
            "corriger",
            "correction",
            "est-ce que ma réponse",
            "ma réponse est-elle",
        )

        if any(
            indicator in text
            for indicator in correction_indicators
        ):
            return PedagogicalIntent.CORRECTION

        # -----------------------------------------
        # Exercice / entraînement
        # -----------------------------------------

        practice_indicators = (
            "donne-moi un exercice",
            "donne moi un exercice",
            "propose-moi un exercice",
            "propose moi un exercice",
            "exercice sur",
            "exercices sur",
            "entraine-moi",
            "entraîne-moi",
        )

        if any(
            indicator in text
            for indicator in practice_indicators
        ):
            return PedagogicalIntent.PRACTICE

        # -----------------------------------------
        # Réexplication
        # -----------------------------------------

        reexplanation_indicators = (
            "je n'ai pas compris",
            "je comprends pas",
            "je ne comprends pas",
            "explique encore",
            "réexplique",
            "reexplique",
            "peux-tu réexpliquer",
            "peux tu réexpliquer",
        )

        if any(
            indicator in text
            for indicator in reexplanation_indicators
        ):
            return PedagogicalIntent.REEXPLANATION

        # -----------------------------------------
        # Résolution de problème
        # -----------------------------------------

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

        # -----------------------------------------
        # Révision
        # -----------------------------------------

        revision_indicators = (
            "révise",
            "revise",
            "révision",
            "revision",
            "résumé",
            "resume",
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

        # -----------------------------------------
        # Explication de concept
        # -----------------------------------------

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

        return PedagogicalIntent.UNKNOWN
