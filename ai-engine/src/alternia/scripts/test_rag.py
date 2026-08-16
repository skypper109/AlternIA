from alternia.rag.embeddings import EmbeddingService
from alternia.rag.vector_store import LocalVectorStore
from alternia.rag.semantic_retriever import SemanticRetriever
from alternia.rag.service import RAGService


def main():

    print()
    print("=" * 70)
    print("              TEST RAG REEL — ALTERNIA")
    print("=" * 70)
    print()

    question = "Comment résoudre une équation du second degré ?"
    student_class = "12eme"
    subject = "mathematiques"

    print(f"Question : {question}")
    print(f"Classe   : {student_class}")
    print(f"Matière  : {subject}")
    print()

    # ---------------------------------------------------------
    # 1. Embeddings
    # ---------------------------------------------------------

    print("[1/4] Chargement du modèle embedding...")

    embedding_service = EmbeddingService()

    # ---------------------------------------------------------
    # 2. Index
    # ---------------------------------------------------------

    print("[2/4] Chargement de l'index RAG...")

    vector_store = LocalVectorStore()

    loaded = vector_store.load()

    if not loaded:
        print()
        print("ERREUR : aucun index RAG disponible.")
        print()
        return

    print(
        f"       Chunks chargés : {vector_store.count}"
    )

    # ---------------------------------------------------------
    # 3. Retriever
    # ---------------------------------------------------------

    print("[3/4] Initialisation du SemanticRetriever...")

    retriever = SemanticRetriever(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )

    rag = RAGService(
        retriever=retriever,
        top_k=5,
    )

    # ---------------------------------------------------------
    # 4. Recherche
    # ---------------------------------------------------------

    print("[4/4] Recherche sémantique...")
    print()

    context = rag.retrieve(
        question=question,
        student_class=student_class,
        subject=subject,
    )

    # ---------------------------------------------------------
    # Résultats
    # ---------------------------------------------------------

    print("=" * 70)
    print("                    RESULTATS RAG")
    print("=" * 70)
    print()

    print(
        f"Sources récupérées : {len(context.sources)}"
    )
    print()

    if not context.sources:
        print("Aucune source pertinente trouvée.")
        print()
        return

    for index, source in enumerate(
        context.sources,
        start=1,
    ):

        print("-" * 70)

        print(
            f"[{index}] Score : {source.score:.4f}"
        )

        print(
            f"    Chunk    : {source.chunk_id}"
        )

        print(
            f"    Classe   : {source.student_class}"
        )

        print(
            f"    Matière  : {source.subject}"
        )

        print(
            f"    Chapitre : "
            f"{source.chapter or 'Non défini'}"
        )

        print(
            f"    Leçon    : "
            f"{source.lesson or 'Non définie'}"
        )

        print(
            f"    Source   : "
            f"{source.source_document or 'Inconnue'}"
        )

        print()

        preview = source.content.strip()

        if len(preview) > 500:
            preview = preview[:500] + "..."

        print("    Contenu :")
        print()

        print(
            "    "
            + preview.replace(
                "\n",
                "\n    ",
            )
        )

        print()

    # ---------------------------------------------------------
    # Contexte final
    # ---------------------------------------------------------

    print("=" * 70)
    print("              CONTEXTE PEDAGOGIQUE")
    print("=" * 70)
    print()

    print(context.context_text)

    print()
    print("=" * 70)
    print("                    RAG OK")
    print("=" * 70)
    print()

    print(
        f"Index chargé     : {vector_store.count} chunks"
    )

    print(
        f"Sources retenues : {len(context.sources)}"
    )

    print()


if __name__ == "__main__":
    main()