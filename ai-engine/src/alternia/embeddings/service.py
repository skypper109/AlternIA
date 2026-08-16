from pathlib import Path

from sentence_transformers import SentenceTransformer


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


class EmbeddingService:
    """
    Génère les embeddings pour AlternIA.

    Le modèle multilingue est chargé une seule fois afin d'éviter
    de recharger le modèle à chaque requête.
    """

    def __init__(
        self,
        model_path: str | Path | None = None,
    ):
        if model_path is not None:
            self.model_path = Path(model_path)
            if not self.model_path.is_absolute():
                self.model_path = PROJECT_ROOT / self.model_path
        elif MULTILINGUAL_MODEL_PATH.exists():
            self.model_path = MULTILINGUAL_MODEL_PATH
        elif LEGACY_MODEL_PATH.exists():
            self.model_path = LEGACY_MODEL_PATH
        else:
            self.model_path = MULTILINGUAL_MODEL_PATH

        if not self.model_path.exists():
            try:
                self.model = SentenceTransformer(
                    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
                )
                self.model.save(str(MULTILINGUAL_MODEL_PATH))
                self.model_path = MULTILINGUAL_MODEL_PATH
                return
            except Exception:
                raise FileNotFoundError(
                    f"Embedding model not found: {self.model_path}"
                )

        self.model = SentenceTransformer(
            str(self.model_path)
        )

    def encode(
        self,
        text: str,
    ) -> list[float]:

        if not text or not text.strip():
            raise ValueError(
                "Cannot generate embedding for empty text."
            )

        vector = self.model.encode(
            text,
            normalize_embeddings=True,
        )

        return vector.tolist()

    def encode_many(
        self,
        texts: list[str],
    ) -> list[list[float]]:

        if not texts:
            return []

        if any(
            not text or not text.strip()
            for text in texts
        ):
            raise ValueError(
                "Cannot generate embeddings for empty text."
            )

        vectors = self.model.encode(
            texts,
            normalize_embeddings=True,
        )

        return vectors.tolist()

    @property
    def dimension(self) -> int:
        dim = self.model.get_sentence_embedding_dimension()
        return int(dim) if dim is not None else 384