"""
Routes API pour la gestion des avatars pédagogiques, upload d'images et tests vocaux.
"""

from pathlib import Path
from PIL import ImagePath
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.src.db.database import get_db
from backend.src.models.avatar import AvatarCreateRequest, AvatarUpdateRequest, StudioVocalTestRequest
from backend.src.services.avatar_service import (
    create_avatar,
    delete_avatar,
    generate_avatar_video,
    get_active_avatar,
    get_avatar_image_path,
    get_avatar_video_path,
    list_avatars,
    save_avatar_image,
    save_viseme_photo,
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


@router.post("/upload-viseme")
async def api_upload_viseme_photo(viseme_id: str, file: UploadFile = File(...)):
    """
    Upload d'une photo pour un visème spécifique (REST, CLOSED, OPEN_SMALL, etc.).
    Utilisé pour l'animation Sprite-Sheet cross-fade réaliste.
    """
    return await save_viseme_photo(file, viseme_id)


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


@router.post("/detect-landmarks")
def api_detect_avatar_landmarks(req: dict):
    """
    Analyse la compatibilité d'une photo d'avatar et détecte les repères faciaux précis.
    """
    from backend.src.services.avatar_service import AVATARS_STORAGE_DIR, analyze_face_landmarks
    photo_url = req.get("photoUrl") or req.get("photo_url") or req.get("fileName")
    if not photo_url:
        raise HTTPException(status_code=400, detail="URL ou nom de fichier d'avatar requis.")
    
    filename = photo_url.split("/api/avatars/images/")[-1] if "/api/avatars/images/" in photo_url else Path(photo_url).name
    path = AVATARS_STORAGE_DIR / filename
    return analyze_face_landmarks(path)


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


@router.post("/generate-video")
async def api_generer_video_avatar(req: dict, db: Session = Depends(get_db)):
    """
    Génère une vidéo parlante ultra-réaliste à partir d'une photo et d'un texte didactique.
    Prend en charge l'accélération GPU (Colab Pro / AWS) et le streaming Web MP4.
    """
    avatar_id = req.get("avatar_id") or req.get("avatarId")
    photo_url = req.get("photo_url") or req.get("photoUrl")
    phrase = req.get("phrase") or req.get("text") or req.get("question")
    voice = req.get("voice") or req.get("voix") or "vivienne"

    return await generate_avatar_video(
        db=db,
        avatar_id=avatar_id,
        photo_url=photo_url,
        phrase=phrase,
        voice=voice,
    )


@router.get("/videos/{filename}")
def api_servir_video_avatar(filename: str):
    """Sert une vidéo d'avatar générée avec streaming fluide H.264."""
    path = get_avatar_video_path(filename)
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "public, max-age=86400",
        "Accept-Ranges": "bytes",
    }
    return FileResponse(str(path), media_type="video/mp4", headers=headers)


# Route de test vocal dans le Studio Vocal
vocal_router = APIRouter(tags=["Studio Vocal"])


@vocal_router.post("/api/studio-vocal/test-audio")
async def api_studio_vocal_test_audio(req: StudioVocalTestRequest):
    """Génère un extrait audio de test pour le Studio Vocal (voix neurale haute fidélité)."""
    return await test_voice_audio(req)

