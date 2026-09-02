from unittest.mock import MagicMock
import pytest

from alternia.hardware.device_controller import DeviceController
from alternia.orchestration.orchestrator import AlterniaOrchestrator
from alternia.stt.engine import STTEngine
from alternia.tts.engine import TTSEngine


def test_device_controller_buttons_class_switching():
    mock_orchestrator = MagicMock(spec=AlterniaOrchestrator)
    mock_tts = MagicMock(spec=TTSEngine)
    mock_stt = MagicMock(spec=STTEngine)

    state_log = []

    def on_state(state, cls, detail):
        state_log.append((state, cls, detail))

    controller = DeviceController(
        orchestrator=mock_orchestrator,
        tts=mock_tts,
        stt=mock_stt,
        initial_class="10eme",
        on_state_change=on_state,
    )

    # Initial state
    assert controller.current_class == "10eme"

    # Click Button 2 -> 11eme
    controller.select_class_11()
    assert controller.current_class == "11eme"
    assert controller.current_series == "11s"

    # Click Button 3 -> 12eme
    controller.select_class_12()
    assert controller.current_class == "12eme"
    assert controller.current_series == "tse"

    # Click Button 1 -> 10eme
    controller.select_class_10()
    assert controller.current_class == "10eme"
    assert controller.current_series == "generale"


def test_device_controller_mic_button_flow():
    mock_orchestrator = MagicMock(spec=AlterniaOrchestrator)
    mock_tts = MagicMock(spec=TTSEngine)
    mock_stt = MagicMock(spec=STTEngine)

    controller = DeviceController(
        orchestrator=mock_orchestrator,
        tts=mock_tts,
        stt=mock_stt,
        initial_class="11eme",
    )

    # Press Button 4 (Start listening)
    controller.start_mic_interaction()
    assert controller.is_listening is True
    mock_stt.start_recording.assert_called_once()

    # Release / Click Button 4 (Stop listening and process)
    controller.stop_mic_interaction()
    assert controller.is_listening is False
