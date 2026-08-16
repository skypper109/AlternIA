import pytest

from alternia.llm.local_client import LocalLLMClient


def test_local_llm_requires_existing_model():

    with pytest.raises(FileNotFoundError):

        LocalLLMClient(
            model_path="/tmp/model-inexistant.gguf"
        )
