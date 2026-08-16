import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from alternia.config.settings import PROJECT_ROOT
from alternia.core.models import KnowledgeChunk


DEFAULT_INDEX_PATH = (
    PROJECT_ROOT
    / "ai-engine"
    / "data"
    / "index"
    / "vector_store.json"
)


@dataclass
class VectorRecord:
    document: KnowledgeChunk
    vector: list[float]


CLASS_HIERARCHY = {
    "10eme": ["10eme"],
    "11eme": ["10eme", "11eme"],
    "12eme": ["10eme", "11eme", "12eme"],
}


def is_chunk_allowed(
    chunk_class,
    chunk_series,
    student_class,
    student_series=None,
) -> bool:
    """
    Règle pédagogique stricte d'AlternIA :
    1. Un élève a UNIQUEMENT accès aux cours de sa classe et des classes inférieures (prérequis).
       -> 10ème : seulement 10ème (jamais 11ème ni 12ème).
       -> 11ème : 11ème (de sa filière) + 10ème (jamais 12ème).
       -> 12ème : 12ème (de sa série) + 11ème + 10ème.
    2. Filtrage strict par série/filière si spécifiée.
    """
    if student_class is None:
        return True

    s_cls = getattr(student_class, "value", str(student_class)).strip().lower()
    c_cls = getattr(chunk_class, "value", str(chunk_class)).strip().lower()

    allowed_classes = CLASS_HIERARCHY.get(s_cls, [s_cls])
    if c_cls not in allowed_classes:
        return False

    if not student_series or student_series in {"generale", "general", "toutes", "all", "none", ""}:
        return True

    s_ser = str(student_series).strip().lower()
    c_ser = str(chunk_series).strip().lower() if chunk_series else "generale"

    # Chunks de 10ème (Tronc Commun) : toujours accessibles comme prérequis
    if c_cls == "10eme":
        return True

    # Chunks généraux de la classe : accessibles
    if c_ser in {"generale", "general", "tronc_commun", ""}:
        return True

    if c_ser == s_ser:
        return True

    # Physique-Chimie partagée en Terminale (TSE & TSExp)
    if c_ser == "tse_tsexp" and s_ser in {"tse", "tsexp", "sciences", "11s"}:
        return True

    # Prérequis 11ème pour un élève de 12ème
    if c_cls == "11eme" and s_cls == "12eme":
        if s_ser in {"tse", "tsexp"} and c_ser in {"11s", "sciences", "generale"}:
            return True
        if s_ser == "tseco" and c_ser in {"11seco", "economie", "generale"}:
            return True
        if s_ser in {"tll", "tss"} and c_ser in {"11l", "lettres", "11seco", "generale"}:
            return True
        return False

    # Filières de 11ème
    if s_cls == "11eme":
        if s_ser in {"11s", "sciences"} and c_ser in {"11s", "sciences"}:
            return True
        if s_ser in {"11seco", "economie", "te"} and c_ser in {"11seco", "economie", "te"}:
            return True
        if s_ser in {"11l", "lettres", "sh", "ll"} and c_ser in {"11l", "lettres", "sh", "ll"}:
            return True
        return False

    # Séries de 12ème (Terminale)
    if s_cls == "12eme" and c_cls == "12eme":
        if s_ser in {"tse", "sciences"} and c_ser in {"tse", "tse_tsexp"}:
            return True
        if s_ser in {"tsexp", "sciences"} and c_ser in {"tsexp", "tse_tsexp"}:
            return True
        if s_ser in {"tseco", "economie"} and c_ser in {"tseco"}:
            return True
        if s_ser in {"tss", "sociales"} and c_ser in {"tss"}:
            return True
        if s_ser in {"tll", "lettres"} and c_ser in {"tll"}:
            return True
        return False

    return False


