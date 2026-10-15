"""
Client LLM Gemini Cloud Ultra-Rapide pour AlternIA.

Propulsé par l'API Google GenAI (Gemini 2.5 Flash / Gemini 3.8 Flash).
- Inférence haute cadence (haute limite de requêtes, réponse instantanée ~1s).
- Affichage en streaming direct dans la console terminal pour une visibilité totale.
- Double moteur d'exécution : SDK 'google-genai' ou REST SSE natif (aucune dépendance requise).
- Support du multi-fournisseur et fallback automatique (Groq Qwen ou Local GGUF).
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Iterator
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None  # type: ignore
    types = None  # type: ignore

from alternia.llm.client import LLMClient


DEFAULT_GEMINI_API_KEY = "AQ.Ab8RN6JGzagbZCG-VcH1I4tTAUGUmN9bB9nwWLDUsP1xTs0r5w"
DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"
FALLBACK_GEMINI_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash",
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
]


class GeminiLLMClient(LLMClient):
    """
    Client LLM propulsé par Gemini 2.5 Flash / Gemini 3.8 Flash pour AlternIA.
    Inférence haute vitesse, streaming console temps réel et tolérance aux pannes.
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
                print(f"\033[1;36m✨ [GeminiLLMClient] Connecté via SDK GenAI | Modèle actif : {self.model}\033[0m")
            except Exception as e:
                print(f"\033[1;33m⚠️ [GeminiLLMClient] SDK GenAI indisponible ({e}) -> Mode REST SSE activé.\033[0m")
                self.client = None
        else:
            print(f"\033[1;36m✨ [GeminiLLMClient] Mode REST SSE natif activé (haute cadence) | Modèle actif : {self.model}\033[0m")

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

    def _build_contents_payload(
        self,
        prompt: str | None = None,
        messages: list[dict[str, str]] | None = None,
    ) -> list[dict[str, Any]]:
        if messages:
            contents: list[dict[str, Any]] = []
            for m in messages:
                role = m.get("role", "user")
                if role == "system":
                    continue
                gemini_role = "model" if role in ("assistant", "model") else "user"
                c = m.get("content", "")
                if c:
                    contents.append({
                        "role": gemini_role,
                        "parts": [{"text": c}],
                    })
            if contents:
                return contents
        text = prompt or ""
        return [{"role": "user", "parts": [{"text": text}]}]

    def _generate_via_rest(
        self,
        model_name: str,
        contents_payload: list[dict[str, Any]],
        system_instruction: str | None,
        temperature: float,
        max_tokens: int,
    ) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
        payload: dict[str, Any] = {
            "contents": contents_payload,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "thinkingConfig": {"thinkingBudget": 0},
            },
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candidates = data.get("candidates", [])
            if not candidates:
                raise RuntimeError(f"Aucune réponse reçue pour {model_name}")
            parts = candidates[0].get("content", {}).get("parts", [])
            text_pieces = [p.get("text", "") for p in parts if p.get("text")]
            return "".join(text_pieces)

    def _stream_via_rest(
        self,
        model_name: str,
        contents_payload: list[dict[str, Any]],
        system_instruction: str | None,
        temperature: float,
        max_tokens: int,
    ) -> Iterator[str]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:streamGenerateContent?alt=sse&key={self.api_key}"
        payload: dict[str, Any] = {
            "contents": contents_payload,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "thinkingConfig": {"thinkingBudget": 0},
            },
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=45) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if line.startswith("data: "):
                    raw_data = line[6:].strip()
                    if not raw_data:
                        continue
                    try:
                        data = json.loads(raw_data)
                    except json.JSONDecodeError:
                        continue

                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        for part in parts:
                            delta = part.get("text", "")
                            if delta:
                                yield delta

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
        contents_payload = self._build_contents_payload(prompt, messages)

        start_time = time.perf_counter()
        preview = content_text[:80].replace("\n", " ")

        print(f"\n\033[1;34m┌─────────────────────────────────────────────────────────────────────────────────────────────\033[0m")
        print(f"\033[1;34m│ ✨ [Gemini Cloud Engine] Appel Modèle : \033[1;36m{self.model}\033[0m \033[1;32m(Haute cadence illimitée)\033[0m")
        print(f"\033[1;34m│ 📥 Prompt : \033[0m{preview}...")
        print(f"\033[1;34m├┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\033[0m")
        print(f"\033[1;36m│ 🎙️ [Réponse Gemini en direct dans la console] :\033[0m\n", flush=True)

        models_to_try = [self.model] + [m for m in FALLBACK_GEMINI_MODELS if m != self.model]

        if not self.api_key or not self.api_key.startswith("AIzaSy"):
            print(f"\033[1;33m⚠️ [GeminiLLMClient] Clé API Gemini manquante ou invalide (doit débuter par 'AIzaSy'). Bascule immédiate sur le secours...\033[0m")
            if self.fallback_client is not None:
                return self.fallback_client.generate(
                    prompt=prompt,
                    messages=messages,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            raise RuntimeError("Clé Gemini invalide et aucun client de secours disponible.")

        for model_candidate in models_to_try:
            try:
                # 1. Essai via SDK genai si disponible
                if self.client is not None:
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
                            # Extraction tolérante aux thinking tokens
                            delta = getattr(chunk, "text", "") or ""
                            if delta:
                                chunks.append(delta)
                                sys.stdout.write(delta)
                                sys.stdout.flush()

                        full_text = "".join(chunks)
                        if full_text:
                            elapsed = time.perf_counter() - start_time
                            token_count = max(len(full_text) // 4, len(chunks))
                            tps = token_count / max(elapsed, 0.001)
                            print(f"\n\n\033[1;34m├┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\033[0m")
                            print(f"\033[1;34m│ ✅ [Gemini SDK] Succès sur {model_candidate} en \033[1;33m{elapsed:.2f}s\033[0m (~{token_count} tokens | \033[1;32m{tps:.1f} tokens/s\033[0m)")
                            print(f"\033[1;34m└─────────────────────────────────────────────────────────────────────────────────────────────\033[0m\n")
                            return full_text
                    except Exception as e_sdk:
                        print(f"\033[1;33m│ ⚠️ [Gemini SDK] Erreur {model_candidate} ({e_sdk}) -> tentative REST...\033[0m")

                # 2. Exécution REST SSE directe (garantie sans dépendances externes)
                chunks = []
                for delta in self._stream_via_rest(
                    model_name=model_candidate,
                    contents_payload=contents_payload,
                    system_instruction=sys_instruction,
                    temperature=eff_temp,
                    max_tokens=eff_max,
                ):
                    chunks.append(delta)
                    sys.stdout.write(delta)
                    sys.stdout.flush()

                full_text = "".join(chunks)
                if full_text:
                    elapsed = time.perf_counter() - start_time
                    token_count = max(len(full_text) // 4, len(chunks))
                    tps = token_count / max(elapsed, 0.001)
                    print(f"\n\n\033[1;34m├┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\033[0m")
                    print(f"\033[1;34m│ ✅ [Gemini REST] Succès sur {model_candidate} en \033[1;33m{elapsed:.2f}s\033[0m (~{token_count} tokens | \033[1;32m{tps:.1f} tokens/s\033[0m)")
                    print(f"\033[1;34m└─────────────────────────────────────────────────────────────────────────────────────────────\033[0m\n")
                    return full_text

            except Exception as e:
                print(f"\n\033[1;33m│ ⚠️ [Gemini API] Échec sur {model_candidate} ({e}), essai du suivant...\033[0m")
                continue

        # Fallback automatique vers Groq ou Local
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
        contents_payload = self._build_contents_payload(prompt, messages)

        start_time = time.perf_counter()
        preview = content_text[:80].replace("\n", " ")

        print(f"\n\033[1;34m┌─────────────────────────────────────────────────────────────────────────────────────────────\033[0m")
        print(f"\033[1;34m│ ✨ [Gemini Stream] Modèle : \033[1;36m{self.model}\033[0m")
        print(f"\033[1;34m│ 📥 Prompt : \033[0m{preview}...")
        print(f"\033[1;34m├┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\033[0m")
        print(f"\033[1;36m│ 🎙️ [Stream Gemini en direct] :\033[0m\n", flush=True)

        models_to_try = [self.model] + [m for m in FALLBACK_GEMINI_MODELS if m != self.model]

        if not self.api_key or not self.api_key.startswith("AIzaSy"):
            print(f"\033[1;33m⚠️ [GeminiLLMClient] Clé API Gemini manquante ou invalide (doit débuter par 'AIzaSy'). Bascule stream immédiate sur le secours...\033[0m")
            if self.fallback_client is not None:
                yield from self.fallback_client.generate_stream(
                    prompt=prompt,
                    messages=messages,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return
            raise RuntimeError("Clé Gemini invalide et aucun client de secours disponible.")

        for model_candidate in models_to_try:
            # 1. Essai via SDK genai
            if self.client is not None:
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
                        delta = getattr(chunk, "text", "") or ""
                        if delta:
                            chunk_count += 1
                            sys.stdout.write(delta)
                            sys.stdout.flush()
                            yield delta

                    if chunk_count > 0:
                        elapsed = time.perf_counter() - start_time
                        print(f"\n\n\033[1;34m├┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\033[0m")
                        print(f"\033[1;34m│ ✅ [Gemini SDK Stream] Terminé en \033[1;33m{elapsed:.2f}s\033[0m ({chunk_count} morceaux)")
                        print(f"\033[1;34m└─────────────────────────────────────────────────────────────────────────────────────────────\033[0m\n")
                        return

                except Exception as e_sdk:
                    print(f"\n\033[1;33m│ ⚠️ [Gemini SDK Stream] Échec sur {model_candidate} ({e_sdk}) -> essai REST...\033[0m")

            # 2. Essai via REST SSE direct (zéro dépendance externe)
            try:
                chunk_count = 0
                for delta in self._stream_via_rest(
                    model_name=model_candidate,
                    contents_payload=contents_payload,
                    system_instruction=sys_instruction,
                    temperature=eff_temp,
                    max_tokens=eff_max,
                ):
                    chunk_count += 1
                    sys.stdout.write(delta)
                    sys.stdout.flush()
                    yield delta

                if chunk_count > 0:
                    elapsed = time.perf_counter() - start_time
                    print(f"\n\n\033[1;34m├┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\033[0m")
                    print(f"\033[1;34m│ ✅ [Gemini REST Stream] Terminé en \033[1;33m{elapsed:.2f}s\033[0m ({chunk_count} morceaux)")
                    print(f"\033[1;34m└─────────────────────────────────────────────────────────────────────────────────────────────\033[0m\n")
                    return

            except Exception as e_rest:
                print(f"\n\033[1;33m│ ⚠️ [Gemini REST Stream] Échec sur {model_candidate} ({e_rest}), essai du suivant...\033[0m")
                continue

        # Fallback automatique vers Groq ou Local
        if self.fallback_client is not None:
            print(f"\033[1;33m🔄 [GeminiLLMClient] Bascule stream sur le fallback ({self.fallback_client.__class__.__name__})...\033[0m")
            yield from self.fallback_client.generate_stream(
                prompt=prompt,
                messages=messages,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return

        raise RuntimeError("Échec du streaming Gemini et aucun client de secours disponible.")
