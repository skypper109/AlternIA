import os
import time
import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger("AlternIA.TalkingHead.Cloud")

class CloudTalkingHeadService:
    """
    Module Standalone d'Animation d'Avatar via Cloud API (fal.ai / Replicate).
    Conçu pour un usage hybride (sans GPU local) si la connexion internet le permet.
    
    Pour l'utiliser sur Google Colab pour des tests :
    1. Ouvrir un Notebook Colab
    2. Cloner le repo SadTalker ou utiliser ce wrapper API (avec la clé API fal.ai)
    3. Pour l'intégration API : définir la variable d'environnement `FAL_KEY`
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("FAL_KEY")
        if not self.api_key:
            logger.warning("Clé API fal.ai manquante. Définissez la variable d'environnement FAL_KEY.")
            
        # Point de terminaison fal.ai pour SadTalker
        # L'URL exacte dépend du modèle déployé sur leur plateforme
        self.api_url = "https://fal.run/fal-ai/sadtalker"

    def is_available(self) -> bool:
        """Vérifie si la clé API est présente."""
        return bool(self.api_key)

    def generate_video_sync(
        self,
        image_url: str,
        audio_url: str,
        pose_style: int = 0
    ) -> Optional[str]:
        """
        Génère une vidéo via l'API Cloud (attente synchrone).
        
        Note : l'image et l'audio doivent être des URLs publiques accessibles 
        par le service cloud.
        
        Args:
            image_url: URL publique vers la photo source.
            audio_url: URL publique vers le fichier audio.
            pose_style: Style de mouvement de tête (0-45).
            
        Returns:
            L'URL de la vidéo MP4 générée, ou None en cas d'erreur.
        """
        if not self.is_available():
            logger.error("Impossible d'utiliser le service Cloud : clé API manquante.")
            return None

        headers = {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "source_image_url": image_url,
            "driven_audio_url": audio_url,
            "pose_style": pose_style,
            "enhancer": "gfpgan"  # Sur le cloud on active toujours l'amélioration car ce sont de gros GPU
        }

        logger.info(f"Envoi de la requête de génération Cloud : {self.api_url}")
        try:
            # Appel API bloquant
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                video_url = result.get("video_url")
                if video_url:
                    logger.info("Vidéo générée avec succès via le Cloud.")
                    return video_url
                else:
                    logger.error("Le service a répondu 200 mais aucune 'video_url' n'a été retournée.")
            else:
                logger.error(f"Erreur de l'API Cloud (Code {response.status_code}): {response.text}")
                
        except requests.exceptions.Timeout:
            logger.error("L'appel à l'API Cloud a expiré (timeout 120s).")
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'appel Cloud : {e}")

        return None
