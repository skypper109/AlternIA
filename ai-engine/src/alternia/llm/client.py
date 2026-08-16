from abc import ABC, abstractmethod
from typing import Iterator


class LLMClient(ABC):
    """
    Interface abstraite du modèle de langage d'AlternIA.

    L'orchestrateur dépend de cette interface et non
    d'un fournisseur particulier.

    On pourra ainsi brancher :
    - un modèle local (Llama.cpp / GGUF),
    - un mock pour les tests (FakeLLMClient),
    - OpenAI, Gemini, Ollama, etc.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str | None = None,
        *,
        messages: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
    ) -> str:
        """
        Génère une réponse textuelle complète à partir d'un prompt ou d'une liste de messages.
        """
        raise NotImplementedError

    def generate_stream(
        self,
        prompt: str | None = None,
        *,
        messages: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
    ) -> Iterator[str]:
        """
        Génère un flux de tokens/mots (streaming).
        Par défaut, émet la réponse complète en une passe si le fournisseur
        ne supporte pas le streaming natif.
        """
        yield self.generate(
            prompt=prompt,
            messages=messages,
            system_prompt=system_prompt,
        )
