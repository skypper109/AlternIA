from typing import Any


class PedagogicalResponseValidator:
    """
    Valide une réponse générée par AlternIA avant
    de la transmettre à l'utilisateur.
    """

    def validate(
        self,
        answer: str,
        *,
        question: str,
        context: Any = None,
    ) -> str:

        if not isinstance(answer, str):
            raise TypeError(
                "La réponse du LLM doit être une chaîne de caractères."
            )

        cleaned_answer = answer.strip()

        if not cleaned_answer:
            raise ValueError(
                "Le LLM a retourné une réponse vide."
            )

        return cleaned_answer