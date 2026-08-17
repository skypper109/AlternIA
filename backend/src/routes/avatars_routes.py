"""
Routes API pour la gestion des avatars pédagogiques et tests vocaux (Vivienne).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.src.db.database import get_db
from backend.src.models.avatar import AvatarCreateRequest, StudioVocalTestRequest
from backend.src.services.avatar_service import (
    create_avatar,
    delete_avatar,
    list_avatars,
    test_voice_audio,
)

router = APIRouter(tags=["Avatars Pédagogiques"])


@router.get("/api/avatars")
def api_liste_avatars(db: Session = Depends(get_db)):
    """Liste des avatars et voix pédagogiques disponibles (dont Vivienne)."""
    return list_avatars(db)


@router.post("/api/avatars")
def api_creer_avatar(req: AvatarCreateRequest, db: Session = Depends(get_db)):
    """Crée un nouvel avatar d'enseignant IA."""
    return create_avatar(db, req)


@router.delete("/api/avatars/{avatar_id}")
def api_supprimer_avatar(avatar_id: str, db: Session = Depends(get_db)):
    """Supprime un profil d'avatar."""
    return delete_avatar(db, avatar_id)


@router.post("/api/studio-vocal/test-audio")
async def api_studio_vocal_test_audio(req: StudioVocalTestRequest):
    """Génère un extrait audio de test pour le Studio Vocal (Vivienne neurale)."""
    return await test_voice_audio(req)
