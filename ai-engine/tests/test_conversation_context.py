from alternia.conversation.context import (
    ConversationContextBuilder,
)
from alternia.conversation.models import (
    ConversationSession,
)


def make_session():

    return ConversationSession(
        session_id="session-test",
        student_id=None,
        student_class="10eme",
        subject="mathematiques",
    )


def test_empty_conversation_context():

    session = make_session()

    builder = ConversationContextBuilder()

    context = builder.build(session)

    assert context == ""


def test_conversation_context():

    session = make_session()

    session.add_message(
        role="student",
        content="Qu'est-ce qu'une équation ?",
    )

    session.add_message(
        role="assistant",
        content=(
            "Une équation est une égalité "
            "contenant une inconnue."
        ),
    )

    builder = ConversationContextBuilder()

    context = builder.build(session)

    assert (
        "CONTEXTE CONVERSATIONNEL ALTERNIA"
        in context
    )

    assert (
        "ÉLÈVE : Qu'est-ce qu'une équation ?"
        in context
    )

    assert (
        "ALTA : Une équation est une égalité"
        in context
    )


def test_conversation_context_topic_and_lesson():

    session = make_session()

    session.current_topic = "équations"

    session.current_lesson = (
        "équations du premier degré"
    )

    session.add_message(
        role="student",
        content="Je n'ai pas compris.",
    )

    builder = ConversationContextBuilder()

    context = builder.build(session)

    assert "Notion actuelle : équations" in context

    assert (
        "Leçon actuelle : "
        "équations du premier degré"
        in context
    )


def test_conversation_context_respects_limit():

    session = make_session()

    for index in range(10):

        session.add_message(
            role="student",
            content=f"Question {index}",
        )

    builder = ConversationContextBuilder(
        max_messages=3
    )

    context = builder.build(session)

    assert "Question 7" in context
    assert "Question 8" in context
    assert "Question 9" in context

    assert "Question 6" not in context