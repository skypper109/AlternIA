"""
Moteur STT (Speech-to-Text) embarqué pour AlternIA Box.

Fonctionnalités :
- Enregistrement direct depuis le microphone (Push-to-Talk matériel ou logiciel)
- Transcription vocale locale et rapide via Faster-Whisper (modèle tiny / base en français)
- Échantillonnage 16 kHz mono (standard de traitement vocal)
- Mode hors-ligne complet (aucune connexion Internet requise)
"""

import io
import logging
import os
import tempfile
import threading
import time
import wave
from pathlib import Path
from typing import Any, Callable, Optional

import numpy as np

from alternia.config.settings import PROJECT_ROOT

logger = logging.getLogger("AlternIA.STT")


class STTEngine:
    """
    Moteur de reconnaissance vocale locale pour le boîtier AlternIA.
    """

    DEFAULT_SAMPLE_RATE = 16000  # 16 kHz optimal pour Whisper

    def __init__(
        self,
        model_size: str = "base",
        language: str = "fr",
        device: str = "cpu",
        compute_type: str = "int8",
        models_dir: Optional[Path] = None,
    ):
        self.model_size = model_size
        self.language = language
        self.device = device
        self.compute_type = compute_type
        self.models_dir = models_dir or (PROJECT_ROOT / "ai-engine" / "models" / "stt")
        self.models_dir.mkdir(parents=True, exist_ok=True)

        self._whisper_model = None
        self._is_recording = False
        self._audio_frames: list[np.ndarray] = []
        self._record_thread: Optional[threading.Thread] = None

    def _get_whisper_model(self):
        """Initialise de façon paresseuse le modèle Faster-Whisper."""
        if self._whisper_model is not None:
            return self._whisper_model

        try:
            from faster_whisper import WhisperModel

            logger.info(
                f"Chargement du modèle STT Faster-Whisper ({self.model_size}, {self.compute_type})..."
            )
            self._whisper_model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                download_root=str(self.models_dir),
                cpu_threads=4,
            )
            return self._whisper_model
        except Exception as exc:
            logger.error(f"Erreur chargement Faster-Whisper : {exc}")
            return None

    def start_recording(self) -> None:
        """Démarre l'enregistrement audio depuis le microphone en arrière-plan."""
        if self._is_recording:
            return

        self._audio_frames = []
        self._is_recording = True

        def _record_worker():
            try:
                import sounddevice as sd

                def audio_callback(indata, frames, time_info, status):
                    if self._is_recording:
                        self._audio_frames.append(indata.copy())

                with sd.InputStream(
                    samplerate=self.DEFAULT_SAMPLE_RATE,
                    channels=1,
                    dtype="int16",
                    callback=audio_callback,
                ):
                    while self._is_recording:
                        time.sleep(0.05)
            except Exception as exc:
                logger.error(f"Erreur d'enregistrement microphone : {exc}")
                self._is_recording = False

        self._record_thread = threading.Thread(
            target=_record_worker, daemon=True, name="AlternIAAudioRecorder"
        )
        self._record_thread.start()
        logger.info("🎙️ Enregistrement microphone démarré...")

    def stop_recording(self) -> Optional[np.ndarray]:
        """Arrête l'enregistrement microphone et retourne le tableau audio numpy."""
        if not self._is_recording:
            return None

        self._is_recording = False
        if self._record_thread and self._record_thread.is_alive():
            self._record_thread.join(timeout=1.0)

        if not self._audio_frames:
            logger.warning("Aucun échantillon audio enregistré.")
            return None

        # Concaténation de tous les segments
        audio_data = np.concatenate(self._audio_frames, axis=0)
        logger.info(
            f"🎙️ Enregistrement terminé ({len(audio_data) / self.DEFAULT_SAMPLE_RATE:.2f}s)."
        )
        return audio_data

    def record_push_to_talk(
        self,
        stop_check: Callable[[], bool],
        max_duration_seconds: float = 15.0,
        on_audio_chunk: Optional[Callable[[float], None]] = None,
    ) -> Optional[np.ndarray]:
        """
        Enregistre l'audio tant que la condition stop_check() retourne False.
        Fournit le niveau sonore (VU-meter) via on_audio_chunk si configuré.
        """
        try:
            import sounddevice as sd
        except ImportError:
            logger.error("sounddevice n'est pas installé.")
            return None

        frames = []
        start_time = time.time()

        def audio_callback(indata, frames_count, time_info, status):
            frames.append(indata.copy())
            if on_audio_chunk:
                # Calcul de l'amplitude moyenne RMS pour feedback visuel
                rms = float(np.sqrt(np.mean(indata.astype(np.float32) ** 2)))
                on_audio_chunk(rms)

        try:
            with sd.InputStream(
                samplerate=self.DEFAULT_SAMPLE_RATE,
                channels=1,
                dtype="int16",
                callback=audio_callback,
            ):
                while not stop_check():
                    if time.time() - start_time >= max_duration_seconds:
                        break
                    time.sleep(0.05)
        except Exception as exc:
            logger.error(f"Erreur d'enregistrement Push-to-Talk : {exc}")
            return None

        if not frames:
            return None

        return np.concatenate(frames, axis=0)

    def transcribe(
        self,
        audio_data_or_path: str | Path | np.ndarray | bytes,
        language: Optional[str] = None,
        suffix: str = ".wav",
    ) -> str:
        """
        Transcrit un enregistrement audio en texte français.
        Accepte un chemin de fichier WAV, un tableau NumPy ou des octets audio.
        """
        model = self._get_whisper_model()
        if model is None:
            # Fallback de secours via SpeechRecognition si disponible
            return self._transcribe_fallback(audio_data_or_path)

        lang = language or self.language
        temp_wav_path: Optional[Path] = None

        try:
            # Gestion des différents formats d'entrée
            if isinstance(audio_data_or_path, (str, Path)):
                input_source = str(audio_data_or_path)
            elif isinstance(audio_data_or_path, np.ndarray):
                temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                temp_wav_path = Path(temp_file.name)
                temp_file.close()
                self._save_numpy_to_wav(audio_data_or_path, temp_wav_path)
                input_source = str(temp_wav_path)
            elif isinstance(audio_data_or_path, bytes):
                temp_file = tempfile.NamedTemporaryFile(suffix=suffix or ".wav", delete=False)
                temp_wav_path = Path(temp_file.name)
                temp_file.write(audio_data_or_path)
                temp_file.close()
                input_source = str(temp_wav_path)
            else:
                return ""

            segments, info = model.transcribe(
                input_source,
                language=lang,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=400),
            )

            text_parts = [segment.text.strip() for segment in segments]
            full_text = " ".join(text_parts).strip()
            logger.info(f"📝 Transcription STT : '{full_text}' (prob={info.language_probability:.2f})")
            return full_text

        except Exception as exc:
            logger.error(f"Erreur transcription Whisper : {exc}")
            return ""
        finally:
            if temp_wav_path and temp_wav_path.exists():
                try:
                    temp_wav_path.unlink()
                except Exception:
                    pass

    def _save_numpy_to_wav(self, audio_data: np.ndarray, file_path: Path) -> None:
        """Sauvegarde un tableau numpy int16 en fichier WAV standard."""
        with wave.open(str(file_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit = 2 bytes
            wf.setframerate(self.DEFAULT_SAMPLE_RATE)
            wf.writeframes(audio_data.tobytes())

    def _transcribe_fallback(self, audio_data_or_path: Any) -> str:
        """Transcription de secours via SpeechRecognition."""
        try:
            import speech_recognition as sr  # pyrefly: ignore
            r = sr.Recognizer()
            if isinstance(audio_data_or_path, (str, Path)):
                with sr.AudioFile(str(audio_data_or_path)) as source:
                    audio = r.record(source)
                    return r.recognize_google(audio, language="fr-FR")
        except Exception:
            pass
        return ""
