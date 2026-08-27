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
        temperature: float = 0.15,
        top_p: float = 0.9,
        repeat_penalty: float = 1.20,
        frequency_penalty: float = 0.5,
        presence_penalty: float = 0.3,
        max_tokens: int | None = None,  # None ou 0 = illimité, le modèle s'arrête naturellement
    ):
        path = Path(model_path)

        # Fallback de modèle si le fichier spécifié n'existe pas
        if not path.exists():
            models_dir = path.parent
            candidates = [
                "qwen2.5-14b-instruct-q4_k_m.gguf",
                "qwen2.5-7b-instruct-q5_k_m.gguf",
                "qwen2.5-7b-instruct-q4_k_m.gguf",
                "qwen2.5-3b-instruct-q4_k_m.gguf",
                "qwen2.5-1.5b-instruct-q4_k_m.gguf",
            ]
            found = False
            for candidate in candidates:
                if (models_dir / candidate).exists():
                    path = models_dir / candidate
                    found = True
                    break
            if not found and models_dir.exists():
                ggufs = list(models_dir.glob("*.gguf"))
                if ggufs:
                    path = ggufs[0]
                    found = True
            if not found:
                raise FileNotFoundError(
                    f"Modèle GGUF introuvable : {path}"
                )

        self.model_path = str(path)
        self.temperature = temperature
        self.top_p = top_p
        self.repeat_penalty = repeat_penalty
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        # max_tokens : 320 tokens = permet une réponse complète et dense (2 à 4 phrases ou listes de principes)
        # sans jamais couper au milieu d'un mot ou d'une phrase.
        self._max_tokens: int | None = max_tokens if (max_tokens is not None and max_tokens > 0) else 320

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
            # Apple Silicon : arm64 est le vrai identifiant sur macOS
            is_apple_silicon = (
                "arm64" in machine
                or "arm" in machine
                or "m1" in machine
                or "m2" in machine
                or "m3" in machine
                or "m4" in machine
            )
            if is_apple_silicon:
                # M-series : threads = tous les P-cores (performance cores)
                threads = min(8, max(4, cpu_count))
            elif machine in {"x86_64", "amd64"}:
                # Intel HT : utiliser UNIQUEMENT les cœurs physiques (cpu_count // 2)
                # Évite la contention de cache L1/L2 et booste la génération jusqu'à 8-10+ tokens/s.
                physical_cores = max(2, cpu_count // 2) if cpu_count > 2 else cpu_count
                threads = min(6, physical_cores)
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
            # Apple Silicon (arm64) → mémoire unifiée, Metal très rapide
            is_apple_silicon = (
                "arm64" in machine
                or "arm" in machine
                or "m1" in machine
                or "m2" in machine
                or "m3" in machine
                or "m4" in machine
            )
            if is_apple_silicon:
                return -1  # Toutes les couches sur Metal GPU
            # Intel Mac (x86_64) → GPU discret non unifié, CPU pur est plus rapide
            return 0

        # Linux : Vérifier la présence d'un GPU NVIDIA (CUDA / RunPod / Colab / AWS)
        if sys_name == "Linux":
            try:
                import torch
                if torch.cuda.is_available() and torch.cuda.device_count() > 0:
                    return -1  # Toutes les couches sur GPU NVIDIA CUDA
            except Exception:
                pass
            if os.path.exists("/proc/driver/nvidia") or os.environ.get("CUDA_VISIBLE_DEVICES"):
                return -1

        # Raspberry Pi (ARM Cortex A72/A76) / CPU pur
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
        model_name = Path(self.model_path).name
        print(f"\033[35m⏱️  [local_client.py]\033[0m Appel LLM synchrone ({model_name})...")

        # Stop sequences sûres : bloquent la fuite de balises de fin de tour ou séparateurs
        stop_sequences = [
            "<|im_end|>",
            "<|endoftext|>",
            "<|im_start|>",
            "</s>",
            "---",
            "QUESTION DE L'ÉLÈVE :",
            "EXTRAITS DU COURS",
        ]

        raw_response = self.llm.create_chat_completion(
            messages=cast(Any, messages),
            temperature=self.temperature,
            top_p=self.top_p,
            repeat_penalty=self.repeat_penalty,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            max_tokens=self._max_tokens,
            stop=stop_sequences,
        )
        response: dict[str, Any] = cast(dict[str, Any], raw_response)

        elapsed = time.perf_counter() - start_time
        usage = response.get("usage", {})
        completion_tokens = usage.get("completion_tokens", 0)
        tokens_per_second = completion_tokens / max(elapsed, 0.001)

        print(
            f"\033[35m⏱️  [local_client.py]\033[0m LLM génération : \033[1;32m{completion_tokens} tokens\033[0m "
            f"en \033[1;33m{elapsed:.2f}s\033[0m (\033[1;36m{tokens_per_second:.2f} tokens/s\033[0m)"
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
        first_token_time: float | None = None
        token_count = 0
        model_name = Path(self.model_path).name

        if messages is None:
            if prompt is None:
                raise ValueError("Soit 'prompt' soit 'messages' doit être fourni.")
            messages = self._build_messages(prompt, system_prompt)

        print(f"\033[35m⏱️  [local_client.py]\033[0m Ingestion du prompt par llama.cpp ({model_name})...")

        # Stop sequences sûres : bloquent la fuite de balises de fin de tour ou séparateurs
        stop_sequences = [
            "<|im_end|>",
            "<|endoftext|>",
            "<|im_start|>",
            "</s>",
            "---",
            "QUESTION DE L'ÉLÈVE :",
            "EXTRAITS DU COURS",
        ]

        raw_stream = self.llm.create_chat_completion(
            messages=cast(Any, messages),
            temperature=self.temperature,
            top_p=self.top_p,
            repeat_penalty=self.repeat_penalty,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            max_tokens=self._max_tokens,
            stop=stop_sequences,
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
                if first_token_time is None:
                    first_token_time = time.perf_counter()
                    ttft = first_token_time - start_time
                    print(f"\033[35m⏱️  [local_client.py]\033[0m Premier token émis (TTFT - Time To First Token) en \033[1;33m{ttft:.4f}s\033[0m")
                token_count += 1
                yield content

        now = time.perf_counter()
        total_elapsed = now - start_time
        decode_elapsed = (now - first_token_time) if first_token_time else total_elapsed
        ttft = (first_token_time - start_time) if first_token_time else 0.0

        if token_count > 0:
            pure_speed = token_count / max(decode_elapsed, 0.001)
            print(
                f"\n\033[35m⏱️  [local_client.py]\033[0m Stream LLM terminé : \033[1;32m{token_count} tokens\033[0m "
                f"générés en \033[1;33m{decode_elapsed:.2f}s\033[0m (\033[1;36m{pure_speed:.2f} tokens/s\033[0m | TTFT: \033[1;33m{ttft:.4f}s\033[0m | total: \033[1;33m{total_elapsed:.2f}s\033[0m)"
            )