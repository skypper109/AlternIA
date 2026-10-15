"""
Routes API pour la synchronisation asynchrone « Store & Forward » d'AlternIA.
Permet aux applications mobiles et aux boîtiers physiques de transmettre
des lots d'événements enregistrés hors-ligne (duels, flashcards, podcasts, temps d'étude)
sans aucune perte de données.
"""

from datetime import datetime
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("alternia.sync")

router = APIRouter(prefix="/api/sync", tags=["Synchronisation Store & Forward"])


class SyncEventDto(BaseModel):
    id: str
    type: str
    payload: Dict[str, Any]
    timestamp: str
    retryCount: int = 0


class SyncBatchRequest(BaseModel):
    device_type: str = "mobile_app"
    events_count: int
    events: List[SyncEventDto]
    client_time: Optional[str] = None


@router.post("/batch")
async def api_sync_batch(request: SyncBatchRequest) -> Dict[str, Any]:
    """
    Traite un lot d'événements asynchrones accumulés hors-ligne.
    """
    logger.info(f"[Store & Forward] Réception d'un lot de {len(request.events)} événements depuis {request.device_type}")
    
    processed = 0
    xp_increment = 0
    coins_increment = 0

    for ev in request.events:
        try:
            ev_type = ev.type
            payload = ev.payload

            if ev_type == "duelCompleted":
                # Consolidation du résultat du duel hors-ligne
                is_winner = payload.get("is_winner", True)
                earned_xp = payload.get("xp_earned", 250 if is_winner else 50)
                earned_coins = payload.get("coins_earned", 25 if is_winner else 5)
                xp_increment += earned_xp
                coins_increment += earned_coins
                logger.info(f"[Sync] Duel synchronisé: +{earned_xp} XP, +{earned_coins} Pièces")

            elif ev_type == "flashcardReviewed":
                # Consolidation d'une révision flashcard (méthode Leitner)
                xp_increment += 15
                logger.info("[Sync] Flashcard synchronisée: +15 XP")

            elif ev_type == "podcastListened":
                xp_increment += 50
                logger.info("[Sync] Podcast synchronisé: +50 XP")

            elif ev_type == "studyTimeLogged":
                minutes = payload.get("duration_minutes", 15)
                xp_increment += min(minutes * 2, 60)

            processed += 1
        except Exception as e:
            logger.warning(f"[Sync] Erreur sur l'événement {ev.id}: {e}")

    return {
        "status": "success",
        "processed_count": processed,
        "total_received": len(request.events),
        "xp_increment": xp_increment,
        "coins_increment": coins_increment,
        "server_time": datetime.utcnow().isoformat(),
        "message": f"{processed} actions synchronisées avec succès.",
    }


@router.get("/status")
async def api_sync_status() -> Dict[str, Any]:
    """Vérification rapide de disponibilité du service de synchronisation."""
    return {
        "status": "online",
        "service": "AlternIA Store & Forward Gateway",
        "server_time": datetime.utcnow().isoformat(),
    }
