from abc import ABC, abstractmethod


class LLMClient(ABC):
    """
    Interface abstraite du modèle de langage d'AlternIA.

    L'orchestrateur dépend de cette interface et non
    d'un fournisseur particulier.

    On pourra ainsi brancher plus tard :
    - un modèle local,
    - OpenAI,
    - Gemini,
    - Ollama,
    - ou un autre fournisseur.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
    ) -> str:
        """
        Génère une réponse à partir d'un prompt.
        """
        raise NotImplementedError
