from pathlib import Path

from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parents[4]

DEFAULT_MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "embeddings"
    / "all-MiniLM-L6-v2"
)


class EmbeddingService:
    """
    Service de génération des embeddings d'AlternIA.

    Le modèle est chargé localement afin que le moteur RAG
    puisse fonctionner sans téléchargement au démarrage.
    """

    def __init__(
        self,
        model_path: str | Path = DEFAULT_MODEL_PATH,
    ):
        self.model_path = Path(model_path)

        if not self.model_path.exists():
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

        vectors = self.model.encode(
            texts,
            normalize_embeddings=True,
        )

        return vectors.tolist()