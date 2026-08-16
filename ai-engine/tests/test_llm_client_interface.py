from alternia.llm.client import LLMClient
from alternia.llm.fake_client import FakeLLMClient


def test_llm_client_generate_with_messages():
    client: LLMClient = FakeLLMClient()

    messages = [
        {"role": "system", "content": "Tu es un tuteur."},
        {"role": "user", "content": "Qu'est-ce qu'une équation ?"},
    ]

    response = client.generate(
        messages=messages,
        system_prompt="Tu es un tuteur.",
    )

    assert "équation" in response.lower() or "égalité" in response.lower()


def test_llm_client_generate_stream_with_messages():
    client: LLMClient = FakeLLMClient(response="Réponse directe.")

    messages = [
        {"role": "user", "content": "Bonjour"},
    ]

    stream = client.generate_stream(
        messages=messages,
    )
    result = "".join(list(stream))

    assert result == "Réponse directe."
