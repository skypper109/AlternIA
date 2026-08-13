from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


MessageRole = Literal["student", "assistant", "system"]


@dataclass
class ConversationMessage:
    """
    Représente un message échangé pendant une session AlternIA.
    """

    role: MessageRole
    content: str
    timestamp: datetime = field(
        default_factory=datetime.utcnow
    )
    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class ConversationSession:
    """
    État courant d'une conversation pédagogique.
    """

    session_id: str
    student_id: str | None
    student_class: str
    subject: str | None = None

    messages: list[ConversationMessage] = field(
        default_factory=list
    )

    current_topic: str | None = None
    current_lesson: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=datetime.utcnow
    )

    updated_at: datetime = field(
        default_factory=datetime.utcnow
    )

    def add_message(
        self,
        role: MessageRole,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationMessage:
        """
        Ajoute un message à la conversation.
        """

        message = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata or {},
        )

        self.messages.append(message)
        self.updated_at = datetime.utcnow()

        return message

    def last_messages(
        self,
        limit: int = 10,
    ) -> list[ConversationMessage]:
        """
        Retourne les derniers messages de la conversation.
        """

        if limit <= 0:
            return []

        return self.messages[-limit:]