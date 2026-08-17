"""
Package models (Schémas Pydantic / DTOs).
"""

from backend.src.models.chat import (
    ChatMessagePayload,
    ChatRequest,
    ChatSource,
    ChatResponse,
    InteractionRecord,
    ResetSessionRequest,
)
from backend.src.models.auth import (
    ConnexionRequest,
    InscriptionParentRequest,
    InscriptionEtablissementRequest,
)
from backend.src.models.boitier import (
    BoitierSyncRequest,
    BoitierWifiRequest,
)
from backend.src.models.avatar import (
    AvatarCreateRequest,
    StudioVocalTestRequest,
)
from backend.src.models.device import (
    TTSRequest,
)

__all__ = [
    "ChatMessagePayload",
    "ChatRequest",
    "ChatSource",
    "ChatResponse",
    "InteractionRecord",
    "ResetSessionRequest",
    "ConnexionRequest",
    "InscriptionParentRequest",
    "InscriptionEtablissementRequest",
    "BoitierSyncRequest",
    "BoitierWifiRequest",
    "AvatarCreateRequest",
    "StudioVocalTestRequest",
    "TTSRequest",
]
