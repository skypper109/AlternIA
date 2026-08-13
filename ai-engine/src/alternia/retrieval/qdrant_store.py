import uuid
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from alternia.core.pedagogical_chunk import (
    PedagogicalChunk,
)


class QdrantVectorStore:
    """
    Couche de persistance vectorielle d'AlternIA.

    Responsabilités :
    - créer la collection ;
    - stocker les embeddings ;
    - stocker les métadonnées pédagogiques ;
    - rechercher les chunks similaires ;
    - filtrer par classe et matière.
    """

    COLLECTION_NAME = "alternia_knowledge"

    @staticmethod
    def _point_id(chunk_id: str) -> str:
        return str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"alternia:chunk:{chunk_id}",
            )
        )

    def __init__(
        self,
        path: str = "data/qdrant",
        dimension: int = 384,
    ):

        self.path = Path(path)

        self.path.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.client = QdrantClient(
            path=str(self.path)
        )

        self.dimension = dimension

        self._ensure_collection()

    def _ensure_collection(self) -> None:

        collections = (
            self.client.get_collections()
        )

        names = {
            collection.name
            for collection in collections.collections
        }

        if self.COLLECTION_NAME not in names:

            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.dimension,
                    distance=Distance.COSINE,
                ),
            )

    def add(
        self,
        chunk: PedagogicalChunk,
        embedding: list[float],
    ) -> None:

        if len(embedding) != self.dimension:
            raise ValueError(
                f"Expected embedding dimension "
                f"{self.dimension}, "
                f"got {len(embedding)}"
            )

        payload = {
            "content": chunk.content,

            "student_class": (
                chunk.metadata.student_class
            ),

            "subject": (
                chunk.metadata.subject
            ),

            "chapter": (
                chunk.metadata.chapter
            ),

            "lesson": (
                chunk.metadata.lesson
            ),

            "section": (
                chunk.metadata.section
            ),

            "source_document": (
                chunk.source_document
            ),

            "page_start": (
                chunk.page_start
            ),

            "page_end": (
                chunk.page_end
            ),
        }

        point = PointStruct(
            id=self._point_id(chunk.chunk_id),
    vector=embedding,
    payload=payload,
        )

        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=[point],
        )

    def add_many(
        self,
        items: list[
            tuple[PedagogicalChunk, list[float]]
        ],
    ) -> None:

        points = []

        for chunk, embedding in items:

            if len(embedding) != self.dimension:
                raise ValueError(
                    "Invalid embedding dimension."
                )

            points.append(
                PointStruct(
                    id=self._point_id(chunk.chunk_id),
    vector=embedding,
    payload={
        "chunk_id": chunk.chunk_id,
                        "content": chunk.content,
                        "student_class": (
                            chunk.metadata.student_class
                        ),
                        "subject": (
                            chunk.metadata.subject
                        ),
                        "chapter": (
                            chunk.metadata.chapter
                        ),
                        "lesson": (
                            chunk.metadata.lesson
                        ),
                        "section": (
                            chunk.metadata.section
                        ),
                        "source_document": (
                            chunk.source_document
                        ),
                        "page_start": (
                            chunk.page_start
                        ),
                        "page_end": (
                            chunk.page_end
                        ),
                    },
                )
            )

        if points:

            self.client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=points,
            )

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        student_class: str | None = None,
        subject: str | None = None,
    ):

        conditions = []

        if student_class:

            conditions.append(
                FieldCondition(
                    key="student_class",
                    match=MatchValue(
                        value=student_class
                    ),
                )
            )

        if subject:

            conditions.append(
                FieldCondition(
                    key="subject",
                    match=MatchValue(
                        value=subject
                    ),
                )
            )

        query_filter = None

        if conditions:

            query_filter = Filter(
                must=conditions
            )

        results = self.client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=query_embedding,
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
        )

        return results.points

    def count(self) -> int:

        result = self.client.count(
            collection_name=self.COLLECTION_NAME,
        )

        return result.count
    def close(self) -> None:
        """Ferme proprement le client Qdrant."""
        self.client.close()