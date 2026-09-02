import sys
from pathlib import Path
import numpy as np
import pytest

ROOT_DIR = Path(__file__).resolve().parents[2]
AI_ENGINE_SRC = ROOT_DIR / "ai-engine" / "src"
if str(AI_ENGINE_SRC) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_SRC))

from alternia.stt.engine import STTEngine


def test_stt_engine_initialization():
    stt = STTEngine(model_size="base", language="fr")
    assert stt.model_size == "base"
    assert stt.language == "fr"
    assert stt.models_dir.exists()


def test_stt_engine_save_wav_and_mock(tmp_path):
    stt = STTEngine()
    
    # 1 seconde de silence à 16kHz
    audio_data = np.zeros(16000, dtype=np.int16)
    wav_path = tmp_path / "test.wav"
    
    stt._save_numpy_to_wav(audio_data, wav_path)
    assert wav_path.exists()
    assert wav_path.stat().st_size > 0
