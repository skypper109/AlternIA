from alternia.core.pedagogical_chunk import PedagogicalChunk

from alternia.embeddings.service import EmbeddingService

from alternia.indexing.knowledge_indexer import KnowledgeIndexer

from alternia.retrieval.qdrant_store import QdrantVectorStore

from alternia.retrieval.semantic_retriever import SemanticRetriever


class Metadata:

    def __init__(
        self,
        student_class,
        subject,
        chapter,
        lesson,
        section,
    ):
        self.student_class = student_class
        self.subject = subject
        self.chapter = chapter
        self.lesson = lesson
        self.section = section


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
        metadata=Metadata(
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
        path="data/qdrant-test",
    )

    try:

        indexer = KnowledgeIndexer(
            embedding_service,
            vector_store,
        )

        chunks = [

            # -------------------------------------------------
            # 10ème — Mathématiques — Équations
            # -------------------------------------------------

            make_chunk(
                "test-10-equations",
                "10eme",
                "mathematiques",
                "algebre",
                "equations",
                (
                    "Une équation du premier degré "
                    "est une égalité contenant "
                    "une inconnue. Pour résoudre une "
                    "équation, on cherche la valeur "
                    "de l'inconnue qui rend l'égalité vraie."
                ),
            ),

            # -------------------------------------------------
            # 10ème — Mathématiques — Géométrie
            # -------------------------------------------------

            make_chunk(
                "test-10-geometrie",
                "10eme",
                "mathematiques",
                "geometrie",
                "triangles",
                (
                    "Un triangle possède trois côtés "
                    "et trois angles. La somme des angles "
                    "d'un triangle est égale à 180 degrés."
                ),
            ),

            # -------------------------------------------------
            # 11ème — Mathématiques — Équations
            # -------------------------------------------------

            make_chunk(
                "test-11-equations",
                "11eme",
                "mathematiques",
                "analyse",
                "equations",
                (
                    "Les équations différentielles "
                    "permettent de modéliser des phénomènes "
                    "qui évoluent dans le temps."
                ),
            ),

            # -------------------------------------------------
            # 10ème — Physique — Mécanique
            # -------------------------------------------------

            make_chunk(
                "test-10-physique",
                "10eme",
                "physique",
                "mecanique",
                "mouvement",
                (
                    "La mécanique étudie le mouvement "
                    "des objets et les forces qui peuvent "
                    "modifier leur mouvement."
                ),
            ),
        ]

        # -----------------------------------------------------
        # Vérification importante
        # -----------------------------------------------------

        assert len(chunks) == 4

        # -----------------------------------------------------
        # INDEXATION
        # -----------------------------------------------------

        indexer.index_chunks(chunks)

        # -----------------------------------------------------
        # RETRIEVER
        # -----------------------------------------------------

        retriever = SemanticRetriever(
            embedding_service,
            vector_store,
        )

        results = retriever.retrieve(
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

            assert (
                payload["student_class"]
                == "10eme"
            )

            assert (
                payload["subject"]
                == "mathematiques"
            )

    finally:

        vector_store.close()