from dataclasses import dataclass

import numpy as np

from alternia.core.models import KnowledgeChunk


@dataclass
class VectorRecord:
    document: KnowledgeChunk
    vector: list[float]


class LocalVectorStore:

    def __init__(self):
        self.records: list[VectorRecord] = []

    def add(
        self,
        document: KnowledgeChunk,
        vector: list[float],
    ) -> None:

        self.records.append(
            VectorRecord(
                document=document,
                vector=vector,
            )
        )

    def add_many(
        self,
        documents: list[KnowledgeChunk],
        vectors: list[list[float]],
    ) -> None:

        if len(documents) != len(vectors):
            raise ValueError(
                "Le nombre de documents doit correspondre "
                "au nombre de vecteurs."
            )

        for document, vector in zip(documents, vectors):
            self.add(document, vector)

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        student_class=None,
        subject=None,
    ) -> list[tuple[KnowledgeChunk, float]]:

        query = np.array(query_vector)

        candidates = []

        for record in self.records:

            document = record.document

            if student_class is not None:
                if document.student_class != student_class:
                    continue

            if subject is not None:
                if document.subject != subject:
                    continue

            document_vector = np.array(record.vector)

            score = float(
                np.dot(query, document_vector)
            )

            candidates.append(
                (document, score)
            )

        candidates.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        return candidates[:top_k]