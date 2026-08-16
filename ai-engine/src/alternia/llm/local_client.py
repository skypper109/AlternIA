import os
from pathlib import Path
import time
from typing import Any, Iterator, cast

from alternia.llm.client import LLMClient


class LocalLLMClient(LLMClient):
    """
    Client LLM local basé sur llama.cpp.

    Le modèle est chargé localement depuis un fichier GGUF.
    Cette implémentation est optimisée pour de faibles latences
    sur Apple Silicon, Linux et Raspberry Pi 4/5.
    """

    def __init__(
        self,
        model_path: str,
        *,
        n_ctx: int = 4096,
        n_threads: int | None = None,
        n_batch: int = 512,
        n_gpu_layers: int | None = None,
        temperature: float = 0.2,
        top_p: float = 0.9,
        repeat_penalty: float = 1.15,
        max_tokens: int | None = None,  # None ou 0 = illimité, le modèle s'arrête naturellement
    ):
        path = Path(model_path)

        # Fallback de modèle si le fichier spécifié n'existe pas
        if not path.exists():
            models_dir = path.parent
            if (models_dir / "qwen2.5-1.5b-instruct-q4_k_m.gguf").exists():
                path = models_dir / "qwen2.5-1.5b-instruct-q4_k_m.gguf"
            elif (models_dir / "qwen2.5-3b-instruct-q4_k_m.gguf").exists():
                path = models_dir / "qwen2.5-3b-instruct-q4_k_m.gguf"
            else:
                raise FileNotFoundError(
                    f"Modèle GGUF introuvable : {path}"
                )

        self.model_path = str(path)
        self.temperature = temperature
        self.top_p = top_p
        self.repeat_penalty = repeat_penalty
        # max_tokens : 240 tokens par défaut (permet une explication complète en ~15s max sur CPU)
        self._max_tokens: int | None = max_tokens if (max_tokens is not None and max_tokens > 0) else 240

        # Détection du nombre optimal de threads :
        # - Sur x86/Intel (Hyperthreading) : utiliser les cœurs physiques (cpu_count // 2 = 4)
        #   évite la contention de cache et booste la vitesse de 10 à 15+ tokens/s.
        # - Pour le prompt initial (n_threads_batch) : utiliser tous les cœurs pour évaluer le prompt en <0.5s.
        cpu_count = os.cpu_count() or 4
        if n_threads is not None:
            threads = n_threads
        else:
            import platform
            machine = platform.machine().lower()
            if "arm" in machine or "m1" in machine or "m2" in machine or "m3" in machine or "m4" in machine:
                threads = min(6, max(2, cpu_count))
            elif machine in {"x86_64", "amd64", "i386", "i686"}:
                threads = max(2, min(4, cpu_count // 2))
            else:
                threads = min(4, max(2, cpu_count))

        threads_batch = cpu_count

        # Détection intelligente de l'accélération matérielle
        # Sur Raspberry Pi 4/5 ou Mac Intel (GPU discret non unifié), n_gpu_layers=0 (CPU pur) est le plus rapide
        gpu_layers = self._detect_optimal_gpu_layers(n_gpu_layers)

        try:
            from llama_cpp import Llama
        except ImportError:
            raise ImportError(
                "Le paquet llama-cpp-python n'est pas installé. "
                "Installez-le avec : pip install llama-cpp-python"
            )

        try:
            self.llm: Any = Llama(
                model_path=self.model_path,
                n_ctx=n_ctx,
                n_threads=threads,
                n_threads_batch=threads_batch,
                n_batch=n_batch,
                n_gpu_layers=gpu_layers,
                verbose=False,
            )
        except Exception:
            # Repli CPU pur en cas d'échec de chargement
            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=n_ctx,
                n_threads=threads,
                n_threads_batch=threads_batch,
                n_batch=n_batch,
                n_gpu_layers=0,
                verbose=False,
            )

    @staticmethod
    def _detect_optimal_gpu_layers(user_gpu_layers: int | None) -> int:
        """Détermine si l'offload GPU est bénéfique sur la machine courante."""
        if user_gpu_layers is not None:
            return user_gpu_layers

        import platform
        sys_name = platform.system()
        machine = platform.machine().lower()

        if sys_name == "Darwin":
            # Apple Silicon (M1/M2/M3/M4) -> mémoire unifiée très rapide avec Metal
            if "arm" in machine or "m1" in machine or "m2" in machine or "m3" in machine:
                return -1
            # Intel Mac avec GPU discret -> le CPU pur est 2.5x plus rapide car pas de goulot PCIe
            return 0

        # Linux / Raspberry Pi 4/5 (ARM Cortex A72 / A76) -> CPU pur
        return 0

    def _build_messages(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> list[dict[str, str]]:

        messages: list[dict[str, str]] = []

        if system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        return messages

    def generate(
        self,
        prompt: str | None = None,
        *,
        messages: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
    ) -> str:
        if messages is None:
            if prompt is None:
                raise ValueError("Soit 'prompt' soit 'messages' doit être fourni.")
            messages = self._build_messages(prompt, system_prompt)

        start_time = time.perf_counter()

        raw_response = self.llm.create_chat_completion(
            messages=cast(Any, messages),
            temperature=self.temperature,
            top_p=self.top_p,
            repeat_penalty=self.repeat_penalty,
            max_tokens=self._max_tokens,  # None = illimité
        )
        response: dict[str, Any] = cast(dict[str, Any], raw_response)

        elapsed = time.perf_counter() - start_time

        usage = response.get("usage", {})

        print(
            f"\n[LLM] génération : {elapsed:.2f}s"
        )

        completion_tokens = usage.get(
            "completion_tokens",
            0,
        )

        if completion_tokens:
            print(
                f"[LLM] tokens générés : {completion_tokens}"
            )
            tokens_per_second = (
                completion_tokens / max(elapsed, 0.001)
            )

            print(
                f"[LLM] vitesse : "
                f"{tokens_per_second:.2f} tokens/s"
            )

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
    ) -> Iterator[str]:
        """
        Génère la réponse token par token.

        Permet à l'interface et au TTS de commencer
        à travailler avant que toute la réponse soit terminée.
        """

        start_time = time.perf_counter()
        token_count = 0

        if messages is None:
            if prompt is None:
                raise ValueError("Soit 'prompt' soit 'messages' doit être fourni.")
            messages = self._build_messages(prompt, system_prompt)

        raw_stream = self.llm.create_chat_completion(
            messages=cast(Any, messages),
            temperature=self.temperature,
            top_p=self.top_p,
            repeat_penalty=self.repeat_penalty,
            max_tokens=self._max_tokens,  # None = illimité
            stream=True,
        )

        for chunk_item in raw_stream:
            if not isinstance(chunk_item, dict):
                continue
            chunk: dict[str, Any] = chunk_item

            choices = chunk.get(
                "choices",
                [],
            )

            if not choices:
                continue

            first_choice = choices[0]
            if not isinstance(first_choice, dict):
                continue

            delta = first_choice.get(
                "delta",
                {},
            )

            if not isinstance(delta, dict):
                continue

            content = delta.get(
                "content",
                "",
            )

            if content:
                token_count += 1
                yield content

        elapsed = time.perf_counter() - start_time

        if token_count > 0:
            speed = token_count / max(elapsed, 0.001)
            print(
                f"\n[LLM-stream] {token_count} tokens en "
                f"{elapsed:.2f}s ({speed:.2f} tokens/s)"
            )