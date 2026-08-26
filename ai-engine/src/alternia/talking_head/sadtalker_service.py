import os
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("AlternIA.TalkingHead.SadTalker")

class SadTalkerService:
    """
    Module Standalone d'Animation d'Avatar (SadTalker)
    Conçu pour être déployé sur un serveur Edge avec GPU (ex: Jetson Nano Super).
    
    Prérequis matériels (NVIDIA Jetson) :
    - JetPack SDK installé (inclut CUDA, cuDNN, TensorRT)
    - PyTorch pour Jetson (https://forums.developer.nvidia.com/t/pytorch-for-jetson)
    
    Installation du dépôt SadTalker :
    ```bash
    git clone https://github.com/OpenTalker/SadTalker.git
    cd SadTalker
    pip install -r requirements.txt
    # Télécharger les checkpoints (voir le README du repo)
    ```
    """

    def __init__(self, sadtalker_dir: str = "/opt/sadtalker"):
        self.sadtalker_dir = Path(sadtalker_dir)
        self.python_exe = "python3"
        self.script_path = self.sadtalker_dir / "inference.py"

        if not self.sadtalker_dir.exists():
            logger.warning(f"Répertoire SadTalker non trouvé : {self.sadtalker_dir}. Ce module nécessite l'installation du dépôt officiel.")

    def is_available(self) -> bool:
        """Vérifie si le script d'inférence est présent."""
        return self.script_path.exists()

    def generate_video(
        self,
        image_path: str,
        audio_path: str,
        output_dir: Optional[str] = None,
        pose_style: int = 0,
        enhancement: bool = False
    ) -> Optional[str]:
        """
        Génère une vidéo de tête parlante à partir d'une photo et d'un audio.
        
        Args:
            image_path: Chemin absolu vers la photo source (JPG/PNG).
            audio_path: Chemin absolu vers le fichier audio (WAV/MP3).
            output_dir: Dossier de destination pour la vidéo.
            pose_style: Index de style de mouvement (0-45).
            enhancement: Si True, active GFPGAN (meilleure qualité de visage, mais plus lent).
        
        Returns:
            Le chemin absolu vers le fichier vidéo MP4 généré, ou None en cas d'erreur.
        """
        if not self.is_available():
            logger.error("SadTalker n'est pas installé ou configuré.")
            return None

        if not output_dir:
            output_dir = tempfile.gettempdir()
            
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

        cmd = [
            self.python_exe,
            str(self.script_path),
            "--driven_audio", str(audio_path),
            "--source_image", str(image_path),
            "--result_dir", str(output_dir),
            "--pose_style", str(pose_style),
            "--cpu", "False",  # Forcer l'utilisation du GPU Jetson
            "--preprocess", "full"  # 'full' est recommandé pour les avatars complets
        ]

        if enhancement:
            # Note: GFPGAN est lourd pour un Jetson, à utiliser avec précaution
            cmd.append("--enhancer")
            cmd.append("gfpgan")

        logger.info(f"Démarrage de la génération SadTalker : {' '.join(cmd)}")
        
        try:
            # Exécution en sous-processus. 
            # Sur Jetson, cela peut prendre entre 10 et 60 secondes selon la longueur de l'audio.
            process = subprocess.run(
                cmd,
                cwd=str(self.sadtalker_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            
            logger.info("Génération terminée avec succès.")
            
            # Chercher le fichier MP4 généré dans le dossier de résultat
            # SadTalker crée un sous-dossier avec le nom de l'image et un timestamp
            # On cherche récursivement le MP4 le plus récent
            mp4_files = list(output_dir_path.glob("**/*.mp4"))
            if mp4_files:
                # Trier par date de modification pour obtenir le plus récent
                latest_video = max(mp4_files, key=lambda p: p.stat().st_mtime)
                return str(latest_video)
                
            logger.error("La commande s'est terminée mais aucun fichier MP4 n'a été trouvé.")
            return None

        except subprocess.CalledProcessError as e:
            logger.error(f"Erreur d'exécution SadTalker (Code {e.returncode}):\nSTDOUT: {e.stdout}\nSTDERR: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la génération SadTalker : {e}")
            return None
