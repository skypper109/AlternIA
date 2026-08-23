"""
Routes API pour la gestion des avatars pédagogiques, upload d'images et tests vocaux.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.src.db.database import get_db
from backend.src.models.avatar import AvatarCreateRequest, AvatarUpdateRequest, StudioVocalTestRequest
from backend.src.services.avatar_service import (
    create_avatar,
    delete_avatar,
    get_active_avatar,
    get_avatar_image_path,
    list_avatars,
    save_avatar_image,
    set_active_avatar,
    test_voice_audio,
    update_avatar,
)

router = APIRouter(prefix="/api/avatars", tags=["Avatars Pédagogiques"])


@router.get("")
def api_liste_avatars(db: Session = Depends(get_db)):
    """Liste de tous les avatars pédagogiques configurés."""
    return list_avatars(db)


@router.get("/actif")
def api_avatar_actif(db: Session = Depends(get_db)):
    """Retourne l'avatar actuellement actif par défaut sur la plateforme et le boîtier."""
    return get_active_avatar(db)


@router.post("/upload")
async def api_upload_avatar_image(file: UploadFile = File(...)):
    """
    Upload d'une image pour un avatar (photo de prof, illustration, personnage 2D/3D).
    Sauvegarde dans data/avatars/ et renvoie l'URL publique.
    """
    return await save_avatar_image(file)


@router.get("/images/{filename}")
def api_serve_avatar_image(filename: str):
    """Sert une image d'avatar enregistrée."""
    path = get_avatar_image_path(filename)
    # Détermination du content-type
    ext = path.suffix.lower()
    media_type = "image/png"
    if ext in [".jpg", ".jpeg"]:
        media_type = "image/jpeg"
    elif ext == ".webp":
        media_type = "image/webp"
    elif ext == ".svg":
        media_type = "image/svg+xml"

    headers = {
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "public, max-age=86400",
    }
    return FileResponse(str(path), media_type=media_type, headers=headers)


@router.post("")
def api_creer_avatar(req: AvatarCreateRequest, db: Session = Depends(get_db)):
    """Crée un nouvel avatar d'enseignant IA."""
    return create_avatar(db, req)


@router.put("/{avatar_id}/activer")
def api_activer_avatar(avatar_id: str, db: Session = Depends(get_db)):
    """Définit un avatar comme l'avatar actif par défaut."""
    return set_active_avatar(db, avatar_id)


@router.put("/{avatar_id}")
def api_modifier_avatar(avatar_id: str, req: AvatarUpdateRequest, db: Session = Depends(get_db)):
    """Met à jour les informations d'un avatar."""
    return update_avatar(db, avatar_id, req)


@router.delete("/{avatar_id}")
def api_supprimer_avatar(avatar_id: str, db: Session = Depends(get_db)):
    """Supprime un profil d'avatar."""
    return delete_avatar(db, avatar_id)


# Route de test vocal dans le Studio Vocal
vocal_router = APIRouter(tags=["Studio Vocal"])


@vocal_router.post("/api/studio-vocal/test-audio")
async def api_studio_vocal_test_audio(req: StudioVocalTestRequest):
    """Génère un extrait audio de test pour le Studio Vocal (voix neurale haute fidélité)."""
    return await test_voice_audio(req)
