import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
AI_ENGINE_SRC = ROOT_DIR / "ai-engine" / "src"
if str(AI_ENGINE_SRC) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_SRC))

import pytest
from alternia.tts.engine import TTSEngine, NEURAL_VOICES


def test_tts_engine_initialization():
    tts = TTSEngine(voice="vivienne", use_neural=True)
    assert tts.voice == "Neural Vivienne"
    assert tts.neural_voice == NEURAL_VOICES["vivienne"]
    tts.stop()


def test_tts_engine_voice_switching():
    tts = TTSEngine(voice="vivienne")
    new_v = tts.set_voice("remy")
    assert "Remy" in new_v
    assert tts.neural_voice == NEURAL_VOICES["remy"]

    new_v = tts.set_voice("system")
    assert "Système" in new_v
    assert tts.use_neural is False
    tts.stop()


def test_tts_clean_for_speech():
    text = "Une équation ax² + bx + c = 0 avec x = [-b ± √(b² - 4ac)] / (2a)."
    cleaned = TTSEngine._clean_for_speech(text)
    assert "au carré" in cleaned
    assert "racine carrée de" in cleaned
    assert "plus ou moins" in cleaned
    assert "égale" in cleaned


def test_tts_play_system_speech(monkeypatch):
    tts = TTSEngine(voice="vivienne", use_neural=False)
    assert hasattr(tts, "_play_system_speech")

    called_cmd = []

    class DummyProcess:
        def wait(self):
            pass

    def dummy_popen(cmd, *args, **kwargs):
        called_cmd.append(cmd)
        return DummyProcess()

    monkeypatch.setattr("subprocess.Popen", dummy_popen)
    tts._play_system_speech("Bonjour le Mali !")
    assert len(called_cmd) == 1
    assert "Bonjour le Mali !" in called_cmd[0]
    tts.stop()

