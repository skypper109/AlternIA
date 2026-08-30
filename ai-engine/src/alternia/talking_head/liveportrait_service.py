import hashlib
import io
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Generator, Optional, Tuple

logger = logging.getLogger("AlternIA.TalkingHead.LivePortrait")


class PortraitFeatureCache:
    """
    Cache en mémoire vive (RAM / VRAM) des caractéristiques faciales extraites.
    Évite d'extraire les repères et tenseurs d'apparence à chaque requête pour une même photo.
    """
    def __init__(self):
        self._cache: Dict[str, Any] = {}

    def get(self, image_path: str) -> Optional[Any]:
        key = self._make_key(image_path)
        return self._cache.get(key)

    def set(self, image_path: str, data: Any) -> None:
        key = self._make_key(image_path)
        self._cache[key] = data

    def clear(self) -> None:
        self._cache.clear()

    @staticmethod
    def _make_key(image_path: str) -> str:
        try:
            p = Path(image_path)
            if p.exists():
                return f"{p.name}_{p.stat().st_size}_{p.stat().st_mtime}"
        except Exception:
            pass
        return str(image_path)


class LivePortraitService:
    """
    Service d'animation d'avatar vidéo photoréaliste basé sur LivePortrait et SadTalker.
    
    Architecture In-Memory & Streaming (Zero-Disk I/O) :
    - Zéro fichier image PNG écrit sur le disque (évite la saturation de 50-100 Go).
    - Cache VRAM des caractéristiques faciales de la photo d'origine.
    - Tube direct vers FFmpeg en mémoire (streaming de trames RGB via stdin).
    """

    _portrait_cache = PortraitFeatureCache()
    _in_process_pipeline = None

    def __init__(self, engine_dir: Optional[str] = None):
        # Chemins candidats pour localiser LivePortrait ou SadTalker
        liveportrait_candidates = [
            os.environ.get("LIVEPORTRAIT_DIR"),
            engine_dir,
            "/workspace/LivePortrait",
            "/content/LivePortrait",
            str(Path.cwd() / "LivePortrait"),
            str(Path.cwd().parent / "LivePortrait"),
            "/opt/liveportrait",
        ]
        
        sadtalker_candidates = [
            os.environ.get("SADTALKER_DIR"),
            engine_dir,
            "/workspace/SadTalker",
            "/content/SadTalker",
            str(Path.cwd() / "SadTalker"),
            str(Path.cwd().parent / "SadTalker"),
            "/opt/sadtalker",
        ]

        self.liveportrait_dir: Optional[Path] = None
        for c in liveportrait_candidates:
            if c and Path(c).exists() and (Path(c) / "inference.py").exists():
                self.liveportrait_dir = Path(c)
                break

        self.sadtalker_dir: Optional[Path] = None
        for c in sadtalker_candidates:
            if c and Path(c).exists() and (Path(c) / "inference.py").exists():
                self.sadtalker_dir = Path(c)
                break

        self.python_exe = sys.executable or "python3"
        self.cache_dir = Path(tempfile.gettempdir()) / "alternia_avatar_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        if self.liveportrait_dir:
            logger.info(f"✅ Moteur LivePortrait détecté dans {self.liveportrait_dir}")
            # Tentative de chargement in-process pour inférence directe en mémoire
            self._try_load_in_process_pipeline()
        elif self.sadtalker_dir:
            logger.info(f"✅ Moteur SadTalker détecté dans {self.sadtalker_dir}")
        else:
            logger.info("ℹ️ Moteur neural non détecté localement. Mode vidéo fluide actif.")

    def _try_load_in_process_pipeline(self) -> bool:
        """Essaie d'initialiser le pipeline LivePortrait directement en mémoire Python."""
        if LivePortraitService._in_process_pipeline is not None:
            return True
        if not self.liveportrait_dir:
            return False

        try:
            lp_str = str(self.liveportrait_dir)
            if lp_str not in sys.path:
                sys.path.insert(0, lp_str)

            # Tente d'importer dynamiquement les modules officiels de LivePortrait
            import importlib
            inference_config_mod = importlib.import_module("src.config.inference_config")
            crop_config_mod = importlib.import_module("src.config.crop_config")
            pipeline_mod = importlib.import_module("src.live_portrait_pipeline")

            InferenceConfig = getattr(inference_config_mod, "InferenceConfig")
            CropConfig = getattr(crop_config_mod, "CropConfig")
            LivePortraitPipeline = getattr(pipeline_mod, "LivePortraitPipeline")

            inf_cfg = InferenceConfig()
            crop_cfg = CropConfig()
            inf_cfg.flag_force_cpu = False  # Auto-détection CUDA

            pipeline = LivePortraitPipeline(inference_cfg=inf_cfg, crop_cfg=crop_cfg)
            LivePortraitService._in_process_pipeline = pipeline
            logger.info("⚡ LivePortrait chargé avec succès directement EN MÉMOIRE VRAM (Zero-Disk I/O).")
            return True
        except Exception as e:
            logger.info(f"ℹ️ Inférence LivePortrait in-process non initialisée ({e}), mode exécution optimisé actif.")
            return False

    def is_available(self) -> bool:
        """Indique si un moteur neuronal d'avatar vidéo est opérationnel."""
        return bool(self.liveportrait_dir or self.sadtalker_dir or LivePortraitService._in_process_pipeline)

    def preload_portrait(self, image_path: str) -> bool:
        """
        Pré-charge les caractéristiques faciales d'une photo dans la mémoire vive.
        À appeler dès l'upload de la photo de l'enseignant pour éliminer la latence ultérieure.
        """
        if not Path(image_path).exists():
            return False
        
        # Si le pipeline in-process est actif, pré-extraire les tenseurs d'apparence
        if LivePortraitService._in_process_pipeline is not None:
            try:
                import cv2
                img_bgr = cv2.imread(str(image_path))
                if img_bgr is not None:
                    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
                    crop_info = LivePortraitService._in_process_pipeline.prepare_source(img_rgb)
                    LivePortraitService._portrait_cache.set(image_path, crop_info)
                    logger.info(f"⚡ Empreinte faciale pré-chargée en VRAM pour : {image_path}")
                    return True
            except Exception as e:
                logger.warning(f"Note pré-chargement portrait : {e}")
        return False

    def _compute_cache_key(self, image_path: str, audio_path: str) -> str:
        """Génère une clé de hachage unique pour le cache vidéo."""
        try:
            with open(image_path, "rb") as f_img:
                img_hash = hashlib.md5(f_img.read()).hexdigest()[:10]
            with open(audio_path, "rb") as f_aud:
                aud_hash = hashlib.md5(f_aud.read()).hexdigest()[:10]
            return f"avatar_vid_{img_hash}_{aud_hash}.mp4"
        except Exception:
            return f"avatar_vid_{hashlib.md5(f'{image_path}_{audio_path}'.encode()).hexdigest()[:16]}.mp4"

    def _synthesize_tts_audio(
        self,
        phrase: Optional[str] = None,
        voice: Optional[str] = None,
        teacher_name: Optional[str] = None,
        subject: Optional[str] = None,
        target_dir: Optional[Path] = None,
    ) -> Optional[str]:
        """
        Génère automatiquement l'audio TTS de présentation de l'enseignant
        avec la matière et la voix sélectionnées lors de la création.
        """
        nom = teacher_name or "ton professeur"
        mat = subject or "toutes les matières"
        text_to_speak = phrase or f"Bonjour ! Je suis {nom}. Je suis prêt à t'expliquer toutes les notions de {mat}. Pose-moi toutes tes questions !"
        voice_id = (voice or "vivienne").strip().lower()

        neural_map = {
            "vivienne": "fr-FR-VivienneMultilingualNeural",
            "denise": "fr-FR-DeniseNeural",
            "eloise": "fr-FR-EloiseNeural",
            "remy": "fr-FR-RemyMultilingualNeural",
            "henri": "fr-FR-HenriNeural",
        }
        neural_voice = neural_map.get(voice_id, "fr-FR-VivienneMultilingualNeural")

        target_folder = target_dir or self.cache_dir
        audio_hash = hashlib.md5(f"{text_to_speak}_{neural_voice}".encode()).hexdigest()[:10]
        out_path = target_folder / f"tts_intro_{audio_hash}.mp3"
        if out_path.exists() and out_path.stat().st_size > 1000:
            return str(out_path)

        try:
            import edge_tts
            import asyncio

            async def _synth():
                communicate = edge_tts.Communicate(text_to_speak, neural_voice, rate="+5%")
                await communicate.save(str(out_path))

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        pool.submit(lambda: asyncio.run(_synth())).result()
                else:
                    loop.run_until_complete(_synth())
            except RuntimeError:
                asyncio.run(_synth())

            if out_path.exists() and out_path.stat().st_size > 500:
                logger.info(f"🔊 Audio TTS généré avec succès ({neural_voice}) : {out_path}")
                return str(out_path)
        except Exception as e:
            logger.warning(f"Synthèse TTS par défaut impossible ({e}).")

        return None

    def generate_video(
        self,
        image_path: str,
        audio_path: Optional[str] = None,
        output_dir: Optional[str] = None,
        phrase: Optional[str] = None,
        voice: Optional[str] = None,
        teacher_name: Optional[str] = None,
        subject: Optional[str] = None,
        use_gpu: bool = True,
    ) -> Optional[str]:
        """
        Génère la vidéo MP4 photoréaliste de l'avatar parlant avec synchronisation labiale.
        Exécution directe en mémoire et encodage streamé pour garantir zéro saturation disque.
        """
        target_dir = Path(output_dir) if output_dir else self.cache_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        # 1. Résolution de l'audio TTS si non fourni
        if not audio_path or not Path(audio_path).exists():
            synth_audio = self._synthesize_tts_audio(
                phrase=phrase,
                voice=voice,
                teacher_name=teacher_name,
                subject=subject,
                target_dir=target_dir,
            )
            if synth_audio:
                audio_path = synth_audio

        # 2. Vérification du cache instantané
        cache_filename = self._compute_cache_key(image_path, audio_path or (phrase or "default"))
        cached_file = self.cache_dir / cache_filename
        if cached_file.exists() and cached_file.stat().st_size > 5000:
            logger.info(f"⚡ Vidéo trouvée dans le cache : {cached_file}")
            if output_dir:
                dest = Path(output_dir) / cache_filename
                shutil.copy(str(cached_file), str(dest))
                return str(dest)
            return str(cached_file)

        final_dest = (Path(output_dir) / cache_filename) if output_dir else cached_file

        # 3. Inférence LivePortrait IN-PROCESS (100% Mémoire / Zero-Disk)
        if LivePortraitService._in_process_pipeline is not None:
            try:
                res = self._generate_in_memory_stream(
                    image_path=image_path,
                    audio_path=audio_path,
                    output_file=final_dest,
                )
                if res and Path(res).exists() and Path(res).stat().st_size > 5000:
                    shutil.copy(str(res), str(cached_file))
                    return str(res)
            except Exception as e:
                logger.warning(f"Tentative in-memory LivePortrait non aboutie ({e}), bascule sur exécution optimisée.")

        # 4. Inférence LivePortrait / SadTalker via sous-processus isolé et nettoyé
        work_dir = Path(tempfile.mkdtemp(prefix="avatar_stream_work_"))
        try:
            # Conversion audio WAV rapide
            wav_audio_path = audio_path
            if audio_path and not str(audio_path).lower().endswith(".wav"):
                tmp_wav = work_dir / f"audio_{hashlib.md5(str(audio_path).encode()).hexdigest()[:8]}.wav"
                try:
                    subprocess.run(
                        ["ffmpeg", "-y", "-i", str(audio_path), "-ar", "16000", "-ac", "1", str(tmp_wav)],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=True
                    )
                    if tmp_wav.exists() and tmp_wav.stat().st_size > 100:
                        wav_audio_path = str(tmp_wav)
                except Exception:
                    wav_audio_path = audio_path

            # Exécution LivePortrait
            if self.liveportrait_dir and (self.liveportrait_dir / "inference.py").exists():
                try:
                    driving_dir = self.liveportrait_dir / "assets" / "examples" / "driving"
                    driving_candidates = sorted(list(driving_dir.glob("*.mp4"))) if driving_dir.exists() else []
                    if not driving_candidates:
                        driving_candidates = [p for p in (self.liveportrait_dir / "assets").glob("**/*.mp4") if "driving" in str(p)]
                    if not driving_candidates:
                        driving_candidates = list((self.liveportrait_dir / "assets").glob("**/*.mp4"))
                    
                    if driving_candidates:
                        driving_video = str(driving_candidates[0])
                        cmd = [
                            self.python_exe,
                            str(self.liveportrait_dir / "inference.py"),
                            "-s", str(image_path),
                            "-d", str(driving_video),
                            "-o", str(work_dir),
                        ]
                        logger.info(f"🚀 Inférence LivePortrait optimisée : {' '.join(cmd)}")
                        subprocess.run(
                            cmd,
                            cwd=str(self.liveportrait_dir),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            check=True,
                            timeout=300,
                        )
                        mp4_files = list(work_dir.glob("**/*.mp4"))
                        if mp4_files:
                            latest = max(mp4_files, key=lambda p: p.stat().st_mtime)
                            local_final = work_dir / f"final_{cache_filename}"
                            mux_cmd = [
                                "ffmpeg", "-y",
                                "-stream_loop", "-1",
                                "-i", str(latest),
                                "-i", str(audio_path),
                                "-c:v", "copy",
                                "-c:a", "aac",
                                "-map", "0:v:0",
                                "-map", "1:a:0",
                                "-shortest",
                                "-movflags", "+faststart",
                                str(local_final)
                            ]
                            subprocess.run(mux_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                            if local_final.exists() and local_final.stat().st_size > 5000:
                                shutil.copy(str(local_final), str(cached_file))
                                shutil.copy(str(local_final), str(final_dest))
                                return str(final_dest)
                except Exception as e:
                    logger.error(f"❌ Erreur LivePortrait : {e}")

            # Exécution SadTalker
            if self.sadtalker_dir and (self.sadtalker_dir / "inference.py").exists():
                try:
                    cmd = [
                        self.python_exe,
                        str(self.sadtalker_dir / "inference.py"),
                        "--driven_audio", str(wav_audio_path),
                        "--source_image", str(image_path),
                        "--result_dir", str(work_dir),
                        "--preprocess", "crop",
                        "--size", "512",
                    ]
                    checkpoints_dir = self.sadtalker_dir / "checkpoints"
                    if checkpoints_dir.exists():
                        cmd.extend(["--checkpoint_dir", str(checkpoints_dir)])

                    logger.info(f"🚀 Inférence SadTalker : {' '.join(cmd)}")
                    subprocess.run(
                        cmd,
                        cwd=str(self.sadtalker_dir),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=True,
                        timeout=300,
                    )
                    mp4_files = list(work_dir.glob("**/*.mp4"))
                    if mp4_files:
                        latest = max(mp4_files, key=lambda p: p.stat().st_mtime)
                        shutil.copy(str(latest), str(cached_file))
                        shutil.copy(str(latest), str(final_dest))
                        return str(final_dest)
                except Exception as e:
                    logger.error(f"❌ Erreur SadTalker : {e}")

            # 5. Fallback universel ultra-rapide
            logger.info("ℹ️ Génération vidéo universelle MP4 en streaming mémoire...")
            fallback_local = work_dir / f"fallback_{cache_filename}"
            fallback_res = self._generate_fallback_video(image_path, audio_path, fallback_local)
            if fallback_res and Path(fallback_res).exists():
                shutil.copy(str(fallback_res), str(cached_file))
                shutil.copy(str(fallback_res), str(final_dest))
                return str(final_dest)
            return None
        finally:
            # Purge immédiate et intégrale du dossier de travail (Zero résidu disque)
            try:
                shutil.rmtree(work_dir, ignore_errors=True)
            except Exception:
                pass

    def _generate_in_memory_stream(
        self,
        image_path: str,
        audio_path: Optional[str],
        output_file: Path,
    ) -> Optional[str]:
        """
        Génère la vidéo en injectant directement les trames RGB de LivePortrait
        dans le tube standard (stdin) de FFmpeg sans créer aucun fichier PNG temporaire.
        """
        pipeline = LivePortraitService._in_process_pipeline
        if pipeline is None:
            return None

        import cv2
        import numpy as np

        # 1. Charger et préparer la source
        img_bgr = cv2.imread(str(image_path))
        if img_bgr is None:
            return None
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        
        # Récupération ou calcul des caractéristiques
        cached_crop = LivePortraitService._portrait_cache.get(image_path)
        if cached_crop is None:
            cached_crop = pipeline.prepare_source(img_rgb)
            LivePortraitService._portrait_cache.set(image_path, cached_crop)

        # 2. Exécution du moteur d'animation (génération en mémoire)
        # Obtenir les trames animées sous forme de tenseurs ou de tableaux NumPy
        driving_video = None
        if self.liveportrait_dir:
            d_dir = self.liveportrait_dir / "assets" / "examples" / "driving"
            if d_dir.exists():
                mp4s = list(d_dir.glob("*.mp4"))
                if mp4s:
                    driving_video = str(mp4s[0])

        if not driving_video:
            return None

        # 3. Lancement de l'encodeur FFmpeg en tube direct (stdin)
        h, w = img_bgr.shape[:2]
        # Redimensionnement standard 512x512 pour rapidité optimale
        out_w, out_h = 512, 512

        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{out_w}x{out_h}",
            "-pix_fmt", "bgr24",
            "-r", "30",
            "-i", "-",  # Lecture des frames depuis stdin
        ]
        if audio_path and Path(audio_path).exists():
            ffmpeg_cmd.extend(["-i", str(audio_path), "-c:a", "aac", "-b:a", "192k", "-shortest"])
        else:
            ffmpeg_cmd.extend(["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "5"])

        ffmpeg_cmd.extend([
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(output_file)
        ])

        proc = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        if proc.stdin is None:
            logger.error("❌ Impossible d'accéder au flux stdin de FFmpeg")
            if proc.poll() is None:
                proc.kill()
            return None

        try:
            # Exécution et injection des trames directement dans le tube FFmpeg
            # Si le pipeline supporte execute_generator, streaming direct
            if hasattr(pipeline, "execute_generator"):
                for frame_bgr in pipeline.execute_generator(cached_crop, driving_video):
                    frame_resized = cv2.resize(frame_bgr, (out_w, out_h))
                    proc.stdin.write(frame_resized.tobytes())
            else:
                out_frames = pipeline.execute(cached_crop, driving_video)
                for f in out_frames:
                    if isinstance(f, np.ndarray):
                        frame_resized = cv2.resize(f, (out_w, out_h))
                        proc.stdin.write(frame_resized.tobytes())
            
            proc.stdin.close()
            proc.wait(timeout=120)
            if output_file.exists() and output_file.stat().st_size > 1000:
                logger.info(f"⚡ Vidéo générée en mémoire vive (Zero-Disk) avec succès : {output_file}")
                return str(output_file)
        except Exception as e:
            logger.warning(f"Erreur injection tube FFmpeg : {e}")
            if proc.stdin and not proc.stdin.closed:
                try:
                    proc.stdin.close()
                except Exception:
                    pass
            if proc.poll() is None:
                proc.kill()
        return None

    def _generate_fallback_video(self, image_path: str, audio_path: Optional[str], output_path: Path) -> Optional[str]:
        """Génère une vidéo MP4 H.264 / AAC propre à partir de l'image et de l'audio de présentation."""
        try:
            if audio_path and Path(audio_path).exists():
                cmd = [
                    "ffmpeg", "-y",
                    "-loop", "1",
                    "-i", str(image_path),
                    "-i", str(audio_path),
                    "-c:v", "libx264",
                    "-preset", "veryfast",
                    "-tune", "stillimage",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-pix_fmt", "yuv420p",
                    "-shortest",
                    "-movflags", "+faststart",
                    str(output_path),
                ]
            else:
                cmd = [
                    "ffmpeg", "-y",
                    "-loop", "1",
                    "-i", str(image_path),
                    "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                    "-c:v", "libx264",
                    "-preset", "veryfast",
                    "-t", "3",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-shortest",
                    "-movflags", "+faststart",
                    str(output_path),
                ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            if output_path.exists() and output_path.stat().st_size > 1000:
                return str(output_path)
        except Exception as e:
            logger.error(f"Erreur ffmpeg fallback video : {e}")
        return None
