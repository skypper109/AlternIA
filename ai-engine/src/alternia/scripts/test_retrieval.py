from alternia.core.models import StudentQuestion, StudentClass, Subject
from alternia.rag.embeddings import EmbeddingService
from alternia.rag.vector_store import LocalVectorStore
from alternia.rag.indexer import KnowledgeIndexer
from alternia.ingestion.pipeline import DocumentIngestionPipeline
from alternia.config.settings import PROJECT_ROOT


KNOWLEDGE_BASE = PROJECT_ROOT / "knowledge-base"


def main():

    print()
    print("=" * 70)
    print("              TEST DU RETRIEVAL RAG")
    print("=" * 70)
    print()

    # ---------------------------------------------------------
    # 1. Ingestion des documents
    # ---------------------------------------------------------

    print("[1/4] Ingestion des PDF...")
    print()

    ingestion = DocumentIngestionPipeline(
        max_chunk_characters=1200,
    )

    chunks = ingestion.process_directory(
        KNOWLEDGE_BASE
    )

    print()
    print(
        f"Chunks chargés : {len(chunks)}"
    )

    # ---------------------------------------------------------
    # 2. Création du moteur d'indexation
    # ---------------------------------------------------------

    print()
    print("[2/4] Chargement du modèle embedding...")

    embedding_service = EmbeddingService()

    vector_store = LocalVectorStore()

    indexer = KnowledgeIndexer(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )

    # ---------------------------------------------------------
    # 3. Indexation
    # ---------------------------------------------------------

    print()
    print("[3/4] Indexation des chunks...")

    indexer.index_chunks(chunks)

    print(
        f"Vecteurs disponibles : "
        f"{len(vector_store.records)}"
    )

    # ---------------------------------------------------------
    # 4. Question de test
    # ---------------------------------------------------------

    questions = [
        StudentQuestion(
            student_id="test-student",
            student_class=StudentClass.TWELVE,
            question="Comment résoudre une équation du second degré ?",
            subject=Subject.MATHEMATIQUES,
        ),

        StudentQuestion(
            student_id="test-student",
            student_class=StudentClass.TWELVE,
            question="Comment résoudre une équation différentielle ?",
            subject=Subject.MATHEMATIQUES,
        ),

        StudentQuestion(
            student_id="test-student",
            student_class=StudentClass.TWELVE,
            question="Comment étudier une fonction ?",
            subject=Subject.MATHEMATIQUES,
        ),

        StudentQuestion(
            student_id="test-student",
            student_class=StudentClass.TWELVE,
            question="Comment calculer une dérivée ?",
            subject=Subject.MATHEMATIQUES,
        ),
    ]

    print()
    print("[4/4] Recherche sémantique...")
    print()

    print()
    for question in questions:

        print()
        print("=" * 70)

        print(
            f"QUESTION : {question.question}"
        )

        print("=" * 70)

        results = indexer.search(
            question,
            top_k=5,
        )

        for index, (document, score) in enumerate(
            results,
            start=1,
        ):

            print()
            print(
                f"[RESULTAT {index}] "
                f"score={score:.4f}"
            )

            print(
                f"Titre    : {document.title}"
            )

            print(
                f"Chapitre : {document.chapter}"
            )

            print(
                f"Source   : {document.source}"
            )

            print()

            print(
                document.content[:500]
            )

        print()
        print()
        print(
            "TEST TERMINÉ"
        )
        print()


if __name__ == "__main__":
    main()