"""
Package services (Logique métier et intégration temps réel).
"""

from backend.src.services.orchestrator_service import (
    AppState,
    get_orchestrator,
    normalize_student_class,
    state,
)
from backend.src.services.learning_service import record_student_interaction
from backend.src.services.analytics_service import (
    get_realtime_insights,
    get_realtime_statistiques,
)
from backend.src.services.auth_service import (
    authenticate_user,
    get_current_user_info,
    register_parent,
    register_school,
)
from backend.src.services.boitier_service import (
    configure_boitier_wifi,
    get_boitier_detail,
    list_boitiers,
    sync_boitier,
)
from backend.src.services.apprenant_service import (
    get_apprenant_detail,
    list_apprenant_sessions,
    list_apprenants,
)
from backend.src.services.avatar_service import (
    create_avatar,
    delete_avatar,
    list_avatars,
    test_voice_audio,
)
from backend.src.services.alerte_service import (
    list_alertes,
    resolve_alerte,
)
from backend.src.services.security import (
    hash_password,
    verify_password,
)

__all__ = [
    "AppState",
    "get_orchestrator",
    "normalize_student_class",
    "state",
    "record_student_interaction",
    "get_realtime_insights",
    "get_realtime_statistiques",
    "authenticate_user",
    "register_parent",
    "register_school",
    "get_current_user_info",
    "list_boitiers",
    "get_boitier_detail",
    "sync_boitier",
    "configure_boitier_wifi",
    "list_apprenants",
    "get_apprenant_detail",
    "list_apprenant_sessions",
    "list_avatars",
    "create_avatar",
    "delete_avatar",
    "test_voice_audio",
    "list_alertes",
    "resolve_alerte",
    "hash_password",
    "verify_password",
]

