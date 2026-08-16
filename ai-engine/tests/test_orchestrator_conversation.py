from types import SimpleNamespace

from alternia.conversation.manager import (
    ConversationManager,
)
from alternia.orchestration.orchestrator import (
    AlterniaOrchestrator,
)
from alternia.pedagogical.engine import (
    PedagogicalEngine,
)
from alternia.llm.fake_client import (
    FakeLLMClient,
)


def make_context():

    return SimpleNamespace(
        context_text=(
            "Une équation est une égalité "
            "contenant une inconnue."
        ),
        sources=[],
    )


def test_orchestrator_uses_conversation_context():

    conversation_manager = (
        ConversationManager()
    )

    conversation_manager.create_session(
        session_id="session-test",
        student_id=None,
        student_class="10eme",
        subject="mathematiques",
    )

    conversation_manager.add_student_message(
        session_id="session-test",
        content="Qu'est-ce qu'une équation ?",
    )

    conversation_manager.add_assistant_message(
        session_id="session-test",
        content=(
            "Une équation est une égalité "
            "contenant une inconnue."
        ),
    )

    class InspectingLLM(FakeLLMClient):

        def generate(
            self,
            prompt,
            *,
            system_prompt=None,
        ):

            assert (
                "CONTEXTE CONVERSATIONNEL ALTERNIA"
                in prompt
            )

            assert (
                "Qu'est-ce qu'une équation ?"
                in prompt
            )

            assert (
                "Une équation est une égalité"
                in prompt
            )

            return "Une réponse contextuelle."

    orchestrator = AlterniaOrchestrator(
        pedagogical_engine=PedagogicalEngine(),
        llm_client=InspectingLLM(),
        conversation_manager=conversation_manager,
    )

    response = orchestrator.ask(
        question="Et comment on la résout ?",
        context=make_context(),
        student_class="10eme",
        subject="mathematiques",
        session_id="session-test",
    )

    assert (
        response["answer"]
        == "Une réponse contextuelle."
    )


def test_orchestrator_ask_stream_records_and_uses_memory():
    conversation_manager = ConversationManager()

    class StreamInspectionLLM(FakeLLMClient):
        def generate_stream(self, prompt, *, system_prompt=None):
            yield "Explication "
            yield "streamée étape par étape."

    orchestrator = AlterniaOrchestrator(
        pedagogical_engine=PedagogicalEngine(),
        llm_client=StreamInspectionLLM(),
        conversation_manager=conversation_manager,
    )

    # Tour 1 en streaming
    stream = orchestrator.ask_stream(
        question="C'est quoi la photosynthèse ?",
        context=make_context(),
        student_class="10eme",
        subject="biologie",
        session_id="session-stream-memory",
    )
    result = "".join(list(stream))
    assert result == "Explication streamée étape par étape."

    # Vérification que la session et les messages ont été mémorisés
    session = conversation_manager.get_session("session-stream-memory")
    assert len(session.messages) == 2
    assert session.messages[0].role == "student"
    assert session.messages[0].content == "C'est quoi la photosynthèse ?"
    assert session.messages[1].role == "assistant"
    assert session.messages[1].content == "Explication streamée étape par étape."