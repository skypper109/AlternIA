from typing import Any

from alternia.conversation.models import (
    ConversationSession,
)


class ConversationManager:
    """
    Gestionnaire des sessions conversationnelles d'AlternIA.

    Responsable de la mémoire court terme d'une conversation.
    """

    def __init__(self):
        self._sessions: dict[
            str,
            ConversationSession,
        ] = {}

    def create_session(
        self,
        session_id: str,
        student_id: str | None,
        student_class: str,
        subject: str | None = None,
    ) -> ConversationSession:

        if session_id in self._sessions:
            raise ValueError(
                f"La session '{session_id}' existe déjà."
            )

        session = ConversationSession(
            session_id=session_id,
            student_id=student_id,
            student_class=student_class,
            subject=subject,
        )

        self._sessions[session_id] = session

        return session

    def get_session(
        self,
        session_id: str,
    ) -> ConversationSession:

        session = self._sessions.get(
            session_id
        )

        if session is None:
            raise KeyError(
                f"Session inconnue : {session_id}"
            )

        return session

    def has_session(
        self,
        session_id: str,
    ) -> bool:

        return session_id in self._sessions

    def delete_session(
        self,
        session_id: str,
    ) -> None:

        self._sessions.pop(
            session_id,
            None,
        )

    def add_student_message(
        self,
        session_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ):

        session = self.get_session(
            session_id
        )

        return session.add_message(
            role="student",
            content=content,
            metadata=metadata,
        )

    def add_assistant_message(
        self,
        session_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ):

        session = self.get_session(
            session_id
        )

        return session.add_message(
            role="assistant",
            content=content,
            metadata=metadata,
        )

    def get_history(
        self,
        session_id: str,
        limit: int = 10,
    ):

        session = self.get_session(
            session_id
        )

        return session.last_messages(
            limit
        )

    def update_topic(
        self,
        session_id: str,
        topic: str | None,
    ) -> ConversationSession:

        session = self.get_session(
            session_id
        )

        session.current_topic = topic

        return session

    def update_lesson(
        self,
        session_id: str,
        lesson: str | None,
    ) -> ConversationSession:

        session = self.get_session(
            session_id
        )

        session.current_lesson = lesson

        return session
    