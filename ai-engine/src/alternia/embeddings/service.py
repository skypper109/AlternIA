from pathlib import Path

from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """
    Génère les embeddings pour AlternIA.

    Le modèle est chargé une seule fois afin d'éviter
    de recharger le modèle à chaque requête.
    """

    def __init__(
        self,
        model_path: str = "models/embeddings/all-MiniLM-L6-v2",
    ):
        self.model_path = Path(model_path)

        if not self.model_path.exists():
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
        return self.model.get_sentence_embedding_dimension()