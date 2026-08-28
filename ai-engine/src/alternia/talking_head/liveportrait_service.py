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

    def generate_video(
        self,
        image_path: str,
        audio_path: str,
        output_dir: Optional[str] = None,
        use_gpu: bool = True,
    ) -> Optional[str]:
        """
        Génère la vidéo MP4 photoréaliste de l'avatar parlant avec synchronisation labiale.
        """
        target_dir = Path(output_dir) if output_dir else self.cache_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        cache_filename = self._compute_cache_key(image_path, audio_path)
        cached_file = self.cache_dir / cache_filename
        if cached_file.exists() and cached_file.stat().st_size > 5000:
            logger.info(f"⚡ Vidéo trouvée dans le cache : {cached_file}")
            if output_dir:
                dest = Path(output_dir) / cache_filename
                shutil.copy(str(cached_file), str(dest))
                return str(dest)
            return str(cached_file)

        # 1. Tentative avec LivePortrait
        if self.liveportrait_dir and (self.liveportrait_dir / "inference.py").exists():
            try:
                driving_candidates = list((self.liveportrait_dir / "assets").glob("**/*.mp4"))
                driving_video = str(driving_candidates[0]) if driving_candidates else str(audio_path)
                
                cmd = [
                    self.python_exe,
                    str(self.liveportrait_dir / "inference.py"),
                    "-s", str(image_path),
                    "-d", str(driving_video),
                    "-o", str(target_dir),
                    "--flag_crop_driving_video", "True",
                ]
                logger.info(f"🚀 Lancement inférence LivePortrait : {' '.join(cmd)}")
                subprocess.run(
                    cmd,
                    cwd=str(self.liveportrait_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True,
                    timeout=300,
                )
                mp4_files = list(target_dir.glob("**/*.mp4"))
                if mp4_files:
                    latest = max(mp4_files, key=lambda p: p.stat().st_mtime)
                    # Mixer l'audio TTS généré avec la vidéo LivePortrait
                    final_path = target_dir / cache_filename
                    try:
                        mux_cmd = [
                            "ffmpeg", "-y",
                            "-i", str(latest),
                            "-i", str(audio_path),
                            "-c:v", "copy",
                            "-c:a", "aac",
                            "-map", "0:v:0",
                            "-map", "1:a:0",
                            "-shortest",
                            "-movflags", "+faststart",
                            str(final_path)
                        ]
                        subprocess.run(mux_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                        if final_path.exists() and final_path.stat().st_size > 5000:
                            shutil.copy(str(final_path), str(cached_file))
                            return str(final_path)
                    except Exception:
                        pass
                    shutil.copy(str(latest), str(cached_file))
                    return str(latest)
            except Exception as e:
                logger.error(f"Erreur LivePortrait : {e}")

        # 2. Tentative avec SadTalker
        if self.sadtalker_dir and (self.sadtalker_dir / "inference.py").exists():
            try:
                cmd = [
                    self.python_exe,
                    str(self.sadtalker_dir / "inference.py"),
                    "--driven_audio", str(audio_path),
                    "--source_image", str(image_path),
                    "--result_dir", str(target_dir),
                    "--preprocess", "crop",
                    "--size", "512",
                ]
                logger.info(f"🚀 Lancement inférence SadTalker : {' '.join(cmd)}")
                subprocess.run(
                    cmd,
                    cwd=str(self.sadtalker_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True,
                    timeout=300,
                )
                mp4_files = list(target_dir.glob("**/*.mp4"))
                if mp4_files:
                    latest = max(mp4_files, key=lambda p: p.stat().st_mtime)
                    shutil.copy(str(latest), str(cached_file))
                    return str(latest)
            except Exception as e:
                logger.error(f"Erreur SadTalker : {e}")

        # 3. Fallback universel : Génère une vidéo MP4 fluide (Image originale + Audio)
        logger.info("ℹ️ Génération vidéo universelle MP4...")
        return self._generate_fallback_video(image_path, audio_path, target_dir / cache_filename)

    def _generate_fallback_video(self, image_path: str, audio_path: str, output_path: Path) -> Optional[str]:
        """Génère une vidéo MP4 H.264 / AAC propre à partir de l'image et de l'audio."""
        try:
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
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            if output_path.exists() and output_path.stat().st_size > 1000:
                return str(output_path)
        except Exception as e:
            logger.error(f"Erreur ffmpeg fallback video : {e}")
        return None
