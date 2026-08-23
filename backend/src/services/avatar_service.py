import os
import shutil
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

ROOT_DIR = Path(__file__).resolve().parents[3]
AI_ENGINE_DIR = ROOT_DIR / "ai-engine" / "src"
AVATARS_STORAGE_DIR = ROOT_DIR / "data" / "avatars"
AVATARS_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

for p in (ROOT_DIR, AI_ENGINE_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from alternia.tts.engine import TTSEngine
from backend.src.db.models import AvatarPedagogique
from backend.src.models.avatar import AvatarCreateRequest, AvatarUpdateRequest, StudioVocalTestRequest


def map_avatar_to_dict(av: AvatarPedagogique) -> Dict[str, Any]:
    return {
        "id": av.id,
        "nom": av.nom,
        "matiere": av.matiere,
        "stylePedagogique": av.style_pedagogique,
        "voixTts": av.voix_tts,
        "photoUrl": av.photo_url,
        "audioUrl": av.audio_sample_url,
        "audioFileName": av.audio_file_name,
        "actif": av.actif,
        "parDefaut": av.par_defaut,
        "dateCreation": av.date_creation.isoformat() if av.date_creation else None,
    }


async def save_avatar_image(file: UploadFile) -> Dict[str, str]:
    """
    Sauvegarde l'image uploadée par l'utilisateur dans le stockage data/avatars/
    et renvoie l'URL d'accès public et le nom de fichier.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant.")

    extension = Path(file.filename).suffix.lower()
    if extension not in [".jpg", ".jpeg", ".png", ".webp", ".svg"]:
        raise HTTPException(status_code=400, detail="Format non supporté. Utilisez JPG, PNG, WEBP ou SVG.")

    # Nom unique sécurisé
    clean_name = f"avatar_{uuid.uuid4().hex[:10]}{extension}"
    target_path = AVATARS_STORAGE_DIR / clean_name

    try:
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:  # 10 Mo max
            raise HTTPException(status_code=400, detail="L'image est trop volumineuse (max 10 Mo).")

        with open(target_path, "wb") as f:
            f.write(content)

        return {
            "photoUrl": f"/api/avatars/images/{clean_name}",
            "fileName": clean_name,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la sauvegarde de l'image : {exc}")


def get_avatar_image_path(filename: str) -> Path:
    """Retourne le chemin absolu vers l'image d'avatar demandée."""
    # Sécurité anti path-traversal
    safe_filename = Path(filename).name
    path = AVATARS_STORAGE_DIR / safe_filename
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Image d'avatar introuvable.")
    return path


def list_avatars(db: Session) -> List[Dict[str, Any]]:
    """Retourne la liste de tous les avatars pédagogiques."""
    avatars = db.query(AvatarPedagogique).order_by(AvatarPedagogique.par_defaut.desc(), AvatarPedagogique.nom.asc()).all()
    return [map_avatar_to_dict(av) for av in avatars]


def get_active_avatar(db: Session) -> Dict[str, Any]:
    """Retourne l'avatar pédagogique actif / par défaut."""
    av = db.query(AvatarPedagogique).filter(AvatarPedagogique.par_defaut == True).first()
    if not av:
        av = db.query(AvatarPedagogique).filter(AvatarPedagogique.actif == True).first()
    if not av:
        av = db.query(AvatarPedagogique).first()

    if not av:
        # Création de l'avatar par défaut Vivienne si la base est vide
        av = AvatarPedagogique(
            id="avatar-vivienne",
            nom="Professeure Vivienne",
            matiere="SVT & Sciences Naturelles",
            style_pedagogique="Chaleureuse, bienveillante et explicite avec exemples concrets",
            voix_tts="vivienne",
            photo_url="assets/avatars/vivienne.svg",
            actif=True,
            par_defaut=True,
        )
        db.add(av)
        db.commit()
        db.refresh(av)

    return map_avatar_to_dict(av)


def create_avatar(db: Session, req: AvatarCreateRequest) -> Dict[str, Any]:
    """Crée un nouvel avatar pédagogique et gère la sélection par défaut."""
    if req.par_defaut:
        # Désactiver l'ancien avatar par défaut
        db.query(AvatarPedagogique).update({AvatarPedagogique.par_defaut: False})

    av = AvatarPedagogique(
        id=f"avatar_{uuid.uuid4().hex[:8]}",
        nom=req.nom.strip(),
        matiere=req.matiere.strip(),
        style_pedagogique=req.style_pedagogique or "Bienveillant, rigoureux et interactif",
        voix_tts=req.voix_tts or "vivienne",
        photo_url=req.photo_url or "assets/avatars/vivienne.svg",
        audio_sample_url=req.audio_sample_url,
        audio_file_name=req.audio_file_name,
        actif=True,
        par_defaut=bool(req.par_defaut),
    )
    db.add(av)
    db.commit()
    db.refresh(av)
    return map_avatar_to_dict(av)


def update_avatar(db: Session, avatar_id: str, req: AvatarUpdateRequest) -> Dict[str, Any]:
    """Met à jour un avatar existant."""
    av = db.query(AvatarPedagogique).filter(AvatarPedagogique.id == avatar_id).first()
    if not av:
        raise HTTPException(status_code=404, detail="Avatar introuvable.")

    if req.nom is not None:
        av.nom = req.nom.strip()
    if req.matiere is not None:
        av.matiere = req.matiere.strip()
    if req.style_pedagogique is not None:
        av.style_pedagogique = req.style_pedagogique
    if req.voix_tts is not None:
        av.voix_tts = req.voix_tts
    if req.photo_url is not None:
        av.photo_url = req.photo_url
    if req.actif is not None:
        av.actif = req.actif
    if req.par_defaut:
        db.query(AvatarPedagogique).update({AvatarPedagogique.par_defaut: False})
        av.par_defaut = True
        av.actif = True

    db.commit()
    db.refresh(av)
    return map_avatar_to_dict(av)


def set_active_avatar(db: Session, avatar_id: str) -> Dict[str, Any]:
    """Définit un avatar comme l'avatar par défaut de toute l'application."""
    av = db.query(AvatarPedagogique).filter(AvatarPedagogique.id == avatar_id).first()
    if not av:
        raise HTTPException(status_code=404, detail="Avatar introuvable.")

    db.query(AvatarPedagogique).update({AvatarPedagogique.par_defaut: False})
    av.par_defaut = True
    av.actif = True
    db.commit()
    db.refresh(av)
    return map_avatar_to_dict(av)


def delete_avatar(db: Session, avatar_id: str) -> Dict[str, Any]:
    """Supprime un avatar pédagogique."""
    av = db.query(AvatarPedagogique).filter(AvatarPedagogique.id == avatar_id).first()
    if not av:
        raise HTTPException(status_code=404, detail="Avatar introuvable.")

    was_default = av.par_defaut
    db.delete(av)
    db.commit()

    # Si c'était l'avatar par défaut, désigner le premier avatar restant
    if was_default:
        next_av = db.query(AvatarPedagogique).first()
        if next_av:
            next_av.par_defaut = True
            db.commit()

    return {"succes": True, "id": avatar_id}


async def test_voice_audio(req: StudioVocalTestRequest) -> Response:
    """Génère un test audio pour le Studio Vocal (voix neurale haute fidélité)."""
    phrase = req.phrase or "Bonjour ! Je suis ton enseignant virtuel AlternIA. Quelle notion souhaites-tu réviser aujourd'hui ?"
    tts_engine = TTSEngine(voice=req.voix or "vivienne")
    try:
        audio_bytes = await tts_engine.synthesize_to_bytes(phrase)
        if not audio_bytes:
            raise HTTPException(status_code=500, detail="Échec de la synthèse audio de test.")
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=test_avatar.mp3"}
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur TTS : {exc}")
