import hashlib
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger("AlternIA.TalkingHead.LivePortrait")


class LivePortraitService:
    """
    Service d'animation d'avatar vidéo photoréaliste basé sur LivePortrait et SadTalker.
    Génère une véritable vidéo MP4 fluide et expressive à partir d'une seule image source (photo du prof)
    et d'un fichier audio de synthèse TTS.
    """

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

        self.liveportrait_dir = None
        for c in liveportrait_candidates:
            if c and Path(c).exists() and (Path(c) / "inference.py").exists():
                self.liveportrait_dir = Path(c)
                break

        self.sadtalker_dir = None
        for c in sadtalker_candidates:
            if c and Path(c).exists() and (Path(c) / "inference.py").exists():
                self.sadtalker_dir = Path(c)
                break

        self.python_exe = sys.executable or "python3"
        self.cache_dir = Path(tempfile.gettempdir()) / "alternia_avatar_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        if self.liveportrait_dir:
            logger.info(f"✅ Moteur LivePortrait détecté dans {self.liveportrait_dir}")
        elif self.sadtalker_dir:
            logger.info(f"✅ Moteur SadTalker détecté dans {self.sadtalker_dir}")
        else:
            logger.info("ℹ️ Moteur neural (LivePortrait/SadTalker) non encore cloné. Mode vidéo fallback actif.")

    def is_available(self) -> bool:
        """Indique si un moteur neuronal d'avatar vidéo est opérationnel."""
        return bool(self.liveportrait_dir or self.sadtalker_dir)

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
        Si l'audio n'est pas fourni, synthétise automatiquement la voix TTS de présentation
        avec la matière et la voix sélectionnées lors de la création de l'enseignant.
        """
        target_dir = Path(output_dir) if output_dir else self.cache_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        # Génération ou résolution de l'audio TTS par défaut si absent
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

        cache_filename = self._compute_cache_key(image_path, audio_path or (phrase or "default"))
        cached_file = self.cache_dir / cache_filename
        if cached_file.exists() and cached_file.stat().st_size > 5000:
            logger.info(f"⚡ Vidéo trouvée dans le cache : {cached_file}")
            if output_dir:
                dest = Path(output_dir) / cache_filename
                shutil.copy(str(cached_file), str(dest))
                return str(dest)
            return str(cached_file)

        # Création d'un dossier de travail dédié sur DISQUE LOCAL RAPIDE (/tmp / SSD local)
        # Évite les goulots d'étranglement, les verrous et les ralentissements des volumes réseau (NFS / RunPod / Cloud Volumes)
        work_dir = Path(tempfile.mkdtemp(prefix="avatar_infer_work_"))

        try:
            # Assurer que l'audio est disponible en format WAV sur le disque local
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
                except Exception as e:
                    logger.warning(f"Conversion audio WAV ffmpeg impossible ({e}), utilisation de l'audio direct.")
                    wav_audio_path = audio_path

            # 1. Tentative avec LivePortrait
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
                        logger.info(f"🚀 Lancement inférence LivePortrait (disque local) : {' '.join(cmd)}")
                        res = subprocess.run(
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
                            # Mixer l'audio TTS généré avec la vidéo LivePortrait sur disque local
                            local_final = work_dir / f"final_{cache_filename}"
                            try:
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
                                    if output_dir:
                                        shutil.copy(str(local_final), str(target_dir / cache_filename))
                                        return str(target_dir / cache_filename)
                                    return str(cached_file)
                            except Exception:
                                pass
                            shutil.copy(str(latest), str(cached_file))
                            if output_dir:
                                shutil.copy(str(latest), str(target_dir / cache_filename))
                                return str(target_dir / cache_filename)
                            return str(cached_file)
                except subprocess.CalledProcessError as e:
                    logger.error(f"❌ Erreur exécution LivePortrait (code {e.returncode}) :\n{e.stderr or e.stdout or e}")
                except Exception as e:
                    logger.error(f"❌ Erreur LivePortrait : {e}")

            # 2. Tentative avec SadTalker
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

                    logger.info(f"🚀 Lancement inférence SadTalker (disque local) : {' '.join(cmd)}")
                    res = subprocess.run(
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
                        if output_dir:
                            shutil.copy(str(latest), str(target_dir / cache_filename))
                            return str(target_dir / cache_filename)
                        return str(cached_file)
                except subprocess.CalledProcessError as e:
                    logger.error(f"❌ Erreur exécution SadTalker (code {e.returncode}) :\n{e.stderr or e.stdout or e}")
                except Exception as e:
                    logger.error(f"❌ Erreur SadTalker : {e}")

            # 3. Fallback universel : Génère une vidéo MP4 fluide sur disque local
            logger.info("ℹ️ Génération vidéo universelle MP4 sur disque local...")
            fallback_local = work_dir / f"fallback_{cache_filename}"
            fallback_res = self._generate_fallback_video(image_path, audio_path, fallback_local)
            if fallback_res and Path(fallback_res).exists():
                shutil.copy(str(fallback_res), str(cached_file))
                if output_dir:
                    shutil.copy(str(fallback_res), str(target_dir / cache_filename))
                    return str(target_dir / cache_filename)
                return str(cached_file)
            return None
        finally:
            # Nettoyage immédiat des milliers de frames temporaires pour ne pas saturer le disque
            try:
                shutil.rmtree(work_dir, ignore_errors=True)
            except Exception:
                pass

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
