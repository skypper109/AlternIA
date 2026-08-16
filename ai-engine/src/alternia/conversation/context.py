from alternia.conversation.models import (
    ConversationMessage,
    ConversationSession,
)


class ConversationContextBuilder:
    """
    Construit le contexte conversationnel transmis
    au moteur pédagogique / LLM.

    Cette classe ne gère pas les sessions.
    Elle transforme simplement une session en texte exploitable.
    """

    def __init__(
        self,
        max_messages: int = 4,  # 2 échanges complets = mémoire active sans ralentir l'inférence
    ):
        self.max_messages = max_messages

    def build(
        self,
        session: ConversationSession,
    ) -> str:
        messages = session.last_messages(
            self.max_messages
        )

        if not messages:
            return ""

        lines = [
            "CONTEXTE CONVERSATIONNEL ALTERNIA",
            "=================================",
        ]
        if session.current_topic:
            lines.append(f"Notion actuelle : {session.current_topic}")

        if session.current_lesson:
            lines.append(f"Leçon actuelle : {session.current_lesson}")

        for message in messages:
            lines.append(
                self._format_message(message)
            )

        return "\n".join(lines)

    @staticmethod
    def _format_message(
        message: ConversationMessage,
    ) -> str:

        role_labels = {
            "student": "ÉLÈVE",
            "assistant": "ALTA",
            "system": "SYSTÈME",
        }

        role = role_labels.get(
            message.role,
            message.role.upper(),
        )

        return (
            f"{role} : "
            f"{message.content.strip()}"
        )