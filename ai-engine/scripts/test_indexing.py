from alternia.core.pedagogical_chunk import (
    PedagogicalChunk,
)

from alternia.embeddings.service import (
    EmbeddingService,
)

from alternia.indexing.knowledge_indexer import (
    KnowledgeIndexer,
)

from alternia.retrieval.qdrant_store import (
    QdrantVectorStore,
)


class Metadata:

    student_class = "10eme"
    subject = "mathematiques"
    chapter = "algebre"
    lesson = "equations"
    section = "resolution"


chunk = PedagogicalChunk(
    chunk_id="demo-equation-001",
    content=(
        "Pour résoudre une équation du "
        "premier degré, on cherche la "
        "valeur inconnue."
    ),
    metadata=Metadata(),
    source_document="demo.pdf",
    page_start=1,
    page_end=1,
)


embedding_service = EmbeddingService()

vector_store = QdrantVectorStore()

indexer = KnowledgeIndexer(
    embedding_service,
    vector_store,
)

try:
    indexer.index_chunk(chunk)

    print("INDEXATION OK")
    print(
        "Nombre de chunks :",
        vector_store.count(),
    )

finally:
    vector_store.close()