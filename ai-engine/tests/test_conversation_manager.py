from alternia.conversation.models import (
    ConversationMessage,
    ConversationSession,
)
from alternia.conversation.manager import (
    ConversationManager,
)


def test_conversation_session():

    session = ConversationSession(
        session_id="test-session-001",
        student_id="student-001",
        student_class="10eme",
        subject="mathematiques",
    )

    assert session.session_id == "test-session-001"

    assert session.student_class == "10eme"

    assert session.subject == "mathematiques"

    assert len(session.messages) == 0

    session.add_message(
        role="student",
        content="Comment résoudre une équation ?",
    )

    session.add_message(
        role="assistant",
        content=(
            "Pour résoudre une équation, "
            "on cherche la valeur de l'inconnue "
            "qui rend l'égalité vraie."
        ),
    )

    assert len(session.messages) == 2

    assert (
        session.messages[0].role
        == "student"
    )

    assert (
        session.messages[1].role
        == "assistant"
    )

    assert (
        session.messages[0].content
        == "Comment résoudre une équation ?"
    )


def test_last_messages():

    session = ConversationSession(
        session_id="test-session-002",
        student_id=None,
        student_class="10eme",
        subject="mathematiques",
    )

    for index in range(5):

        session.add_message(
            role="student",
            content=f"Question {index}",
        )

    messages = session.last_messages(
        limit=2
    )

    assert len(messages) == 2

    assert messages[0].content == "Question 3"

    assert messages[1].content == "Question 4"


def test_last_messages_with_invalid_limit():

    session = ConversationSession(
        session_id="test-session-003",
        student_id=None,
        student_class="10eme",
    )

    session.add_message(
        role="student",
        content="Bonjour",
    )

    assert session.last_messages(0) == []

    assert session.last_messages(-1) == []


def test_conversation_manager():

    manager = ConversationManager()

    session = manager.create_session(
        session_id="session-001",
        student_id="student-001",
        student_class="10eme",
        subject="mathematiques",
    )

    assert session.session_id == "session-001"

    assert manager.has_session(
        "session-001"
    )

    manager.add_student_message(
        "session-001",
        "Comment résoudre une équation ?",
    )

    manager.add_assistant_message(
        "session-001",
        "On commence par isoler l'inconnue.",
    )

    history = manager.get_history(
        "session-001"
    )

    assert len(history) == 2

    assert history[0].role == "student"

    assert history[1].role == "assistant"


def test_update_conversation_context():

    manager = ConversationManager()

    manager.create_session(
        session_id="session-002",
        student_id=None,
        student_class="10eme",
        subject="mathematiques",
    )

    manager.update_topic(
        "session-002",
        "équations",
    )

    manager.update_lesson(
        "session-002",
        "équations du premier degré",
    )

    session = manager.get_session(
        "session-002"
    )

    assert (
        session.current_topic
        == "équations"
    )

    assert (
        session.current_lesson
        == "équations du premier degré"
    )


def test_unknown_session():

    manager = ConversationManager()

    assert not manager.has_session(
        "unknown"
    )

    try:
        manager.get_session("unknown")
        assert False
    except KeyError:
        pass