from alternia.context.context_builder import ContextBuilder
from alternia.indexing.knowledge_indexer import KnowledgeIndexer
from alternia.retrieval.qdrant_store import QdrantVectorStore
from alternia.retrieval.semantic_retriever import SemanticRetriever
from alternia.embeddings.service import EmbeddingService

from alternia.core.pedagogical_chunk import PedagogicalChunk
from alternia.ingestion.metadata.structure import PedagogicalMetadata

def make_chunk(
    chunk_id: str,
    student_class: str,
    subject: str,
    chapter: str,
    lesson: str,
    content: str,
):
    return PedagogicalChunk(
        chunk_id=chunk_id,
        content=content,
        metadata=PedagogicalMetadata(
            student_class=student_class,
            subject=subject,
            chapter=chapter,
            lesson=lesson,
        ),
        source_document="programme-mali-test.txt",
        page_start=1,
        page_end=1,
    )

def test_real_rag_context_builder():

    embedding_service = EmbeddingService()

    vector_store = QdrantVectorStore(
        path="data/qdrant-context-test",
    )

    try:

        indexer = KnowledgeIndexer(
            embedding_service,
            vector_store,
        )

        chunks = [

            make_chunk(
                "context-10-equations",
                "10eme",
                "mathematiques",
                "algebre",
                "equations",
                (
                    "Une équation du premier degré "
                    "est une égalité contenant "
                    "une inconnue."
                ),
            ),

            make_chunk(
                "context-10-resolution",
                "10eme",
                "mathematiques",
                "algebre",
                "resolution des equations",
                (
                    "Pour résoudre une équation, "
                    "on cherche la valeur de "
                    "l'inconnue qui rend "
                    "l'égalité vraie."
                ),
            ),

            make_chunk(
                "context-10-geometrie",
                "10eme",
                "mathematiques",
                "geometrie",
                "triangles",
                (
                    "Un triangle possède "
                    "trois côtés et "
                    "trois angles."
                ),
            ),

            make_chunk(
                "context-11-equations",
                "11eme",
                "mathematiques",
                "analyse",
                "equations",
                (
                    "Les équations différentielles "
                    "permettent de modéliser "
                    "des phénomènes."
                ),
            ),

            make_chunk(
                "context-10-physique",
                "10eme",
                "physique",
                "mecanique",
                "mouvement",
                (
                    "La mécanique étudie "
                    "le mouvement des objets."
                ),
            ),
        ]

        indexer.index_chunks(chunks)

        retriever = SemanticRetriever(
            embedding_service,
            vector_store,
        )

        results = retriever.retrieve(
            query="Comment résoudre une équation ?",
            student_class="10eme",
            subject="mathematiques",
            top_k=5,
        )

        assert len(results) > 0

        builder = ContextBuilder(
            max_sources=3,
        )

        context = builder.build(
            query="Comment résoudre une équation ?",
            results=results,
            student_class="10eme",
            subject="mathematiques",
        )

        assert not context.is_empty()

        assert len(context.sources) <= 3

        assert (
            context.student_class
            == "10eme"
        )

        assert (
            context.subject
            == "mathematiques"
        )

        assert (
            "équation"
            in context.context_text.lower()
        )

        # Vérification importante :
        # aucune source de 11ème ne doit entrer
        # dans le contexte de la 10ème.

        for source in context.sources:

            assert (
                source.student_class
                == "10eme"
            )

            assert (
                source.subject
                == "mathematiques"
            )

    finally:

        vector_store.close()