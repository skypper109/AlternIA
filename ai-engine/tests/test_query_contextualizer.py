from alternia.rag.contextualizer import QueryContextualizer
from alternia.hardware.manager import HardwareManager
from alternia.tts.engine import TTSEngine


def test_query_contextualizer_standalone():
    q = "Qu'est-ce que la sociologie végétale ?"
    result = QueryContextualizer.contextualize(q)
    assert result == q


def test_query_contextualizer_follow_up_importance():
    past = ["Qu'est-ce que la sociologie végétale ?"]
    curr = "C'est quoi son importance ?"
    result = QueryContextualizer.contextualize(curr, past_student_messages=past)
    assert "sociologie végétale" in result
    assert "importance" in result or "rôle" in result


def test_query_contextualizer_reexplain():
    past = ["en biologie c'est quoi La zonation ?"]
    curr = "réexplique moi en détail"
    result = QueryContextualizer.contextualize(curr, past_student_messages=past)
    assert "zonation" in result


def test_query_contextualizer_elliptical():
    past = ["C'est quoi La sociabilité ?"]
    curr = "en biologie"
    result = QueryContextualizer.contextualize(curr, past_student_messages=past)
    assert "sociabilité" in result
    assert "biologie" in result


def test_hardware_manager_mock():
    hw = HardwareManager()
    assert not hw.is_rpi or hw._gpio_available in {True, False}
    hw.set_led_status("ready")
    hw.set_led_status("listening")
    hw.set_led_status("speaking")
    hw.set_led_status("error")
    hw.cleanup()


def test_tts_engine_vivienne_voice():
    tts = TTSEngine(voice="vivienne")
    assert "vivienne" in tts.neural_voice.lower()
    assert "vivienne" in tts.voice.lower()
    assert tts.cache_dir.exists()
