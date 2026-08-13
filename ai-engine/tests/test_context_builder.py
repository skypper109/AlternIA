from types import SimpleNamespace

from alternia.context.context_builder import (
    ContextBuilder,
)


def make_result(
    chunk_id,
    student_class,
    subject,
    content,
    score,
    chapter="algebre",
    lesson="equations",
):

    return SimpleNamespace(

        score=score,

        payload={

            "chunk_id": chunk_id,

            "student_class":
                student_class,

            "subject":
                subject,

            "chapter":
                chapter,

            "lesson":
                lesson,

            "content":
                content,

            "source_document":
                "mathematiques.pdf",
        },
    )


def test_context_builder():

    results = [

        make_result(
            "chunk-1",
            "10eme",
            "mathematiques",
            "Une équation est une égalité contenant une inconnue.",
            0.95,
        ),

        make_result(
            "chunk-2",
            "10eme",
            "mathematiques",
            "Pour résoudre une équation, on isole l'inconnue.",
            0.90,
        ),
    ]

    builder = ContextBuilder(
        max_sources=5
    )

    context = builder.build(
        query="Comment résoudre une équation ?",
        results=results,
        student_class="10eme",
        subject="mathematiques",
    )

    assert context.query == (
        "Comment résoudre une équation ?"
    )

    assert context.student_class == "10eme"

    assert context.subject == "mathematiques"

    assert len(context.sources) == 2

    assert (
        context.sources[0].chunk_id
        == "chunk-1"
    )

    assert (
        "CONTEXTE PÉDAGOGIQUE ALTERNIA"
        in context.context_text
    )

    assert (
        "Une équation est une égalité"
        in context.context_text
    )


def test_context_builder_filters_class():

    results = [

        make_result(
            "10-math",
            "10eme",
            "mathematiques",
            "Cours de mathématiques de 10ème.",
            0.95,
        ),

        make_result(
            "11-math",
            "11eme",
            "mathematiques",
            "Cours de mathématiques de 11ème.",
            0.99,
        ),
    ]

    builder = ContextBuilder()

    context = builder.build(
        query="équation",
        results=results,
        student_class="10eme",
        subject="mathematiques",
    )

    assert len(context.sources) == 1

    assert (
        context.sources[0].chunk_id
        == "10-math"
    )


def test_context_builder_filters_subject():

    results = [

        make_result(
            "math",
            "10eme",
            "mathematiques",
            "Cours de mathématiques.",
            0.95,
        ),

        make_result(
            "physique",
            "10eme",
            "physique",
            "Cours de physique.",
            0.99,
        ),
    ]

    builder = ContextBuilder()

    context = builder.build(
        query="équation",
        results=results,
        student_class="10eme",
        subject="mathematiques",
    )

    assert len(context.sources) == 1

    assert (
        context.sources[0].chunk_id
        == "math"
    )


def test_context_builder_removes_duplicates():

    results = [

        make_result(
            "same",
            "10eme",
            "mathematiques",
            "Même contenu.",
            0.80,
        ),

        make_result(
            "same",
            "10eme",
            "mathematiques",
            "Même contenu.",
            0.95,
        ),
    ]

    builder = ContextBuilder()

    context = builder.build(
        query="équation",
        results=results,
        student_class="10eme",
        subject="mathematiques",
    )

    assert len(context.sources) == 1

    assert (
        context.sources[0].score
        == 0.95
    )


def test_context_builder_respects_top_k():

    results = [

        make_result(
            f"chunk-{i}",
            "10eme",
            "mathematiques",
            f"Contenu {i}",
            1.0 - (i * 0.01),
        )

        for i in range(10)
    ]

    builder = ContextBuilder(
        max_sources=3
    )

    context = builder.build(
        query="équation",
        results=results,
        student_class="10eme",
        subject="mathematiques",
    )

    assert len(context.sources) == 3

    assert (
        context.sources[0].score
        >= context.sources[1].score
    )

    assert (
        context.sources[1].score
        >= context.sources[2].score
    )