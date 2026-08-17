from pathlib import Path
from typing import Any, cast

from alternia.llm.client import LLMClient


class LocalLlamaClient(LLMClient):
    """
    Client LLM local basé sur llama.cpp.

    Destiné notamment au Raspberry Pi 4/5 et machines légères.
    """

    def __init__(
        self,
        model_path: str,
        *,
        n_ctx: int = 2048,
        n_threads: int = 4,
        n_batch: int = 128,
        temperature: float = 0.15,
        top_p: float = 0.9,
        repeat_penalty: float = 1.20,
        frequency_penalty: float = 0.5,
        presence_penalty: float = 0.3,
        max_tokens: int = 180,
        verbose: bool = False,
    ):
        self.model_path = Path(model_path)

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Modèle LLM introuvable : "
                f"{self.model_path}"
            )

        self.temperature = temperature
        self.top_p = top_p
        self.repeat_penalty = repeat_penalty
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.max_tokens = max_tokens

        try:
            from llama_cpp import Llama
        except ImportError:
            raise ImportError(
                "Le paquet llama-cpp-python n'est pas installé. "
                "Installez-le avec : pip install llama-cpp-python"
            )

        self.llm: Any = Llama(
            model_path=str(self.model_path),
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_batch=n_batch,
            verbose=verbose,
        )

    def generate(
        self,
        prompt: str | None = None,
        *,
        messages: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
    ) -> str:

        if messages is None:
            messages = []
            if system_prompt:
                messages.append(
                    {
                        "role": "system",
                        "content": system_prompt,
                    }
                )

            if prompt:
                messages.append(
                    {
                        "role": "user",
                        "content": prompt,
                    }
                )

        raw_response = self.llm.create_chat_completion(
            messages=cast(Any, messages),
            temperature=self.temperature,
            top_p=self.top_p,
            repeat_penalty=self.repeat_penalty,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            max_tokens=self.max_tokens,
        )
        response: dict[str, Any] = cast(dict[str, Any], raw_response)

        choices = response.get("choices", [])
        if choices and isinstance(choices, list):
            message = choices[0].get("message", {})
            content = message.get("content", "")
            return str(content).strip()

        return ""

    def generate_stream(
        self,
        prompt: str | None = None,
        *,
        messages: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
    ):
        if messages is None:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            if prompt:
                messages.append({"role": "user", "content": prompt})

        raw_stream = self.llm.create_chat_completion(
            messages=cast(Any, messages),
            temperature=self.temperature,
            top_p=self.top_p,
            repeat_penalty=self.repeat_penalty,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            max_tokens=self.max_tokens,
            stream=True,
        )

        for chunk_item in raw_stream:
            if not isinstance(chunk_item, dict):
                continue
            choices = chunk_item.get("choices", [])
            if not choices or not isinstance(choices[0], dict):
                continue
            delta = choices[0].get("delta", {})
            if isinstance(delta, dict) and "content" in delta:
                yield str(delta["content"])
