from alternia.core.pedagogical_chunk import PedagogicalChunk
from alternia.embeddings.service import EmbeddingService
from alternia.indexing.knowledge_indexer import KnowledgeIndexer
from alternia.ingestion.metadata.structure import PedagogicalMetadata
from alternia.retrieval.qdrant_store import QdrantVectorStore
from alternia.retrieval.semantic_retriever import SemanticRetriever


def make_chunk(
    chunk_id,
    student_class,
    subject,
    chapter,
    lesson,
    content,
):

    return PedagogicalChunk(
        chunk_id=chunk_id,
        content=content,
        metadata=PedagogicalMetadata(
            student_class=student_class,
            subject=subject,
            chapter=chapter,
            lesson=lesson,
            section="cours",
        ),
        source_document="programme.pdf",
        page_start=1,
        page_end=2,
    )


def test_real_semantic_retrieval():

    embedding_service = EmbeddingService()

    vector_store = QdrantVectorStore(
        location=":memory:",
    )

    indexer = KnowledgeIndexer(
        embedding_service,
        vector_store,
    )

    retriever = SemanticRetriever(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )

    try:

        chunks = [
            make_chunk(
                chunk_id="chunk-1",
                student_class="10eme",
                subject="mathematiques",
                chapter="algebre",
                lesson="equations",
                content=(
                    "Pour résoudre une équation du "
                    "premier degré ax + b = 0, on "
                    "isole la variable x en "
                    "soustrayant b puis en divisant "
                    "par a. La solution est alors "
                    "x = -b / a."
                ),
            ),
            make_chunk(
                chunk_id="chunk-2",
                student_class="10eme",
                subject="mathematiques",
                chapter="geometrie",
                lesson="pythagore",
                content=(
                    "Le théorème de Pythagore énonce "
                    "que dans un triangle rectangle, le "
                    "carré de l'hypoténuse est égal à "
                    "la somme des carrés des deux "
                    "autres côtés : AB² + AC² = BC²."
                ),
            ),
            make_chunk(
                chunk_id="chunk-3",
                student_class="10eme",
                subject="physique",
                chapter="electricite",
                lesson="loi_ohm",
                content=(
                    "La loi d'Ohm relie la tension U, "
                    "l'intensité I et la résistance R "
                    "selon la formule U = R * I. Elle "
                    "s'applique aux conducteurs "
                    "ohmiques."
                ),
            ),
            make_chunk(
                chunk_id="chunk-4",
                student_class="11eme",
                subject="mathematiques",
                chapter="analyse",
                lesson="derivation",
                content=(
                    "La dérivée d'une fonction f en un "
                    "point mesure le taux de variation "
                    "instantané de la fonction. Elle est "
                    "notée f'(x)."
                ),
            ),
            make_chunk(
                chunk_id="chunk-5",
                student_class="10eme",
                subject="mathematiques",
                chapter="algebre",
                lesson="equations_exemples",
                content=(
                    "Exemple de résolution : 2x + 4 = 0 "
                    "donne 2x = -4 donc x = -2. On peut "
                    "vérifier en remplaçant x par -2."
                ),
            ),
        ]

        # -----------------------------------------------------
        # Indexation
        # -----------------------------------------------------

        indexer.index_chunks(chunks)

        # -----------------------------------------------------
        # Requête de recherche
        # -----------------------------------------------------

        results = retriever.search(
            query="Comment résoudre une équation ?",
            student_class="10eme",
            subject="mathematiques",
            top_k=3,
        )

        # -----------------------------------------------------
        # Vérification
        # -----------------------------------------------------

        assert len(results) > 0

        for result in results:

            payload = result.payload
            assert payload is not None

            assert (
                payload.get("student_class")
                == "10eme"
            )

            assert (
                payload.get("subject")
                == "mathematiques"
            )

    finally:

        vector_store.close()