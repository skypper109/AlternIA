import json
import time
import uuid
from pathlib import Path
from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchAny,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)

from alternia.config.settings import PROJECT_ROOT, settings
from alternia.core.models import KnowledgeChunk, StudentClass, Subject
from alternia.rag.vector_store import (
    CLASS_HIERARCHY,
    SERIES_PREREQUISITES,
    SUBJECT_SYNONYMS,
    is_chunk_allowed,
)


DEFAULT_QDRANT_PATH = (
    PROJECT_ROOT
    / "ai-engine"
    / "data"
    / "qdrant"
)


class QdrantVectorStore:
    """
    Base vectorielle haute performance pour AlternIA reposant sur Qdrant.
    Supporte le stockage disque persistant (embarqué sans daemon obligatoire),
    ainsi que la connexion à un serveur Qdrant distant ou le mode mémoire.
    
    Fournit l'API standard attendue par KnowledgeIndexer et SemanticRetriever :
    - add(document, vector)
    - add_many(documents, vectors)
    - search(query_vector, top_k, student_class, student_series, subject, allow_fallback)
    - remove_by_source(source)
    - has_source(source)
    - count
    - clear()
    - save()
    - load()
    """

    COLLECTION_NAME = "alternia_knowledge"

    @staticmethod
    def _point_id(chunk_id: str) -> str:
        """Génère un UUID déterministe valide pour Qdrant à partir de l'identifiant du chunk."""
        return str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"alternia:chunk:{chunk_id}",
            )
        )

    def __init__(
        self,
        storage_path: str | Path | None = None,
        location: str | None = None,
        url: str | None = None,
        dimension: int = 384,
        collection_name: str = COLLECTION_NAME,
    ):
        self.dimension = dimension
        self.collection_name = collection_name

        if location == ":memory:":
            self.client = QdrantClient(location=":memory:")
            self.storage_path = None
        elif url or getattr(settings, "vector_db_url", None):
            target_url = url or settings.vector_db_url
            self.client = QdrantClient(url=target_url)
            self.storage_path = None
        else:
            path = Path(storage_path or DEFAULT_QDRANT_PATH)
            path.mkdir(parents=True, exist_ok=True)
            self.storage_path = path
            self.client = QdrantClient(path=str(self.storage_path))

        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Vérifie ou initialise la collection Qdrant et ses index de filtrage."""
        collections = self.client.get_collections()
        names = {col.name for col in collections.collections}

        if self.collection_name not in names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.dimension,
                    distance=Distance.COSINE,
                ),
            )

        # Index de métadonnées pour accélération des filtres sur serveur Qdrant
        if self.storage_path is None:
            try:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    for field in ["student_class", "series", "subject", "source"]:
                        self.client.create_payload_index(
                            collection_name=self.collection_name,
                            field_name=field,
                            field_schema=PayloadSchemaType.KEYWORD,
                        )
            except Exception:
                pass

    # =========================================================
    # CONVERSION PAYLOAD <-> KNOWLEDGECHUNK
    # =========================================================

    def _document_to_payload(self, document: KnowledgeChunk) -> dict:
        s_cls = (
            document.student_class.value
            if hasattr(document.student_class, "value")
            else str(document.student_class)
        )
        s_subj = (
            document.subject.value
            if hasattr(document.subject, "value")
            else str(document.subject)
        ) if document.subject else "autre"

        return {
            "chunk_id": document.chunk_id,
            "content": document.content,
            "student_class": s_cls.strip().lower(),
            "series": (document.series or "generale").strip().lower(),
            "subject": s_subj.strip().lower(),
            "chapter": document.chapter or "Non défini",
            "lesson": document.lesson or "",
            "section": document.section or "",
            "title": document.title or "Sans titre",
            "source": str(document.source),
            "source_version": document.source_version or "",
            "page_start": document.page_start or 1,
            "page_end": document.page_end or 1,
        }

    def _point_to_knowledge_chunk(self, point) -> KnowledgeChunk:
        payload = point.payload or {}
        return KnowledgeChunk(
            chunk_id=payload.get("chunk_id", str(point.id)),
            content=payload.get("content", ""),
            student_class=StudentClass.from_str(payload.get("student_class")) or StudentClass.TEN,
            series=payload.get("series") or "generale",
            subject=Subject.from_str(payload.get("subject")) or Subject.AUTRE,
            chapter=payload.get("chapter", "Non défini"),
            lesson=payload.get("lesson") or None,
            section=payload.get("section") or None,
            title=payload.get("title", "Sans titre"),
            source=payload.get("source", ""),
            source_version=payload.get("source_version") or None,
            page_start=payload.get("page_start", 1),
            page_end=payload.get("page_end", 1),
        )

    # =========================================================
    # AJOUT
    # =========================================================

    def add(
        self,
        document: KnowledgeChunk,
        vector: list[float],
    ) -> None:
        if not vector:
            raise ValueError("Impossible d'ajouter un vecteur vide.")
        if len(vector) != self.dimension:
            raise ValueError(
                f"Dimension attendue : {self.dimension}, reçu : {len(vector)}"
            )

        point = PointStruct(
            id=self._point_id(document.chunk_id),
            vector=vector,
            payload=self._document_to_payload(document),
        )

        self.client.upsert(
            collection_name=self.collection_name,
            points=[point],
        )

    def add_many(
        self,
        documents: list[KnowledgeChunk],
        vectors: list[list[float]],
        batch_size: int = 250,
    ) -> None:
        if len(documents) != len(vectors):
            raise ValueError(
                "Le nombre de documents doit correspondre au nombre de vecteurs."
            )

        if not documents:
            return

        points = [
            PointStruct(
                id=self._point_id(doc.chunk_id),
                vector=vec,
                payload=self._document_to_payload(doc),
            )
            for doc, vec in zip(documents, vectors)
        ]

        # Envoi par lots pour fluidité mémoire
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            self.client.upsert(
                collection_name=self.collection_name,
                points=batch,
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
        if top_k <= 0 or not query_vector:
            return []

        t0 = time.perf_counter()

        s_cls = (
            getattr(student_class, "value", str(student_class)).strip().lower()
            if student_class is not None
            else None
        )
        s_ser = str(student_series).strip().lower() if student_series else None
        s_subj = (
            getattr(subject, "value", str(subject)).strip().lower()
            if subject is not None
            else None
        )

        # Construction des filtres Qdrant
        allowed_classes = CLASS_HIERARCHY.get(s_cls, [s_cls]) if s_cls else None

        allowed_subjects = None
        if s_subj and s_subj not in {"general", "generale", "toutes", "all", "autre", "none", ""}:
            allowed_subjects = list(SUBJECT_SYNONYMS.get(s_subj, {s_subj}))

        def build_filter(use_subject: bool, use_class: bool) -> Optional[Filter]:
            conditions = []
            if use_class and allowed_classes:
                conditions.append(
                    FieldCondition(
                        key="student_class",
                        match=MatchAny(any=allowed_classes),
                    )
                )

            if use_subject and allowed_subjects:
                conditions.append(
                    FieldCondition(
                        key="subject",
                        match=MatchAny(any=allowed_subjects),
                    )
                )

            if not conditions:
                return None
            return Filter(must=conditions)

        # Tentative 1 : filtrage strict (classe + matière)
        limit_to_fetch = max(top_k * 3, 50)
        query_filter = build_filter(use_subject=True, use_class=True)

        res = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=limit_to_fetch,
            with_payload=True,
        )
        raw_points = res.points

        # Filtrage fin série en Python
        candidates = []
        for pt in raw_points:
            doc = self._point_to_knowledge_chunk(pt)
            if not is_chunk_allowed(
                chunk_class=doc.student_class,
                chunk_series=doc.series,
                student_class=student_class,
                student_series=student_series,
            ):
                continue
            candidates.append((doc, float(pt.score or 0.0)))
            if len(candidates) >= top_k:
                break

        # Fallback 1 : si aucun résultat, relâcher le filtre de matière
        if allow_fallback and len(candidates) == 0 and allowed_subjects:
            fallback_filter = build_filter(use_subject=False, use_class=True)
            res_fb = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=fallback_filter,
                limit=limit_to_fetch,
                with_payload=True,
            )
            for pt in res_fb.points:
                doc = self._point_to_knowledge_chunk(pt)
                if not is_chunk_allowed(
                    chunk_class=doc.student_class,
                    chunk_series=doc.series,
                    student_class=student_class,
                    student_series=student_series,
                ):
                    continue
                candidates.append((doc, float(pt.score or 0.0)))
                if len(candidates) >= top_k:
                    break

        # Fallback 2 : si toujours aucun résultat, recherche globale sans filtre
        if allow_fallback and len(candidates) == 0:
            res_all = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=top_k,
                with_payload=True,
            )
            for pt in res_all.points:
                candidates.append((self._point_to_knowledge_chunk(pt), float(pt.score or 0.0)))

        dt = time.perf_counter() - t0
        print(f"\033[36m⏱️  [qdrant_store.py]\033[0m Recherche Qdrant ({len(candidates)} résultats, top {top_k}) en \033[1;33m{dt:.4f}s\033[0m")

        return candidates[:top_k]

    # =========================================================
    # MAINTENANCE & SOURCES
    # =========================================================

    def remove_by_source(self, source: str | Path) -> int:
        """Supprime tous les chunks provenant d'un document PDF donné."""
        src_str = str(source)
        # Compter les points à supprimer
        scroll_filter = Filter(
            must=[FieldCondition(key="source", match=MatchValue(value=src_str))]
        )
        count_res = self.client.count(
            collection_name=self.collection_name,
            count_filter=scroll_filter,
        )
        total_to_remove = count_res.count

        if total_to_remove > 0:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=FilterSelector(filter=scroll_filter),
            )

        return total_to_remove

    def has_source(self, source: str | Path) -> bool:
        """Vérifie si la source a déjà au moins un chunk dans Qdrant."""
        src_str = str(source)
        scroll_filter = Filter(
            must=[FieldCondition(key="source", match=MatchValue(value=src_str))]
        )
        points, _ = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=scroll_filter,
            limit=1,
        )
        return len(points) > 0

    def clear(self) -> None:
        """Vide complètement la collection Qdrant."""
        self.client.delete_collection(collection_name=self.collection_name)
        self._ensure_collection()

    def save(self) -> None:
        """Qdrant persiste immédiatement sur disque. Cette méthode garantit l'alignement API."""
        pass

    def load(self) -> bool:
        """Vérifie si des documents sont présents dans la collection Qdrant."""
        try:
            return self.count > 0
        except Exception:
            return False

    @property
    def count(self) -> int:
        """Nombre total de points stockés dans la collection."""
        try:
            res = self.client.count(collection_name=self.collection_name)
            return res.count
        except Exception:
            return 0

    def close(self) -> None:
        """Ferme la connexion Qdrant."""
        self.client.close()

    # =========================================================
    # MIGRATION DEPUIS VECTOR_STORE.JSON
    # =========================================================

    def migrate_from_json(self, json_path: Path | str | None = None) -> int:
        """
        Migre les vecteurs et chunks existants depuis vector_store.json vers Qdrant.
        Permet de réutiliser instantanément les embeddings déjà calculés.
        """
        target_path = Path(
            json_path
            or (
                PROJECT_ROOT
                / "ai-engine"
                / "data"
                / "index"
                / "vector_store.json"
            )
        )
        if not target_path.exists():
            return 0

        print(f"📦 [Qdrant] Migration des chunks existants depuis {target_path}...")
        content = target_path.read_text(encoding="utf-8")
        if not content.strip():
            return 0

        records = json.loads(content)
        documents = []
        vectors = []

        for item in records:
            doc = KnowledgeChunk.model_validate(item["document"])
            vec = [float(v) for v in item["vector"]]
            documents.append(doc)
            vectors.append(vec)

        if documents:
            self.add_many(documents, vectors, batch_size=250)
            print(f"✅ [Qdrant] {len(documents)} chunks migrés avec succès dans Qdrant.")

        return len(documents)
