from alternia.llm.client import LLMClient


class FakeLLMClient(LLMClient):
    """
    LLM simulé utilisé pour les tests.

    Deux modes sont possibles :

    1. response fournie :
       retourne exactement cette réponse.

    2. response absente :
       génère une réponse déterministe en fonction
       du contenu du prompt.
    """

    def __init__(
        self,
        response: str | None = None,
    ):
        self.response = response

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
    ) -> str:

        # -----------------------------------------
        # Réponse explicitement demandée par le test
        # -----------------------------------------

        if self.response is not None:
            return self.response

        # -----------------------------------------
        # Comportement automatique
        # -----------------------------------------

        if "équation" in prompt.lower():
            return (
                "Une équation est une égalité mathématique "
                "dans laquelle on cherche la valeur d'une "
                "inconnue. Pour la résoudre, on cherche "
                "la valeur qui rend l'égalité vraie."
            )

        return (
            "Je vais t'aider à comprendre cette question "
            "étape par étape."
        )
