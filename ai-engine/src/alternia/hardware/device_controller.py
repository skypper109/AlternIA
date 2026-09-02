"""
Contrôleur du dispositif physique AlternIA Box (4 Boutons + Micro STT + RAG + Synthèse Vocale TTS).

Logique des 4 boutons :
- Bouton 1 : Bascule sur le programme de 10ème Année (Tronc Commun).
- Bouton 2 : Bascule sur le programme de 11ème Année (Générale).
- Bouton 3 : Bascule sur le programme de 12ème Année (Terminale).
- Bouton 4 : Bouton Micro / Communication vocale (enregistre la voix, transcrit via Faster-Whisper,
             interroge le RAG selon la classe sélectionnée, et répond vocalement).
             Pour continuer ou poser une autre question, l'élève clique à nouveau sur le Bouton 4.
"""

import logging
import re
import threading
import time
from typing import Callable, Optional

from alternia.hardware.manager import HardwareManager
from alternia.orchestration.orchestrator import AlterniaOrchestrator
from alternia.pedagogical.curriculum_keywords import detect_malian_curriculum_subject
from alternia.rag.contextualizer import QueryContextualizer
from alternia.stt.engine import STTEngine
from alternia.tts.engine import TTSEngine

logger = logging.getLogger("AlternIA.Device")