class LocalVectorStore:
    """
    Stockage vectoriel local persistant d'AlternIA avec partitionnement hiérarchique de classe.
    """

    def __init__(
        self,
        storage_path: str | Path = DEFAULT_INDEX_PATH,
    ):
        self.storage_path = Path(storage_path)

        self.storage_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.records: list[VectorRecord] = []

    # =========================================================
    # AJOUT
    # =========================================================

    def add(
        self,
        document: KnowledgeChunk,
        vector: list[float],
    ) -> None:

        if not vector:
            raise ValueError(
                "Impossible d'ajouter un vecteur vide."
            )

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

        for document, vector in zip(
            documents,
            vectors,
        ):
            self.add(
                document=document,
                vector=vector,
            )

    # =========================================================
    # RECHERCHE
    # =========================================================

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        student_class=None,
        student_series=None,
        subject=None,
        allow_fallback: bool = True,
    ) -> list[tuple[KnowledgeChunk, float]]:

        if top_k <= 0 or not query_vector or not self.records:
            return []

        query = np.asarray(
            query_vector,
            dtype=np.float32,
        )
        norm_query = np.linalg.norm(query)
        if norm_query > 1e-6:
            query = query / norm_query

        matched_records = []
        vectors = []

        for record in self.records:
            document = record.document

            # 1. Vérification de la hiérarchie de classe et série
            if not is_chunk_allowed(
                chunk_class=document.student_class,
                chunk_series=getattr(document, "series", None),
                student_class=student_class,
                student_series=student_series,
            ):
                continue

            # 2. Filtrage matière
            if subject is not None and document.subject != subject:
                continue

            matched_records.append(document)
            vectors.append(record.vector)

        # Si aucun chunk ne correspond à la matière exacte, chercher dans les autres matières
        # autorisées de la même classe ou inférieure (JAMAIS dans une classe supérieure)
        if allow_fallback and len(matched_records) == 0:
            for record in self.records:
                doc = record.document
                if is_chunk_allowed(
                    chunk_class=doc.student_class,
                    chunk_series=getattr(doc, "series", None),
                    student_class=student_class,
                    student_series=student_series,
                ):
                    matched_records.append(doc)
                    vectors.append(record.vector)

        if not matched_records:
            return []

        matrix = np.asarray(vectors, dtype=np.float32)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        norm_matrix = matrix / norms

        scores = np.dot(norm_matrix, query)

        top_indices = np.argsort(scores)[::-1][:top_k]

        candidates = [
            (matched_records[idx], float(scores[idx]))
            for idx in top_indices
        ]

        return candidates

    # =========================================================
    # SUPPRESSION
    # =========================================================

    def remove_by_source(
        self,
        source: str | Path,
    ) -> int:
        """
        Supprime tous les chunks provenant d'un PDF.

        Retourne le nombre de chunks supprimés.
        """

        source = str(Path(source))

        previous_count = len(
            self.records
        )

        self.records = [
            record
            for record in self.records
            if record.document.source != source
        ]

        return (
            previous_count
            - len(self.records)
        )

    def has_source(
        self,
        source: str | Path,
    ) -> bool:
        """
        Vérifie si au moins un chunk provient
        de la source indiquée.
        """

        source = str(Path(source))

        return any(
            record.document.source == source
            for record in self.records
        )

    def clear(self) -> None:
        """
        Vide complètement l'index en mémoire.
        """

        self.records.clear()

    # =========================================================
    # PERSISTANCE
    # =========================================================

    def save(self) -> None:
        """
        Sauvegarde l'intégralité de l'index localement.
        """

        self.storage_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        records = []

        for record in self.records:

            records.append(
                {
                    "document": record.document.model_dump(
                        mode="json"
                    ),
                    "vector": record.vector,
                }
            )

        temporary_path = self.storage_path.with_suffix(
            self.storage_path.suffix + ".tmp"
        )

        temporary_path.write_text(
            json.dumps(
                records,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        temporary_path.replace(
            self.storage_path
        )

    def load(self) -> bool:
        """
        Recharge l'index depuis le disque.

        Retourne True si un index a été chargé,
        False si aucun index n'existe.
        """

        if not self.storage_path.exists():
            return False

        content = self.storage_path.read_text(
            encoding="utf-8",
        )

        if not content.strip():
            return False

        records = json.loads(
            content
        )

        self.records.clear()

        for record in records:

            document = (
                KnowledgeChunk.model_validate(
                    record["document"]
                )
            )

            vector = [
                float(value)
                for value in record["vector"]
            ]

            self.records.append(
                VectorRecord(
                    document=document,
                    vector=vector,
                )
            )

        return True

    # =========================================================
    # INFORMATIONS
    # =========================================================

    @property
    def count(self) -> int:
        """
        Nombre total de chunks actuellement indexés.
        """

        return len(
            self.records
        )