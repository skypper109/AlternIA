from alternia.rag.embeddings import EmbeddingService


def test_embedding_generation():

    service = EmbeddingService()

    vector = service.encode(
        "Comment résoudre une équation ?"
    )

    assert vector is not None
    assert len(vector) > 0

    print()
    print("Dimension du vecteur :", len(vector))
    print("Premiers éléments :", vector[:5])