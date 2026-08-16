class PedagogicalResponseValidator:
    """
    Valide une réponse générée par le LLM.

    Cette première version effectue des contrôles
    structurels simples avant d'envoyer la réponse
    à l'élève.
    """

    def validate(
        self,
        answer: str,
        *,
        question: str,
        context: str = "",
    ) -> str:

        if answer is None:
            raise ValueError(
                "Le LLM a retourné une réponse vide."
            )

        answer = answer.strip()

        if not answer:
            raise ValueError(
                "Le LLM a retourné une réponse vide."
            )

        # Protection contre certaines réponses
        # manifestement internes.
        forbidden_markers = (
            "REQUÊTE PÉDAGOGIQUE ALTERNIA",
            "STRATÉGIE PÉDAGOGIQUE",
            "INSTRUCTION FINALE",
        )

        for marker in forbidden_markers:
            if marker in answer:
                raise ValueError(
                    "La réponse contient des informations "
                    "internes au système pédagogique."
                )

        return answer