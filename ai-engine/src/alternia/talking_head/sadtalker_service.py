import hashlib
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger("AlternIA.TalkingHead.SadTalker")


class SadTalkerService:
    """
    Module d'Animation d'Avatar Vidéo Haute Fidélité (SadTalker / LivePortrait).
    Supporte :
    - Google Colab Pro (GPU NVIDIA A100 / L4 / T4)
    - Serveur Cloud AWS GPU (g5.xlarge / g4dn.xlarge)
    - Machine locale ou Edge (Jetson Nano) avec fallback automatique.
    """

    def __init__(self, sadtalker_dir: Optional[str] = None):
        # Chemins candidats pour localiser le dépôt SadTalker
        candidates = [
            os.environ.get("SADTALKER_DIR"),
            sadtalker_dir,
            "/workspace/SadTalker",  # RunPod
            "/content/SadTalker",  # Standard Google Colab
            str(Path.cwd() / "SadTalker"),
            str(Path.cwd().parent / "SadTalker"),
            "/opt/sadtalker",
        ]
        
        self.sadtalker_dir: Optional[Path] = None
        for c in candidates:
            if c and Path(c).exists() and (Path(c) / "inference.py").exists():
                self.sadtalker_dir = Path(c)
                break

        if self.sadtalker_dir is None:
            # Répertoire par défaut si existant
            default_path = Path("/content/SadTalker" if Path("/content").exists() else "/opt/sadtalker")
            if default_path.exists() and (default_path / "inference.py").exists():
                self.sadtalker_dir = default_path

        self.python_exe: str = sys.executable or "python3"
        self.script_path: Optional[Path] = (self.sadtalker_dir / "inference.py") if self.sadtalker_dir else None
        self.cache_dir: Path = Path(tempfile.gettempdir()) / "alternia_avatar_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        if not self.is_available():
            logger.info(
                f"ℹ️ SadTalker non détecté ({self.sadtalker_dir or 'non configuré'}). "
                "Le mode Cloud GPU ou le fallback vidéo sera utilisé."
            )

    def is_available(self) -> bool:
        """Vérifie si le script d'inférence officiel est présent."""
        return bool(self.sadtalker_dir and self.script_path and self.script_path.exists())

    def _compute_cache_key(self, image_path: str, audio_path: str) -> str:
        """Génère une clé de hachage unique pour la mise en cache de la vidéo."""
        try:
            with open(image_path, "rb") as f_img:
                img_hash = hashlib.md5(f_img.read()).hexdigest()[:10]
            with open(audio_path, "rb") as f_aud:
                aud_hash = hashlib.md5(f_aud.read()).hexdigest()[:10]
            return f"vid_{img_hash}_{aud_hash}.mp4"
        except Exception:
            return f"vid_{hashlib.md5(f'{image_path}_{audio_path}'.encode()).hexdigest()[:16]}.mp4"

    def generate_video(
        self,
        image_path: str,
        audio_path: str,
        output_dir: Optional[str] = None,
        pose_style: int = 0,
        enhancement: bool = False,
        use_gpu: Optional[bool] = None,
    ) -> Optional[str]:
        """
        Génère une vidéo MP4 parlante ultra-réaliste à partir d'une photo et d'un audio.
        
        Args:
            image_path: Chemin absolu vers l'image du professeur (JPG/PNG).
            audio_path: Chemin absolu vers la voix synthétisée (WAV/MP3).
            output_dir: Dossier où stocker la vidéo finale.
            pose_style: Index de dynamisme des mouvements de tête (0-45).
            enhancement: Si True, active GFPGAN pour une amélioration haute définition du visage.
            use_gpu: Forcer l'utilisation GPU (True) ou CPU (False), None = auto-détection CUDA.
            
        Returns:
            Le chemin absolu vers le fichier vidéo MP4 généré, ou le fallback en local.
        """
        if not Path(image_path).exists() or not Path(audio_path).exists():
            logger.error(f"Fichier source manquant : Image={image_path}, Audio={audio_path}")
            return None

        # 1. Vérification du cache instantané
        cache_filename = self._compute_cache_key(image_path, audio_path)
        cached_file = self.cache_dir / cache_filename
        if cached_file.exists() and cached_file.stat().st_size > 1000:
            logger.info(f"⚡ Vidéo trouvée dans le cache GPU : {cached_file}")
            if output_dir:
                dest = Path(output_dir) / cache_filename
                shutil.copy(str(cached_file), str(dest))
                return str(dest)
            return str(cached_file)

        target_dir = Path(output_dir) if output_dir else self.cache_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        # 2. Si SadTalker officiel est installé (sur Colab Pro / AWS GPU)
        work_dir = Path(tempfile.mkdtemp(prefix="sadtalker_work_"))
        try:
            # Assurer le format WAV sur disque local
            wav_audio = audio_path
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
                        wav_audio = str(tmp_wav)
                except Exception:
                    wav_audio = audio_path

            if self.is_available() and self.sadtalker_dir and self.script_path:
                try:
                    import torch
                    cuda_available = torch.cuda.is_available()
                except ImportError:
                    cuda_available = False

                gpu_flag = "False" if (use_gpu is False or not cuda_available) else "True"
                use_cpu = (gpu_flag == "False")

                cmd = [
                    self.python_exe,
                    str(self.script_path),
                    "--driven_audio", str(wav_audio),
                    "--source_image", str(image_path),
                    "--result_dir", str(work_dir),
                    "--pose_style", str(pose_style),
                    "--preprocess", "crop",  # 'crop' ou 'full'
                    "--size", "256" if use_cpu else "512",
                ]

                checkpoints_dir = self.sadtalker_dir / "checkpoints"
                if checkpoints_dir.exists():
                    cmd.extend(["--checkpoint_dir", str(checkpoints_dir)])

                if use_cpu:
                    cmd.extend(["--cpu"])
                if enhancement and not use_cpu:
                    cmd.extend(["--enhancer", "gfpgan"])

                logger.info(f"🚀 Lancement inférence SadTalker GPU (disque local, CUDA={cuda_available}) : {' '.join(cmd)}")

                try:
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
                        if output_dir:
                            shutil.copy(str(latest), str(target_dir / cache_filename))
                            return str(target_dir / cache_filename)
                        return str(cached_file)
                except subprocess.CalledProcessError as e:
                    logger.error(f"❌ Erreur exécution SadTalker (code {e.returncode}) :\n{e.stderr or e.stdout or e}")
                except Exception as e:
                    logger.error(f"❌ Erreur exécution SadTalker : {e}")

            # 3. Fallback universel : Génère une vidéo MP4 propre sur disque local
            logger.info("ℹ️ Utilisation du générateur vidéo de fallback sur disque local...")
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
            try:
                shutil.rmtree(work_dir, ignore_errors=True)
            except Exception:
                pass

    def _generate_fallback_video(self, image_path: str, audio_path: str, output_path: Path) -> Optional[str]:
        """
        Génère une vidéo MP4 statique animée avec audio synchronisé via ffmpeg ou python.
        Permet de tester l'UI et le streaming vidéo même sans GPU lourd installé en local.
        """
        # Tentative avec ffmpeg si présent
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
                str(output_path)
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            if output_path.exists() and output_path.stat().st_size > 500:
                return str(output_path)
        except Exception:
            pass

        # Si ffmpeg n'est pas installé, copier l'image comme placeholder
        return str(image_path)
