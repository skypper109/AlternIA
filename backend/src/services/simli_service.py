"""
Service de génération vidéo d'avatar photoréaliste via l'API officielle Simli AI.
Utilise le Face ID et la clé API pour produire une animation labiale HD parfaite.
"""

import os
import io
import asyncio
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger("AlternIA.SimliService")

SIMLI_API_KEY = os.getenv("SIMLI_API_KEY", "1e1ikibdppliekw9mt04nf")
SIMLI_FACE_ID = os.getenv("SIMLI_FACE_ID", "b9e5fba3-071a-4e35-896e-211c4d6eaa7b")


class SimliBackendService:
    def __init__(self, api_key: str = SIMLI_API_KEY, face_id: str = SIMLI_FACE_ID):
        self.api_key = api_key
        self.face_id = face_id

    def convert_audio_to_pcm16(self, audio_path: str) -> Optional[bytes]:
        """Convertit n'importe quel fichier audio (MP3/WAV) en PCM16 mono 16000Hz (requis par Simli)."""
        try:
            cmd = [
                "ffmpeg", "-y", "-i", audio_path,
                "-f", "s16le", "-acodec", "pcm_s16le",
                "-ar", "16000", "-ac", "1", "-"
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return res.stdout
        except Exception as e:
            logger.warning(f"Erreur conversion FFmpeg PCM16 pour Simli : {e}")
            return None

    async def generate_video(
        self,
        audio_path: str,
        output_path: str,
        face_id: Optional[str] = None,
        max_duration: int = 60
    ) -> Optional[str]:
        """Génère un fichier vidéo MP4 synchronisé avec les lèvres de l'avatar Simli."""
        pcm_bytes = self.convert_audio_to_pcm16(audio_path)
        if not pcm_bytes:
            return None

        target_face_id = face_id or self.face_id
        target_output = Path(output_path)
        target_output.parent.mkdir(parents=True, exist_ok=True)

        try:
            from simli import SimliClient, SimliConfig
            from simli.renderers import FileRenderer

            logger.info(f"🚀 [SimliBackendService] Lancement de la génération vidéo Simli (Face ID: {target_face_id})...")
            
            async with SimliClient(
                SimliConfig(
                    apiKey=self.api_key,
                    faceId=target_face_id,
                    maxSessionLength=max_duration,
                    maxIdleTime=10,
                )
            ) as connection:
                await connection.send(pcm_bytes)
                renderer = FileRenderer(connection, output_file=str(target_output))
                await renderer.render()

            if target_output.exists() and target_output.stat().st_size > 1000:
                logger.info(f"✅ [SimliBackendService] Vidéo générée avec succès : {target_output.name}")
                return str(target_output)

        except ImportError:
            logger.warning("Package 'simli-ai' non installé sur le serveur.")
        except Exception as e:
            logger.error(f"❌ [SimliBackendService] Erreur lors de la génération vidéo Simli : {e}")

        return None
