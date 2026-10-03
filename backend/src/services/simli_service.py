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


_pyav_strict_patched = False


def _patch_pyav_for_experimental_codecs():
    """
    RÈGLE FFmpeg / PyAV :
    Si un codec expérimental (comme vorbis) est utilisé, FFmpeg requiert l'option 'strict: experimental'.
    On injecte de manière idempotente l'option dans PyAV via les options du dictionnaire,
    sans manipuler d'attribut interne 'strict' inexistant sur AudioCodecContext (Cython).
    """
    global _pyav_strict_patched
    if _pyav_strict_patched:
        return

    try:
        import av
        if getattr(av, "_alternia_strict_patched", False):
            _pyav_strict_patched = True
            return

        if hasattr(av.container, "OutputContainer") and hasattr(av.container.OutputContainer, "add_stream"):
            _orig_add_stream = av.container.OutputContainer.add_stream

            def _safe_add_stream(self_cont, *args, **kwargs):
                if len(args) >= 3:
                    args_list = list(args)
                    opts = dict(args_list[2] or {})
                    opts.setdefault("strict", "experimental")
                    args_list[2] = opts
                    args = tuple(args_list)
                else:
                    opts = dict(kwargs.get("options") or {})
                    opts.setdefault("strict", "experimental")
                    kwargs["options"] = opts

                return _orig_add_stream(self_cont, *args, **kwargs)

            av.container.OutputContainer.add_stream = _safe_add_stream

        if hasattr(av, "open"):
            _orig_av_open = av.open

            def _safe_av_open(*args, **kwargs):
                opts = dict(kwargs.get("options") or {})
                opts.setdefault("strict", "experimental")
                kwargs["options"] = opts
                return _orig_av_open(*args, **kwargs)

            av.open = _safe_av_open

        setattr(av, "_alternia_strict_patched", True)
        _pyav_strict_patched = True
    except Exception as patch_err:
        logger.debug(f"PyAV strict patch note : {patch_err}")


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

    def transcode_to_ios_compatible_mp4(self, input_path: str, output_path: str) -> bool:
        """
        Transcode la vidéo en H.264 (yuv420p) + AAC 44.1kHz avec +faststart.
        Obligatoire pour que le lecteur iOS (AVPlayer de Flutter) et Android lisent
        la vidéo instantanément en streaming sans geler ni bloquer l'image.
        """
        try:
            temp_fixed = str(output_path) + ".tmp_ios.mp4"
            cmd = [
                "ffmpeg", "-y", "-i", str(input_path),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
                "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
                "-movflags", "+faststart",
                temp_fixed
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            if Path(temp_fixed).exists() and Path(temp_fixed).stat().st_size > 1000:
                Path(temp_fixed).replace(output_path)
                return True
        except Exception as e:
            logger.warning(f"Erreur transcodage FFmpeg iOS MP4 : {e}")
        return False

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
            _patch_pyav_for_experimental_codecs()

            from simli import SimliClient, SimliConfig
            from simli.renderers.renderers import FileRenderer

            logger.info(f"[SimliBackendService] Lancement de la génération vidéo Simli (Face ID: {target_face_id})...")
            
            simli_config = SimliConfig(
                faceId=target_face_id,
                maxSessionLength=max_duration,
                maxIdleTime=10,
            )
            async with SimliClient(
                api_key=self.api_key,
                config=simli_config,
            ) as connection:
                await connection.send(pcm_bytes)
                # On force 'aac' pour l'audio au lieu de 'vorbis' afin d'éviter les codecs expérimentaux dans MP4
                renderer = FileRenderer(
                    client=connection,
                    filename=str(target_output),
                    videoCodec="h264",
                    audioCodec="aac",
                )
                await renderer.render()

            if target_output.exists() and target_output.stat().st_size > 1000:
                # Transcodage immédiat en MP4 H.264/AAC avec faststart pour iOS & Android
                self.transcode_to_ios_compatible_mp4(str(target_output), str(target_output))
                logger.info(f"✅ [SimliBackendService] Vidéo Simli générée et optimisée avec succès : {target_output.name}")
                return str(target_output)

        except ImportError as err:
            logger.warning(f"Package 'simli-ai' ou dépendance manquante (av, etc.) : {err}")
        except Exception as e:
            logger.error(f"❌ [SimliBackendService] Erreur lors de la génération vidéo Simli : {e}")

        return None
