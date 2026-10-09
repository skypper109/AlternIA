"""
Routes API pour le Mode Grin Éducatif d'AlternIA.
Gère les salons de révision locaux, la découverte des pairs à proximité
et le catalogue de ressources partagées en P2P.
"""

from datetime import datetime
import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/grin", tags=["Mode Grin Éducatif"])

# Stockage en mémoire vive des salons actifs du Grin
_ACTIVE_GRIN_ROOMS: List[Dict[str, Any]] = [
    {
        "id": "grin_room_01",
        "title": "Grin Bac TSE — Révise Kirina",
        "hostName": "Moussa Traoré",
        "hostClass": "TSE",
        "subject": "Mathématiques",
        "playerCount": 3,
        "maxPlayers": 6,
        "pinCode": "7412",
        "isLocalBoitier": True,
        "createdAt": datetime.utcnow().isoformat(),
    },
    {
        "id": "grin_room_02",
        "title": "Défi Physique Badalabougou",
        "hostName": "Fanta Diarra",
        "hostClass": "11eme",
        "subject": "Physique-Chimie",
        "playerCount": 2,
        "maxPlayers": 4,
        "pinCode": "3350",
        "isLocalBoitier": True,
        "createdAt": datetime.utcnow().isoformat(),
    },
]

_ACTIVE_PEERS: List[Dict[str, Any]] = [
    {
        "id": "peer_1",
        "name": "Moussa Traoré",
        "className": "TSE",
        "scoreSession": 1450,
        "deviceModel": "Boîtier AlternIA (ESP32-S3)",
        "isConnectedLocal": True,
    },
    {
        "id": "peer_2",
        "name": "Fanta Diarra",
        "className": "11eme Sc",
        "scoreSession": 1200,
        "deviceModel": "Infinix Hot 12",
        "isConnectedLocal": True,
    },
    {
        "id": "peer_3",
        "name": "Sekou Coulibaly",
        "className": "TSE",
        "scoreSession": 980,
        "deviceModel": "Tecno Spark 9",
        "isConnectedLocal": True,
    },
    {
        "id": "peer_4",
        "name": "Aminata Koné",
        "className": "10eme",
        "scoreSession": 850,
        "deviceModel": "Samsung Galaxy A13",
        "isConnectedLocal": True,
    },
]

_SHARED_RESOURCES: List[Dict[str, Any]] = [
    {
        "id": "res_01",
        "title": "Podcast Audio : Dérivées & Primitives",
        "subject": "Mathématiques",
        "type": "podcast",
        "sizeMb": "4.2 Mo",
        "sharedBy": "Boîtier AlternIA",
    },
    {
        "id": "res_02",
        "title": "Fiche Synthèse : Équations de Newton",
        "subject": "Physique-Chimie",
        "type": "fiche_cours",
        "sizeMb": "1.1 Mo",
        "sharedBy": "Moussa (TSE)",
    },
    {
        "id": "res_03",
        "title": "Flashcards : Indépendance & Empires",
        "subject": "Histoire-Géo",
        "type": "flashcards",
        "sizeMb": "0.8 Mo",
        "sharedBy": "Fanta (11eme)",
    },
]


class GrinRoomCreateRequest(BaseModel):
    title: str
    host_name: str
    host_class: str = "TSE"
    subject: str = "Mathématiques"
    max_players: int = 6


@router.get("/rooms")
async def api_list_grin_rooms() -> List[Dict[str, Any]]:
    """Liste des salons ouverts actuellement dans le Grin."""
    return _ACTIVE_GRIN_ROOMS


@router.post("/rooms/create")
async def api_create_grin_room(req: GrinRoomCreateRequest) -> Dict[str, Any]:
    """Crée un nouveau salon multijoueur sur le serveur ou le boîtier local."""
    pin = str(int(time.time() * 1000) % 9000 + 1000)
    new_room = {
        "id": f"room_{int(time.time())}",
        "title": req.title,
        "hostName": req.host_name,
        "hostClass": req.host_class,
        "subject": req.subject,
        "playerCount": 1,
        "maxPlayers": req.max_players,
        "pinCode": pin,
        "isLocalBoitier": True,
        "createdAt": datetime.utcnow().isoformat(),
    }
    _ACTIVE_GRIN_ROOMS.insert(0, new_room)
    return new_room


@router.get("/peers")
async def api_list_grin_peers() -> List[Dict[str, Any]]:
    """Liste des camarades découverts sur le réseau local du boîtier."""
    return _ACTIVE_PEERS


@router.get("/resources")
async def api_list_grin_resources() -> List[Dict[str, Any]]:
    """Catalogue de ressources éducatives disponibles pour le partage P2P."""
    return _SHARED_RESOURCES
