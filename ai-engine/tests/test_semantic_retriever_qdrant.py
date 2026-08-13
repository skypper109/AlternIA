from unittest.mock import Mock

import pytest

from alternia.retrieval.semantic_retriever import (
    SemanticRetriever,
)


def test_retrieve():

    embedding_service = Mock()

    embedding_service.encode.return_value = [
        0.1,
        0.2,
        0.3,
    ]

    vector_store = Mock()

    vector_store.search.return_value = [
        "result-1",
        "result-2",
    ]

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

    assert results == [
        "result-1",
        "result-2",
    ]

    embedding_service.encode.assert_called_once_with(
        "Comment résoudre une équation ?"
    )

    vector_store.search.assert_called_once_with(
        query_embedding=[
            0.1,
            0.2,
            0.3,
        ],
        top_k=3,
        student_class="10eme",
        subject="mathematiques",
    )


def test_class_is_required():

    embedding_service = Mock()
    vector_store = Mock()

    retriever = SemanticRetriever(
        embedding_service,
        vector_store,
    )

    with pytest.raises(ValueError):

        retriever.retrieve(
            query="Une question",
            student_class="",
        )


def test_query_cannot_be_empty():

    embedding_service = Mock()
    vector_store = Mock()

    retriever = SemanticRetriever(
        embedding_service,
        vector_store,
    )

    with pytest.raises(ValueError):

        retriever.retrieve(
            query="",
            student_class="10eme",
        )


def test_top_k_must_be_positive():

    embedding_service = Mock()
    vector_store = Mock()

    retriever = SemanticRetriever(
        embedding_service,
        vector_store,
    )

    with pytest.raises(ValueError):

        retriever.retrieve(
            query="Une question",
            student_class="10eme",
            top_k=0,
        )