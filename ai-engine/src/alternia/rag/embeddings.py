from pathlib import Path
import os
import time
import torch

from sentence_transformers import SentenceTransformer

# Optimisation multi-cœurs CPU pour SentenceTransformers
try:
    num_threads = min(4, max(2, os.cpu_count() or 4))
    torch.set_num_threads(num_threads)
except Exception:
    pass


PROJECT_ROOT = Path(__file__).resolve().parents[4]

MULTILINGUAL_MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "embeddings"
    / "paraphrase-multilingual-MiniLM-L12-v2"
)

LEGACY_MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "embeddings"
    / "all-MiniLM-L6-v2"
)

DEFAULT_MODEL_PATH = (
    MULTILINGUAL_MODEL_PATH
    if MULTILINGUAL_MODEL_PATH.exists()
    else LEGACY_MODEL_PATH
)


class EmbeddingService:
    """
    Service de génération des embeddings d'AlternIA.

    Utilise un modèle multilingue optimisé pour le français (scolaire/sciences),
    très léger et rapide sur Raspberry Pi 4/5 et CPU/Edge.
    """

    def __init__(
        self,
        model_path: str | Path | None = None,
    ):
        if model_path is not None:
            self.model_path = Path(model_path)
        elif MULTILINGUAL_MODEL_PATH.exists():
            self.model_path = MULTILINGUAL_MODEL_PATH
        elif LEGACY_MODEL_PATH.exists():
            self.model_path = LEGACY_MODEL_PATH
        else:
            self.model_path = MULTILINGUAL_MODEL_PATH

        if not self.model_path.exists():
            try:
                # Tentative de chargement via HuggingFace Hub si non téléchargé
                self.model = SentenceTransformer(
                    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
                )
                self.model.save(str(MULTILINGUAL_MODEL_PATH))
                self.model_path = MULTILINGUAL_MODEL_PATH
                return
            except Exception:
                raise FileNotFoundError(
                    "Modèle embedding introuvable : "
                    f"{self.model_path}"
                )

        self.model = SentenceTransformer(
            str(self.model_path)
        )

    def encode(
        self,
        text: str,
    ) -> list[float]:

        if not text.strip():
            raise ValueError(
                "Impossible de générer un embedding "
                "pour un texte vide."
            )

        t0 = time.perf_counter()
        vector = self.model.encode(
            text,
            normalize_embeddings=True,
        )
        dt = time.perf_counter() - t0
        print(f"\033[36m⏱️  [embeddings.py]\033[0m Encodage sémantique de la requête (dim {len(vector)}) en \033[1;33m{dt:.4f}s\033[0m")

        return vector.tolist()

    def encode_many(
        self,
        texts: list[str],
    ) -> list[list[float]]:

        if not texts:
            return []

        vectors = self.model.encode(
            texts,
            normalize_embeddings=True,
        )

        return vectors.tolist()