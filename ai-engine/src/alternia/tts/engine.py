import asyncio
import hashlib
import os
import platform
import queue
import re
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Optional
import edge_tts

# Désactiver le warning de parallélisme HuggingFace lors des forks de processus
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Voix Neurales Haute Définition (Expressivité humaine type ChatGPT)
NEURAL_VOICES = {
    "vivienne": "fr-FR-VivienneMultilingualNeural",  # Féminine ultra-naturelle, chaleureuse et fluide (Défaut AlternIA)
    "denise": "fr-FR-DeniseNeural",                  # Féminine claire et posée
    "eloise": "fr-FR-EloiseNeural",                  # Féminine jeune, vivante et dynamique
    "remy": "fr-FR-RemyMultilingualNeural",          # Masculine naturelle et conversationnelle
    "henri": "fr-FR-HenriNeural",                    # Masculine posée et académique
}


class TTSEngine:
    """
    Moteur Text-To-Speech haute fidélité pour AlternIA avec pipeline de pré-synthèse.

    Caractéristiques :
    - Voix Neurale française ultra-naturelle et humaine (Vivienne par défaut).
    - Cache disque intelligent pour 0ms de latence sur les phrases déjà synthétisées.
    - Pipeline audio à 2 étages (synthèse en parallèle pendant la lecture) : 0ms de pause entre phrases.
    - File d'attente asynchrone non-bloquante pour lecture fluide au fil de la génération LLM.
    - Traduction phonétique des symboles et formules mathématiques pour une diction pédagogique parfaite.
    """

    def __init__(
        self,
        voice: Optional[str] = None,
        rate: Optional[int] = None,
        use_neural: bool = True,
        cache_dir: Optional[str] = None,
    ):
        self.system = platform.system()
        self.use_neural = use_neural
        self.neural_voice = self._resolve_neural_voice(voice or "vivienne")
        self.system_voice = self._detect_best_system_voice()
        self.rate = rate or 190

        # Répertoire de cache pour accélérer la voix Vivienne sur Raspberry Pi
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path(tempfile.gettempdir()) / "alternia_tts_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Pipeline à double étage : textes à synthétiser -> audios prêts à jouer
        self._text_queue: queue.Queue = queue.Queue()
        self._audio_queue: queue.Queue = queue.Queue()

        self._stop_event = threading.Event()
        self._synthesis_thread: Optional[threading.Thread] = None
        self._playback_thread: Optional[threading.Thread] = None
        self._current_process: Optional[subprocess.Popen] = None
        self._temp_files: list[str] = []

        self._start_pipeline()

    @property
    def voice(self) -> str:
        """Retourne le nom de la voix active."""
        if self.use_neural and self.neural_voice:
            for key, val in NEURAL_VOICES.items():
                if val == self.neural_voice or key == self.neural_voice:
                    return f"Neural {key.capitalize()}"
            return self.neural_voice
        return f"Système ({self.system_voice})"

    def _resolve_neural_voice(self, voice_name: str) -> str:
        """Résout un nom court de voix en identifiant officiel Azure Neural."""
        cleaned = voice_name.strip().lower()
        if cleaned in NEURAL_VOICES:
            return NEURAL_VOICES[cleaned]
        if "neural" in cleaned:
            return voice_name
        return NEURAL_VOICES["vivienne"]

    def set_voice(self, voice_name: str) -> str:
        """Change dynamiquement la voix utilisée."""
        cleaned = voice_name.strip().lower()
        if cleaned in {"system", "locale", "local", "systeme"}:
            self.use_neural = False
            return self.voice

        self.use_neural = True
        self.neural_voice = self._resolve_neural_voice(cleaned)
        return self.voice

    def _detect_best_system_voice(self) -> str:
        """Détecte la meilleure voix système locale française disponible."""
        if self.system == "Darwin":
            try:
                result = subprocess.run(
                    ["say", "-v", "?"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                french_voices = []
                for line in result.stdout.splitlines():
                    if "fr_FR" in line or "fr_CA" in line or "français" in line.lower() or "french" in line.lower():
                        match = re.match(r"^(.+?)\s{2,}fr_", line)
                        if match:
                            french_voices.append(match.group(1).strip())

                # Priorités absolues pour voix françaises de haute qualité sur Mac
                for preferred in ["Thomas", "Jacques", "Amélie", "Eddy (Français (France))", "Flo (Français (France))", "Audrey", "Aurélie"]:
                    if preferred in french_voices:
                        return preferred

                if french_voices:
                    return french_voices[0]
                return "Thomas"
            except Exception:
                return "Thomas"

        elif self.system == "Linux":
            return "fr+f3"

        return "default"

    def _start_pipeline(self):
        """Démarre les deux workers (synthèse en amont + lecture immédiate)."""
        self._synthesis_thread = threading.Thread(
            target=self._synthesis_worker,
            daemon=True,
            name="AlterniaTTSSynthesizer",
        )
        self._playback_thread = threading.Thread(
            target=self._playback_worker,
            daemon=True,
            name="AlterniaTTSPlayer",
        )
        self._synthesis_thread.start()
        self._playback_thread.start()

    def _synthesis_worker(self):
        """Pré-synthétise les phrases en parallèle pour qu'elles soient prêtes avant la fin de la lecture précédente."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            while not self._stop_event.is_set():
                try:
                    item = self._text_queue.get(timeout=0.15)
                except queue.Empty:
                    continue

                if item is None:
                    break

                text = item.strip()
                clean_text = self._clean_for_speech(text)
                if not clean_text:
                    self._text_queue.task_done()
                    continue

                if self.use_neural:
                    text_hash = hashlib.md5(f"{self.neural_voice}_{clean_text}_{self.rate}".encode("utf-8")).hexdigest()
                    cached_path = self.cache_dir / f"{text_hash}.mp3"
                    if cached_path.exists() and cached_path.stat().st_size > 0:
                        self._audio_queue.put(("cache_file", str(cached_path)))
                    else:
                        try:
                            temp_path = str(cached_path)
                            communicate = edge_tts.Communicate(clean_text, self.neural_voice, rate="+5%")
                            loop.run_until_complete(communicate.save(temp_path))

                            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                                self._audio_queue.put(("cache_file", temp_path))
                            else:
                                self._audio_queue.put(("system", clean_text))
                        except Exception:
                            self._audio_queue.put(("system", clean_text))
                else:
                    self._audio_queue.put(("system", clean_text))

                self._text_queue.task_done()
        finally:
            try:
                loop.close()
            except Exception:
                pass


    def _playback_worker(self):
        """Joue immédiatement les fichiers audio dès qu'ils arrivent, sans latence entre phrases."""
        while not self._stop_event.is_set():
            try:
                item = self._audio_queue.get(timeout=0.15)
            except queue.Empty:
                continue

            if item is None:
                break

            mode, payload = item

            if mode in {"file", "cache_file"}:
                audio_path = payload
                try:
                    if self.system == "Darwin":
                        self._current_process = subprocess.Popen(["afplay", audio_path])
                        self._current_process.wait()
                    elif self.system == "Linux":
                        if shutil.which("mpv"):
                            self._current_process = subprocess.Popen(["mpv", "--no-video", "--really-quiet", audio_path])
                        elif shutil.which("ffplay"):
                            self._current_process = subprocess.Popen(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", audio_path])
                        elif shutil.which("paplay"):
                            self._current_process = subprocess.Popen(["paplay", audio_path])
                        elif shutil.which("aplay"):
                            self._current_process = subprocess.Popen(["aplay", "-q", audio_path])
                        if self._current_process:
                            self._current_process.wait()
                finally:
                    self._current_process = None
                    if mode == "file" and os.path.exists(audio_path):
                        try:
                            os.remove(audio_path)
                        except Exception:
                            pass
            elif mode == "system":
                self._play_system_speech(payload)

            self._audio_queue.task_done()

    def _play_system_speech(self, clean_text: str) -> None:
        """Lecture de repli via le synthétiseur système local (say ou espeak)."""
        system_clean_text = re.sub(r"<[^>]+>", " ", clean_text)
        system_clean_text = re.sub(r"\s+", " ", system_clean_text).strip()
        if not system_clean_text:
            return

        if self.system == "Darwin":
            cmd = ["say", "-r", str(self.rate)]
            if self.system_voice and self.system_voice != "default":
                cmd.extend(["-v", self.system_voice])
            cmd.append(system_clean_text)
            try:
                self._current_process = subprocess.Popen(cmd)
                self._current_process.wait()
            except Exception:
                pass
            finally:
                self._current_process = None

        elif self.system == "Linux":
            executable = "espeak-ng" if shutil.which("espeak-ng") else "espeak"
            if shutil.which(executable):
                cmd = [executable, "-v", self.system_voice, "-s", str(self.rate), system_clean_text]
                try:
                    self._current_process = subprocess.Popen(cmd)
                    self._current_process.wait()
                except Exception:
                    pass
                finally:
                    self._current_process = None


    @staticmethod
    def _clean_for_speech(text: str) -> str:
        """
        Nettoie et enrichit le texte avec une ponctuation humaine fluide et dynamique
        sans temps de pause excessifs (style conversationnel ChatGPT / Denise).
        """
        t = text.strip()

        # Supprimer le code markdown brut et balises
        t = re.sub(r"<think>[\s\S]*?</think>", "", t, flags=re.IGNORECASE)
        t = re.sub(r"```[\s\S]*?```", " , comme montré dans cette démonstration, ", t)
        t = re.sub(r"`([^`]+)`", r"\1", t)
        t = re.sub(r"\*\*\*([^*]+)\*\*\*", r"\1", t)
        t = re.sub(r"\*\*([^*]+)\*\*", r"\1", t)
        t = re.sub(r"\*([^*]+)\*", r"\1", t)
        t = t.replace("***", "").replace("**", "").replace("*", "")
        t = re.sub(r"^#+\s*", "", t, flags=re.MULTILINE)

        # Remplacement des fractions LaTeX simples : \frac{a}{b} -> a sur b
        t = re.sub(r"\\frac\{([^}]+)\}\{([^}]+)\}", r"\1 sur \2", t)
        t = re.sub(r"\\sqrt\{([^}]+)\}", r"racine carrée de \1", t)
        t = re.sub(r"\\left|\\right", "", t)
        t = re.sub(r"\\[a-zA-Z]+", " ", t)  # Nettoyer les commandes LaTeX restantes

        # Remplacement phonétique des symboles mathématiques et scientifiques
        t = t.replace("²", " au carré ")
        t = t.replace("^2", " au carré ")
        t = t.replace("³", " au cube ")
        t = t.replace("^3", " au cube ")
        t = t.replace("±", " plus ou moins ")
        t = t.replace("≠", " différent de ")
        t = t.replace("≤", " inférieur ou égal à ")
        t = t.replace("≥", " supérieur ou égal à ")
        t = t.replace("→", " donne ")
        t = t.replace("⇒", " implique ")
        t = t.replace("⇔", " équivaut à ")
        t = t.replace("×", " fois ")
        t = t.replace("√", "racine carrée de ")
        t = t.replace("Δ", "delta ")
        t = t.replace("π", "pi ")
        t = t.replace("∈", " appartient à ")
        t = t.replace("∉", " n'appartient pas à ")
        t = t.replace("∞", " l'infini ")
        t = t.replace("≈", " environ ")

        # Unités scientifiques courantes en français
        t = re.sub(r"(\d+)\s*m/s²", r"\1 mètres par seconde au carré", t)
        t = re.sub(r"(\d+)\s*m/s\b", r"\1 mètres par seconde", t)
        t = re.sub(r"(\d+)\s*km/h\b", r"\1 kilomètres par heure", t)
        t = re.sub(r"(\d+)\s*rad/s\b", r"\1 radians par seconde", t)
        t = re.sub(r"(\d+)\s*Hz\b", r"\1 Hertz", t)
        t = re.sub(r"(\d+)\s*mol/L\b", r"\1 moles par litre", t)
        t = re.sub(r"(\d+)\s*mol\b", r"\1 moles", t)

        # Nettoyage des signes d'égalité avec espacement naturel
        t = re.sub(r"(\w+)\s*=\s*", r"\1 égale ", t)

        # Ponctuation fluide : Puces et énumérations
        t = re.sub(r"^[-*•]\s+", ", ", t, flags=re.MULTILINE)
        t = re.sub(r"^(\d+)\.\s+", r"Point \1, ", t, flags=re.MULTILINE)

        # Enchaînement rapide et naturel des phrases et paragraphes (sans pauses longues)
        t = re.sub(r"\n\s*\n+", ". ", t)
        t = re.sub(r"\n+", ", ", t)
        t = re.sub(r"\s*:\s*", ", ", t)
        t = re.sub(r"\s*;\s*", ", ", t)
        t = re.sub(r"\s*,\s*", ", ", t)
        t = re.sub(r"\s*\.\s*", ". ", t)
        t = re.sub(r"\s*\?\s*", "? ", t)
        t = re.sub(r"\s*!\s*", "! ", t)

        # Normalisation des niveaux et filières scolaires maliennes pour une diction parfaite
        t = re.sub(r"\b10[eè]me\b", "dixième année", t, flags=re.IGNORECASE)
        t = re.sub(r"\b11[eè]me\b", "onzième année", t, flags=re.IGNORECASE)
        t = re.sub(r"\b12[eè]me\b", "douzième année", t, flags=re.IGNORECASE)
        t = re.sub(r"\bterminal\b", "terminale", t, flags=re.IGNORECASE)
        t = re.sub(r"\bterminale\b", "classe de terminale", t, flags=re.IGNORECASE)
        t = re.sub(r"\s*&\s*", " et ", t)
        # Supprimer les parenthèses de sigles qui créent des prononciations étranges (ex: (TSExp), (11S), (TSE))
        t = re.sub(r"\s*\([A-Za-z0-9\s-]+\)", "", t)

        # Nettoyer les espaces multiples
        t = re.sub(r"\s+", " ", t)

        return t.strip()

    async def synthesize_to_bytes(self, text: str) -> bytes:
        """Génère directement les octets audio MP3 pour l'API web/dispositif."""
        clean_text = self._clean_for_speech(text)
        if not clean_text:
            return b""
        import edge_tts
        communicate = edge_tts.Communicate(clean_text, self.neural_voice, rate="+5%")
        audio_chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio" and "data" in chunk:
                audio_chunks.append(chunk["data"])
        return b"".join(audio_chunks)

    def speak(self, text: str, async_mode: bool = False) -> None:
        """Lit un texte complet."""
        if not text or not text.strip():
            return
        self._text_queue.put(text.strip())

    def speak_sentence_async(self, sentence: str) -> None:
        """Enfile une phrase pour lecture fluide en streaming au fil de la génération."""
        if sentence and sentence.strip():
            self._text_queue.put(sentence.strip())

    def speak_sync(self, text: str) -> None:
        """Joue un texte de façon bloquante et attend la fin de la lecture (idéal pour les adieux/sorties)."""
        if not text or not text.strip():
            return
        clean_text = self._clean_for_speech(text)
        if not clean_text:
            return

        if self.use_neural:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                text_hash = hashlib.md5(f"{self.neural_voice}_{clean_text}_{self.rate}".encode("utf-8")).hexdigest()
                cached_path = self.cache_dir / f"{text_hash}.mp3"
                if not (cached_path.exists() and cached_path.stat().st_size > 0):
                    communicate = edge_tts.Communicate(clean_text, self.neural_voice, rate="+5%")
                    loop.run_until_complete(communicate.save(str(cached_path)))
                loop.close()

                if cached_path.exists() and cached_path.stat().st_size > 0:
                    if self.system == "Darwin":
                        subprocess.run(["afplay", str(cached_path)], check=False)
                        return
                    elif self.system == "Linux":
                        if shutil.which("mpv"):
                            subprocess.run(["mpv", "--no-video", "--really-quiet", str(cached_path)], check=False)
                            return
                        elif shutil.which("ffplay"):
                            subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(cached_path)], check=False)
                            return
                        elif shutil.which("paplay"):
                            subprocess.run(["paplay", str(cached_path)], check=False)
                            return
                        elif shutil.which("aplay"):
                            subprocess.run(["aplay", "-q", str(cached_path)], check=False)
                            return
            except Exception:
                pass

        # Repli système
        self._play_system_speech(clean_text)

    def stop(self) -> None:
        """Arrête immédiatement la parole en cours et vide toutes les files d'attente."""
        if self._current_process and self._current_process.poll() is None:
            try:
                self._current_process.terminate()
            except Exception:
                pass

        # Vider la file de texte
        while not self._text_queue.empty():
            try:
                self._text_queue.get_nowait()
                self._text_queue.task_done()
            except Exception:
                break

        # Vider la file d'audio et supprimer les fichiers temporaires non joués
        while not self._audio_queue.empty():
            try:
                item = self._audio_queue.get_nowait()
                if item and item[0] == "file" and os.path.exists(item[1]):
                    try:
                        os.remove(item[1])
                    except Exception:
                        pass
                self._audio_queue.task_done()
            except Exception:
                break
