from alternia.embeddings.service import EmbeddingService


def test_embedding_generation():

    service = EmbeddingService()

    vector = service.encode(
        "Comment résoudre une équation ?"
    )

    assert isinstance(vector, list)

    assert len(vector) == 384

    assert all(
        isinstance(value, float)
        for value in vector
    )


def test_embedding_is_normalized():

    service = EmbeddingService()

    vector = service.encode(
        "Les équations du premier degré."
    )

    norm = sum(
        value * value
        for value in vector
    ) ** 0.5

    assert abs(norm - 1.0) < 1e-5


def test_batch_embedding():

    service = EmbeddingService()

    vectors = service.encode_many(
        [
            "Une équation est une égalité.",
            "Un triangle possède trois côtés.",
        ]
    )

    assert len(vectors) == 2

    assert len(vectors[0]) == 384
    assert len(vectors[1]) == 384