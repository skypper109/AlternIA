"""
Client LLM Groq Cloud Ultra-Rapide pour AlternIA.

Propulsé par l'API Groq (Qwen 3.8 27B / GPT-OSS 120B).
- Évite la surcharge mémoire/CPU du LLM local (allège considérablement le système).
- Affichage en streaming direct dans la console terminal pour une visibilité totale.
- Conservation de la logique locale existante en fallback (LazyLocalLLMClient).
"""

import os
import sys
import time
from typing import Any, Iterator, cast
from pathlib import Path

try:
    from groq import Groq
except ImportError:
    Groq = None  # type: ignore

from alternia.llm.client import LLMClient


DEFAULT_GROQ_API_KEY = "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"
DEFAULT_GROQ_MODEL = "qwen/qwen3.8-27b"
SECONDARY_GROQ_MODEL = "openai/gpt-oss-120b"


class LazyLocalLLMClient(LLMClient):
    """
    Client local paresseux : ne charge les poids lourds du modèle GGUF (llama.cpp)
    en mémoire vive (RAM) QUE si un appel de secours est requis (hors-ligne ou panne réseau).
    Permet d'économiser plusieurs gigaoctets de RAM et 100% de CPU au démarrage normal.
    """

    def __init__(self, model_path: str, n_ctx: int = 4096, n_batch: int = 512):
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_batch = n_batch
        self._real_client: LLMClient | None = None

    def _get_client(self) -> LLMClient:
        if self._real_client is None:
            print(f"\n\033[1;33m⏳ [LazyLocalLLMClient] Chargement à la demande du modèle local GGUF ({self.model_path})...\033[0m")
            from alternia.llm.local_client import LocalLLMClient
            self._real_client = LocalLLMClient(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_batch=self.n_batch,
            )
            print(f"\033[1;32m✅ [LazyLocalLLMClient] Modèle local chargé en mémoire pour le secours.\033[0m\n")
        return self._real_client

    def generate(
        self,
        prompt: str | None = None,
        *,
        messages: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        return self._get_client().generate(
            prompt=prompt,
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def generate_stream(
        self,
        prompt: str | None = None,
        *,
        messages: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> Iterator[str]:
        yield from self._get_client().generate_stream(
            prompt=prompt,
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )


class GroqLLMClient(LLMClient):
    """
    Client LLM ultra-rapide propulsé par Groq API (Qwen 3.8 27B / GPT-OSS 120B).
    Prend en charge le streaming live en console et le fallback automatique.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        fallback_client: LLMClient | None = None,
        temperature: float = 0.7,
        top_p: float = 1.0,
        max_tokens: int = 4096,
    ):
        self.api_key = (
            api_key
            or os.getenv("GROQ_API_KEY")
            or os.getenv("LLM_API_KEY")
            or DEFAULT_GROQ_API_KEY
        ).strip()

        self.model = (
            model
            or os.getenv("GROQ_MODEL")
            or os.getenv("LLM_MODEL")
            or DEFAULT_GROQ_MODEL
        ).strip()

        self.fallback_client = fallback_client
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens

        self.client: Any = None
        if Groq is not None and self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
                print(f"\033[1;32m⚡ [GroqLLMClient] Connecté avec succès | Modèle actif : {self.model}\033[0m")
            except Exception as e:
                print(f"\033[1;31m⚠️ [GroqLLMClient] Erreur initialisation Groq : {e}\033[0m")
                self.client = None
        else:
            print(f"\033[1;33m⚠️ [GroqLLMClient] Module 'groq' non trouvé ou clé API manquante.\033[0m")

    def _build_messages(
        self,
        prompt: str | None = None,
        system_prompt: str | None = None,
        messages: list[dict[str, str]] | None = None,
    ) -> list[dict[str, str]]:
        if messages is not None:
            formatted = list(messages)
            if system_prompt and not any(m.get("role") == "system" for m in formatted):
                formatted.insert(0, {"role": "system", "content": system_prompt})
            return formatted

        res: list[dict[str, str]] = []
        if system_prompt:
            res.append({"role": "system", "content": system_prompt})
        if prompt:
            res.append({"role": "user", "content": prompt})
        return res

    def generate(
        self,
        prompt: str | None = None,
        *,
        messages: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """
        Génère une réponse complète en streamant les tokens en temps réel dans la console.
        """
        req_messages = self._build_messages(prompt, system_prompt, messages)
        eff_temp = temperature if temperature is not None else self.temperature
        eff_max = max_tokens if max_tokens is not None else self.max_tokens

        start_time = time.perf_counter()
        preview = (prompt or (messages[-1]["content"] if messages else ""))[:80].replace("\n", " ")

        print(f"\n\033[1;35m┌─────────────────────────────────────────────────────────────────────────────────────────────\033[0m")
        print(f"\033[1;35m│ 🚀 [Groq Cloud Engine] Appel Modèle : \033[1;33m{self.model}\033[0m \033[1;36m(Inférence ultra-rapide)\033[0m")
        print(f"\033[1;35m│ 📥 Prompt : \033[0m{preview}...")
        print(f"\033[1;35m├┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\033[0m")
        print(f"\033[1;32m│ 🎙️ [Réponse en direct dans la console] :\033[0m\n", flush=True)

        if self.client is not None:
            try:
                call_args: dict[str, Any] = {
                    "model": self.model,
                    "messages": req_messages,
                    "temperature": eff_temp,
                    "max_completion_tokens": eff_max,
                    "top_p": self.top_p,
                    "stream": True,
                }
                # Support reasoning_effort si modèle de raisonnement spécifique
                if "gpt-oss" in self.model.lower():
                    call_args["reasoning_effort"] = "medium"

                completion = self.client.chat.completions.create(**call_args)

                chunks: list[str] = []
                for chunk in completion:
                    delta = chunk.choices[0].delta.content or ""
                    if delta:
                        chunks.append(delta)
                        sys.stdout.write(delta)
                        sys.stdout.flush()

                full_text = "".join(chunks)
                elapsed = time.perf_counter() - start_time
                token_count = max(len(full_text) // 4, len(chunks))
                tps = token_count / max(elapsed, 0.001)

                print(f"\n\n\033[1;35m├┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\033[0m")
                print(f"\033[1;35m│ ✅ [Groq API] Terminé avec succès en \033[1;33m{elapsed:.2f}s\033[0m (~{token_count} tokens | \033[1;32m{tps:.1f} tokens/s\033[0m)")
                print(f"\033[1;35m└─────────────────────────────────────────────────────────────────────────────────────────────\033[0m\n")
                return full_text

            except Exception as e:
                print(f"\n\033[1;31m│ ⚠️ [Groq API] Erreur lors de l'appel : {e}\033[0m")
                print(f"\033[1;31m└─────────────────────────────────────────────────────────────────────────────────────────────\033[0m\n")

        # Fallback automatique sur le client local ou secondaire si Groq échoue
        if self.fallback_client is not None:
            print(f"\033[1;33m🔄 [GroqLLMClient] Bascule automatique sur le fallback ({self.fallback_client.__class__.__name__})...\033[0m")
            return self.fallback_client.generate(
                prompt=prompt,
                messages=messages,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        raise RuntimeError("Échec de la génération Groq et aucun client de secours disponible.")

    def generate_stream(
        self,
        prompt: str | None = None,
        *,
        messages: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> Iterator[str]:
        """
        Génère un flux de tokens (streaming) tout en l'affichant en direct dans la console.
        """
        req_messages = self._build_messages(prompt, system_prompt, messages)
        eff_temp = temperature if temperature is not None else self.temperature
        eff_max = max_tokens if max_tokens is not None else self.max_tokens

        start_time = time.perf_counter()
        preview = (prompt or (messages[-1]["content"] if messages else ""))[:80].replace("\n", " ")

        print(f"\n\033[1;35m┌─────────────────────────────────────────────────────────────────────────────────────────────\033[0m")
        print(f"\033[1;35m│ 🚀 [Groq Stream Engine] Appel Modèle : \033[1;33m{self.model}\033[0m")
        print(f"\033[1;35m│ 📥 Prompt : \033[0m{preview}...")
        print(f"\033[1;35m├┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\033[0m")
        print(f"\033[1;32m│ 🎙️ [Stream en direct] :\033[0m\n", flush=True)

        if self.client is not None:
            try:
                call_args: dict[str, Any] = {
                    "model": self.model,
                    "messages": req_messages,
                    "temperature": eff_temp,
                    "max_completion_tokens": eff_max,
                    "top_p": self.top_p,
                    "stream": True,
                }
                if "gpt-oss" in self.model.lower():
                    call_args["reasoning_effort"] = "medium"

                completion = self.client.chat.completions.create(**call_args)

                chunk_count = 0
                for chunk in completion:
                    delta = chunk.choices[0].delta.content or ""
                    if delta:
                        chunk_count += 1
                        sys.stdout.write(delta)
                        sys.stdout.flush()
                        yield delta

                elapsed = time.perf_counter() - start_time
                print(f"\n\n\033[1;35m├┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\033[0m")
                print(f"\033[1;35m│ ✅ [Groq Stream] Terminé en \033[1;33m{elapsed:.2f}s\033[0m ({chunk_count} morceaux)")
                print(f"\033[1;35m└─────────────────────────────────────────────────────────────────────────────────────────────\033[0m\n")
                return

            except Exception as e:
                print(f"\n\033[1;31m│ ⚠️ [Groq Stream] Erreur : {e}\033[0m")
                print(f"\033[1;31m└─────────────────────────────────────────────────────────────────────────────────────────────\033[0m\n")

        # Fallback automatique
        if self.fallback_client is not None:
            print(f"\033[1;33m🔄 [GroqLLMClient] Bascule stream sur le fallback...\033[0m")
            yield from self.fallback_client.generate_stream(
                prompt=prompt,
                messages=messages,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return

        raise RuntimeError("Échec du streaming Groq et aucun client de secours disponible.")
