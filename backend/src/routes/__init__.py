"""
Package routes (API REST FastAPI).
"""

from backend.src.routes.alertes_routes import router as alertes_router
from backend.src.routes.apprenants_routes import router as apprenants_router
from backend.src.routes.auth_routes import router as auth_router
from backend.src.routes.avatars_routes import router as avatars_router, vocal_router
from backend.src.routes.boitiers_routes import router as boitiers_router
from backend.src.routes.chat_routes import router as chat_router
from backend.src.routes.device_routes import router as device_router
from backend.src.routes.insights_routes import router as insights_router
from backend.src.routes.parent_routes import router as parent_router
from backend.src.routes.rapports_routes import router as rapports_router
from backend.src.routes.revision_routes import router as revision_router
from backend.src.routes.esp32_routes import router as esp32_router
from backend.src.routes.culture_routes import router as culture_router
from backend.src.routes.duel_routes import router as duel_router
from backend.src.routes.podcast_routes import router as podcast_router
from backend.src.routes.sync_routes import router as sync_router

__all__ = [
    "chat_router",
    "auth_router",
    "boitiers_router",
    "apprenants_router",
    "avatars_router",
    "vocal_router",
    "alertes_router",
    "insights_router",
    "device_router",
    "parent_router",
    "rapports_router",
    "revision_router",
    "esp32_router",
    "culture_router",
    "duel_router",
    "podcast_router",
    "sync_router",
]
