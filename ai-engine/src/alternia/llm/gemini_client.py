"""
Client LLM Gemini Cloud Ultra-Rapide pour AlternIA.

Propulsé par l'API Google GenAI (Gemini 3 Flash / Gemini 2.5 Flash).
- Inférence illimitée en requêtes par seconde et par jour.
- Affichage en streaming direct dans la console terminal pour une visibilité totale.
- Support du multi-fournisseur et fallback automatique (Groq Qwen ou Local GGUF).
"""

import os
import sys
import time
from typing import Any, Iterator, cast
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None  # type: ignore
    types = None  # type: ignore

from alternia.llm.client import LLMClient


DEFAULT_GEMINI_API_KEY = "AQ.Ab8RN6JGzagbZCG-VcH1I4tTAUGUmN9bB9nwWLDUsP1xTs0r5w"
DEFAULT_GEMINI_MODEL = "gemini-3-flash-preview"
FALLBACK_GEMINI_MODELS = ["gemini-3-flash-preview", "gemini-2.5-flash", "gemini-flash-latest"]


class GeminiLLMClient(LLMClient):
    """
    Client LLM propulsé par Gemini 3 Flash pour AlternIA.
    Inférence haute vitesse illimitée, streaming console temps réel et tolérance aux pannes.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        fallback_client: LLMClient | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        self.api_key = (
            api_key
            or os.getenv("GEMINI_API_KEY")
            or DEFAULT_GEMINI_API_KEY
        ).strip()

        self.model = (
            model
            or os.getenv("GEMINI_MODEL")
            or DEFAULT_GEMINI_MODEL
        ).strip()

        self.fallback_client = fallback_client
        self.temperature = temperature
        self.max_tokens = max_tokens

        self.client: Any = None
        if genai is not None and self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
                print(f"\033[1;36m✨ [GeminiLLMClient] Connecté avec succès | Modèle actif : {self.model} (Requêtes illimitées)\033[0m")
            except Exception as e:
                print(f"\033[1;31m⚠️ [GeminiLLMClient] Erreur initialisation Gemini : {e}\033[0m")
                self.client = None
        else:
            print(f"\033[1;33m⚠️ [GeminiLLMClient] Module 'google-genai' non trouvé ou clé API manquante.\033[0m")

    def _format_prompt(
        self,
        prompt: str | None = None,
        messages: list[dict[str, str]] | None = None,
    ) -> str:
        if prompt:
            return prompt
        if messages:
            lines: list[str] = []
            for m in messages:
                role = m.get("role", "user")
                c = m.get("content", "")
                if role == "system":
                    continue
                lines.append(f"{role.capitalize()}: {c}")
            return "\n".join(lines) if lines else ""
        return ""

    def _extract_system(
        self,
        system_prompt: str | None = None,
        messages: list[dict[str, str]] | None = None,
    ) -> str | None:
        if system_prompt:
            return system_prompt
        if messages:
            for m in messages:
                if m.get("role") == "system":
                    return m.get("content", "")
        return None

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
        Génère une réponse complète en streamant les tokens en temps réel dans la console terminal.
        """
        content_text = self._format_prompt(prompt, messages)
        sys_instruction = self._extract_system(system_prompt, messages)
        eff_temp = temperature if temperature is not None else self.temperature
        eff_max = max_tokens if max_tokens is not None else self.max_tokens

        start_time = time.perf_counter()
        preview = content_text[:80].replace("\n", " ")

        print(f"\n\033[1;34m┌─────────────────────────────────────────────────────────────────────────────────────────────\033[0m")
        print(f"\033[1;34m│ ✨ [Gemini Cloud Engine] Appel Modèle : \033[1;36m{self.model}\033[0m \033[1;32m(Inférence illimitée)\033[0m")
        print(f"\033[1;34m│ 📥 Prompt : \033[0m{preview}...")
        print(f"\033[1;34m├┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\033[0m")
        print(f"\033[1;36m│ 🎙️ [Réponse Gemini en direct dans la console] :\033[0m\n", flush=True)

        if self.client is not None:
            # Essayer le modèle principal, puis les variantes en cas d'erreur de version
            models_to_try = [self.model] + [m for m in FALLBACK_GEMINI_MODELS if m != self.model]

            for model_candidate in models_to_try:
                try:
                    config_args: dict[str, Any] = {
                        "temperature": eff_temp,
                    }
                    if sys_instruction:
                        config_args["system_instruction"] = sys_instruction
                    if eff_max:
                        config_args["max_output_tokens"] = eff_max

                    config = types.GenerateContentConfig(**config_args) if types else None

                    stream = self.client.models.generate_content_stream(
                        model=model_candidate,
                        contents=content_text,
                        config=config,
                    )

                    chunks: list[str] = []
                    for chunk in stream:
                        delta = chunk.text or ""
                        if delta:
                            chunks.append(delta)
                            sys.stdout.write(delta)
                            sys.stdout.flush()

                    full_text = "".join(chunks)
                    elapsed = time.perf_counter() - start_time
                    token_count = max(len(full_text) // 4, len(chunks))
                    tps = token_count / max(elapsed, 0.001)

                    print(f"\n\n\033[1;34m├┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\033[0m")
                    print(f"\033[1;34m│ ✅ [Gemini API] Terminé avec succès en \033[1;33m{elapsed:.2f}s\033[0m (~{token_count} tokens | \033[1;32m{tps:.1f} tokens/s\033[0m)")
                    print(f"\033[1;34m└─────────────────────────────────────────────────────────────────────────────────────────────\033[0m\n")
                    return full_text

                except Exception as e:
                    print(f"\n\033[1;33m│ ⚠️ [Gemini API] Échec sur {model_candidate} ({e}), essai du suivant...\033[0m")
                    continue

        # Fallback automatique
        if self.fallback_client is not None:
            print(f"\033[1;33m🔄 [GeminiLLMClient] Bascule automatique sur le fallback ({self.fallback_client.__class__.__name__})...\033[0m")
            return self.fallback_client.generate(
                prompt=prompt,
                messages=messages,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        raise RuntimeError("Échec de la génération Gemini et aucun client de secours disponible.")

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
        Génère un flux de tokens (streaming) tout en affichant en temps réel dans la console.
        """
        content_text = self._format_prompt(prompt, messages)
        sys_instruction = self._extract_system(system_prompt, messages)
        eff_temp = temperature if temperature is not None else self.temperature
        eff_max = max_tokens if max_tokens is not None else self.max_tokens

        start_time = time.perf_counter()
        preview = content_text[:80].replace("\n", " ")

        print(f"\n\033[1;34m┌─────────────────────────────────────────────────────────────────────────────────────────────\033[0m")
        print(f"\033[1;34m│ ✨ [Gemini Stream] Modèle : \033[1;36m{self.model}\033[0m")
        print(f"\033[1;34m│ 📥 Prompt : \033[0m{preview}...")
        print(f"\033[1;34m├┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\033[0m")
        print(f"\033[1;36m│ 🎙️ [Stream Gemini en direct] :\033[0m\n", flush=True)

        if self.client is not None:
            models_to_try = [self.model] + [m for m in FALLBACK_GEMINI_MODELS if m != self.model]

            for model_candidate in models_to_try:
                try:
                    config_args: dict[str, Any] = {
                        "temperature": eff_temp,
                    }
                    if sys_instruction:
                        config_args["system_instruction"] = sys_instruction
                    if eff_max:
                        config_args["max_output_tokens"] = eff_max

                    config = types.GenerateContentConfig(**config_args) if types else None

                    stream = self.client.models.generate_content_stream(
                        model=model_candidate,
                        contents=content_text,
                        config=config,
                    )

                    chunk_count = 0
                    for chunk in stream:
                        delta = chunk.text or ""
                        if delta:
                            chunk_count += 1
                            sys.stdout.write(delta)
                            sys.stdout.flush()
                            yield delta

                    elapsed = time.perf_counter() - start_time
                    print(f"\n\n\033[1;34m├┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\033[0m")
                    print(f"\033[1;34m│ ✅ [Gemini Stream] Terminé en \033[1;33m{elapsed:.2f}s\033[0m ({chunk_count} morceaux)")
                    print(f"\033[1;34m└─────────────────────────────────────────────────────────────────────────────────────────────\033[0m\n")
                    return

                except Exception as e:
                    print(f"\n\033[1;33m│ ⚠️ [Gemini Stream] Échec sur {model_candidate} ({e}), essai du suivant...\033[0m")
                    continue

        # Fallback automatique
        if self.fallback_client is not None:
            print(f"\033[1;33m🔄 [GeminiLLMClient] Bascule stream sur le fallback...\033[0m")
            yield from self.fallback_client.generate_stream(
                prompt=prompt,
                messages=messages,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return

        raise RuntimeError("Échec du streaming Gemini et aucun client de secours disponible.")
