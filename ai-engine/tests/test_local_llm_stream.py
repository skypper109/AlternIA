from pathlib import Path
import pytest
from alternia.llm.local_client import LocalLLMClient


MODEL_PATH = (
    Path(__file__).resolve().parents[1]
    / "models"
    / "llm"
    / "qwen2.5-3b-instruct-q4_k_m.gguf"
)


@pytest.mark.skipif(not MODEL_PATH.exists(), reason="Modèle GGUF local non téléchargé sur cette machine")
def test_local_llm_stream():

    client = LocalLLMClient(
        model_path=str(MODEL_PATH),
        max_tokens=40,
    )

    chunks = list(
        client.generate_stream(
            "Explique très brièvement ce qu'est une équation.",
            system_prompt=(
                "Tu es AlternIA, un assistant pédagogique. "
                "Réponds en français et sois très concis."
            ),
        )
    )

    answer = "".join(chunks)

    assert answer.strip()
    assert len(chunks) > 1