class DeviceController:
    """
    Contrôleur principal du boîtier vocal AlternIA.
    """

    CLASS_LABELS = {
        "10eme": "10ème Année (Tronc Commun)",
        "11eme": "11ème Année (Générale)",
        "12eme": "12ème Année (Terminale)",
    }

    SERIES_DEFAULTS = {
        "10eme": "generale",
        "11eme": "11s",
        "12eme": "tse",
    }

    def __init__(
        self,
        orchestrator: AlterniaOrchestrator,
        tts: TTSEngine,
        stt: Optional[STTEngine] = None,
        initial_class: str = "10eme",
        on_state_change: Optional[Callable[[str, str, str], None]] = None,
    ):
        self.orchestrator = orchestrator
        self.tts = tts
        self.stt = stt or STTEngine(model_size="base", language="fr")
        self.on_state_change = on_state_change

        self.current_class = initial_class
        self.current_series = self.SERIES_DEFAULTS.get(initial_class, "generale")
        self.session_id = f"device_session_{int(time.time())}"
        self.student_id = f"eleve_box_{self.current_class}"

        self.is_listening = False
        self.is_processing = False
        self.is_speaking = False
        self._record_stop_flag = threading.Event()

        # Initialisation du gestionnaire de boutons matériels
        self.hardware = HardwareManager(
            on_class_10=self.select_class_10,
            on_class_11=self.select_class_11,
            on_class_12=self.select_class_12,
            on_mic_press=self.start_mic_interaction,
            on_mic_release=self.stop_mic_interaction,
        )

        self._notify_state("ready")

    def _notify_state(self, state: str, detail: str = "") -> None:
        """Met à jour les voyants lumineux et notifie l'interface graphique/terminal."""
        self.hardware.set_led_status(state)
        if self.on_state_change:
            self.on_state_change(state, self.current_class, detail)

    # =========================================================================
    # GESTION DES BOUTONS DE CLASSE (BOUTONS 1, 2, 3)
    # =========================================================================

    def select_class_10(self) -> None:
        """Action Bouton 1 : Sélectionne la 10ème Année."""
        self.current_class = "10eme"
        self.current_series = "generale"
        self.student_id = f"eleve_box_10eme"
        logger.info("👉 [Bouton 1 cliqué] Programme configuré sur : 10ème Année (Tronc Commun)")
        self._notify_state("ready", "Programme 10ème activé")
        self.tts.speak_sentence_async("Mode 10ème activé. Tu peux poser ta question en appuyant sur le bouton micro.")

    def select_class_11(self) -> None:
        """Action Bouton 2 : Sélectionne la 11ème Année."""
        self.current_class = "11eme"
        self.current_series = "11s"
        self.student_id = f"eleve_box_11eme"
        logger.info("👉 [Bouton 2 cliqué] Programme configuré sur : 11ème Année (Générale)")
        self._notify_state("ready", "Programme 11ème activé")
        self.tts.speak_sentence_async("Mode 11ème activé. Tu peux poser ta question en appuyant sur le bouton micro.")

    def select_class_12(self) -> None:
        """Action Bouton 3 : Sélectionne la 12ème Année (Terminale)."""
        self.current_class = "12eme"
        self.current_series = "tse"
        self.student_id = f"eleve_box_12eme"
        logger.info("👉 [Bouton 3 cliqué] Programme configuré sur : 12ème Année (Terminale)")
        self._notify_state("ready", "Programme 12ème activé")
        self.tts.speak_sentence_async("Mode Terminale 12ème activé. Tu peux poser ta question en appuyant sur le bouton micro.")

    # =========================================================================
    # GESTION DU BOUTON MICRO / COMMUNICATION (BOUTON 4)
    # =========================================================================

    def start_mic_interaction(self) -> None:
        """Action Bouton 4 (Appui) : Démarre l'écoute du micro."""
        if self.is_listening or self.is_processing:
            return

        # Interrompre tout son en cours
        self.tts.stop()
        self.is_listening = True
        self._record_stop_flag.clear()
        self._notify_state("listening", "Microphone ouvert... Parle maintenant !")

        logger.info(f"🎙️ [Bouton 4] Écoute micro active ({self.CLASS_LABELS[self.current_class]})...")
        self.stt.start_recording()

    def stop_mic_interaction(self) -> None:
        """Action Bouton 4 (Relâchement / Clic de fin) : Traite et répond vocalement."""
        if not self.is_listening:
            return

        self.is_listening = False
        self._record_stop_flag.set()
        self.is_processing = True
        self._notify_state("thinking", "Analyse vocale et recherche pédagogique...")

        # Exécution du traitement dans un thread dédié pour ne pas bloquer les événements
        threading.Thread(
            target=self._process_voice_query,
            daemon=True,
            name="AlternIAVoiceProcessor",
        ).start()

    def _process_voice_query(self) -> None:
        """Pipeline complet : Arrêt Micro -> STT -> RAG (Classe active) -> LLM -> TTS."""
        try:
            # 1. Récupération de l'audio
            audio_data = self.stt.stop_recording()
            if audio_data is None or len(audio_data) < 1600:  # < 0.1s
                logger.warning("Aucun son détecté lors de l'appui sur le bouton 4.")
                self._notify_state("ready", "Aucun son capté. Réessaie en appuyant sur le bouton 4.")
                self.is_processing = False
                return

            # 2. Reconnaissance vocale STT (Faster-Whisper)
            question_text = self.stt.transcribe(audio_data, language="fr").strip()
            if not question_text:
                logger.info("Transcription vide.")
                self._notify_state("ready", "Je n'ai pas entendu de question. Réessaie !")
                self.tts.speak_sentence_async("Je n'ai pas bien entendu. Réappuie sur le bouton 4 et pose ta question.")
                self.is_processing = False
                return

            logger.info(f"🗣️ Élève ({self.current_class}) : '{question_text}'")
            self._notify_state("thinking", f"Question : « {question_text} »")

            # 3. Détection de matière et contextualisation RAG
            detected_subject = detect_malian_curriculum_subject(question_text)
            rag_query = question_text

            session = self.orchestrator.conversation_manager.get(self.session_id)
            if session and session.messages:
                student_past = [m.content for m in session.messages if m.role == "student"]
                rag_query = QueryContextualizer.contextualize(
                    current_question=question_text,
                    past_student_messages=student_past,
                    current_topic=getattr(session, "current_topic", None),
                )

            # 4. Recherche RAG avec restriction stricte sur la classe active (Bouton 1, 2 ou 3)
            rag_context = None
            if self.orchestrator.rag_service:
                rag_context = self.orchestrator.rag_service.retrieve(
                    question=rag_query,
                    student_class=self.current_class,
                    subject=detected_subject,
                    student_id=self.student_id,
                    series=self.current_series,
                )

            # 5. Génération LLM & Émission Vocale TTS en continu
            self._notify_state("speaking", f"ALTA répond ({self.current_class})...")
            stream = self.orchestrator.ask_stream(
                question=question_text,
                context=rag_context,
                student_class=self.current_class,
                subject=detected_subject,
                student_id=self.student_id,
                session_id=self.session_id,
                series=self.current_series,
            )

            full_response = ""
            sentence_buffer = ""
            tts_split = re.compile(r"(?<=[.!?…])\s+|\n+")

            for chunk in stream:
                full_response += chunk
                sentence_buffer += chunk

                # Émission au fil de l'eau phrase par phrase
                m = tts_split.search(sentence_buffer)
                if m and len(sentence_buffer[:m.end()].strip()) >= 15:
                    segment = sentence_buffer[:m.end()].strip()
                    sentence_buffer = sentence_buffer[m.end():]
                    self.tts.speak_sentence_async(segment)

            # Émettre le reliquat de fin s'il existe
            if sentence_buffer.strip():
                self.tts.speak_sentence_async(sentence_buffer.strip())

            logger.info(f"🤖 ALTA > {full_response}")
            self._notify_state("ready", f"Prêt ! (Pour continuer, clique sur le Bouton 4)")

        except Exception as exc:
            logger.error(f"Erreur traitement vocal : {exc}", exc_info=True)
            self._notify_state("error", f"Erreur : {exc}")
            self.tts.speak_sentence_async("Une erreur est survenue lors du traitement.")
        finally:
            self.is_processing = False

    def close(self) -> None:
        """Arrête le contrôleur et libère le matériel."""
        self.hardware.cleanup()
        self.tts.stop()
