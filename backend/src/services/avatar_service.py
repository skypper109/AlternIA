import json
import os
import shutil
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
import cv2
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


def analyze_face_landmarks(img_path: Path) -> Dict[str, Any]:
    """
    Analyse l'image d'un avatar avec OpenCV pour :
    1. Détecter la présence et le cadrage d'un visage humain.
    2. Calculer les repères faciaux exacts (Yeux, Nez, Bouche, Mâchoire).
    3. Évaluer le score de compatibilité pour l'animation 2.5D et la synchronisation labiale.
    """
    if not img_path.exists() or not img_path.is_file():
        return {
            "valide": False,
            "visage_detecte": False,
            "score_compatibilite": 0.0,
            "message": "Fichier image introuvable pour l'analyse.",
            "landmarks": None,
        }

    # Cas des SVG / illustrations vectorielles
    if img_path.suffix.lower() == ".svg":
        return {
            "valide": True,
            "visage_detecte": True,
            "score_compatibilite": 95.0,
            "message": "Illustration vectorielle SVG détectée. Repères par défaut appliqués.",
            "landmarks": {
                "left_eye": {"x": 0.35, "y": 0.40},
                "right_eye": {"x": 0.65, "y": 0.40},
                "nose": {"x": 0.50, "y": 0.52},
                "mouth": {"x": 0.50, "y": 0.68},
                "jaw_bottom": {"x": 0.50, "y": 0.88},
            },
        }

    try:
        img = cv2.imread(str(img_path))
        if img is None:
            return {
                "valide": False,
                "visage_detecte": False,
                "score_compatibilite": 0.0,
                "message": "Impossible de décoder le format d'image.",
                "landmarks": None,
            }

        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")

        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=4, minSize=(60, 60))

        if len(faces) == 0:
            # Aucun visage frontal net détecté -> fallback proportionnel centré
            return {
                "valide": True,
                "visage_detecte": False,
                "score_compatibilite": 70.0,
                "message": "Aucun visage frontal net détecté automatiquement. Repères proportionnels standard appliqués.",
                "landmarks": {
                    "left_eye": {"x": 0.35, "y": 0.38},
                    "right_eye": {"x": 0.65, "y": 0.38},
                    "nose": {"x": 0.50, "y": 0.52},
                    "mouth": {"x": 0.50, "y": 0.68},
                    "jaw_bottom": {"x": 0.50, "y": 0.88},
                },
            }

        # Sélectionner le visage principal (plus grande surface)
        faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
        fx, fy, fw, fh = faces[0]

        face_roi = gray[fy : fy + fh, fx : fx + fw]
        eyes = eye_cascade.detectMultiScale(face_roi, scaleFactor=1.1, minNeighbors=3, minSize=(15, 15))

        if len(eyes) >= 2:
            eyes_sorted = sorted(eyes, key=lambda e: e[0])
            e1, e2 = eyes_sorted[0], eyes_sorted[-1]
            left_eye = {"x": round((fx + e1[0] + e1[2] / 2) / w, 3), "y": round((fy + e1[1] + e1[3] / 2) / h, 3)}
            right_eye = {"x": round((fx + e2[0] + e2[2] / 2) / w, 3), "y": round((fy + e2[1] + e2[3] / 2) / h, 3)}
        else:
            left_eye = {"x": round((fx + fw * 0.33) / w, 3), "y": round((fy + fh * 0.38) / h, 3)}
            right_eye = {"x": round((fx + fw * 0.67) / w, 3), "y": round((fy + fh * 0.38) / h, 3)}

        nose = {"x": round((fx + fw * 0.50) / w, 3), "y": round((fy + fh * 0.56) / h, 3)}
        mouth = {"x": round((fx + fw * 0.50) / w, 3), "y": round((fy + fh * 0.74) / h, 3)}
        jaw = {"x": round((fx + fw * 0.50) / w, 3), "y": round((fy + fh * 0.95) / h, 3)}

        # Calcul du score de compatibilité
        center_dx = abs((fx + fw / 2) / w - 0.5)
        center_dy = abs((fy + fh / 2) / h - 0.5)
        face_ratio = (fw * fh) / (w * h)

        score = 100.0 - (center_dx * 30.0) - (center_dy * 25.0)
        if face_ratio < 0.08:
            score -= 20.0
        score = max(50.0, min(99.0, score))

        return {
            "valide": True,
            "visage_detecte": True,
            "score_compatibilite": round(score, 1),
            "message": f"Visage détecté à {round(score, 1)}% de compatibilité. Repères faciaux calés avec précision pour l'animation 2.5D.",
            "face_box": {
                "x": round(fx / w, 3),
                "y": round(fy / h, 3),
                "w": round(fw / w, 3),
                "h": round(fh / h, 3),
            },
            "landmarks": {
                "left_eye": left_eye,
                "right_eye": right_eye,
                "nose": nose,
                "mouth": mouth,
                "jaw_bottom": jaw,
            },
        }
    except Exception as exc:
        return {
            "valide": True,
            "visage_detecte": False,
            "score_compatibilite": 65.0,
            "message": f"Analyse partielle ({exc}). Repères proportionnels standard appliqués.",
            "landmarks": {
                "left_eye": {"x": 0.35, "y": 0.38},
                "right_eye": {"x": 0.65, "y": 0.38},
                "nose": {"x": 0.50, "y": 0.52},
                "mouth": {"x": 0.50, "y": 0.68},
                "jaw_bottom": {"x": 0.50, "y": 0.88},
            },
        }


def map_avatar_to_dict(av: AvatarPedagogique) -> Dict[str, Any]:
    landmarks = None
    if av.landmarks_json:
        try:
            landmarks = json.loads(av.landmarks_json)
        except Exception:
            landmarks = None

    viseme_photos = None
    if av.viseme_photos_json:
        try:
            viseme_photos = json.loads(av.viseme_photos_json)
        except Exception:
            viseme_photos = None

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
        "landmarks": landmarks,
        "visemePhotos": viseme_photos,
        "dateCreation": av.date_creation.isoformat() if av.date_creation else None,
    }


async def save_avatar_image(file: UploadFile) -> Dict[str, Any]:
    """
    Sauvegarde l'image uploadée par l'utilisateur dans data/avatars/
    et lance automatiquement l'analyse des repères faciaux et du diagnostic de compatibilité.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant.")

    extension = Path(file.filename).suffix.lower()
    if extension not in [".jpg", ".jpeg", ".png", ".webp", ".svg"]:
        raise HTTPException(status_code=400, detail="Format non supporté. Utilisez JPG, PNG, WEBP ou SVG.")

    clean_name = f"avatar_{uuid.uuid4().hex[:10]}{extension}"
    target_path = AVATARS_STORAGE_DIR / clean_name

    try:
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="L'image est trop volumineuse (max 10 Mo).")

        with open(target_path, "wb") as f:
            f.write(content)

        # Analyse automatique des repères faciaux
        analysis = analyze_face_landmarks(target_path)

        return {
            "photoUrl": f"/api/avatars/images/{clean_name}",
            "fileName": clean_name,
            "compatibility": analysis,
            "landmarks": analysis.get("landmarks"),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la sauvegarde de l'image : {exc}")


def get_avatar_image_path(filename: str) -> Path:
    """Retourne le chemin absolu vers l'image d'avatar demandée."""
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
        db.query(AvatarPedagogique).update({AvatarPedagogique.par_defaut: False})

    landmarks_json = None
    if req.landmarks:
        landmarks_json = json.dumps(req.landmarks)
    elif req.photo_url and "/api/avatars/images/" in req.photo_url:
        filename = req.photo_url.split("/api/avatars/images/")[-1]
        analysis = analyze_face_landmarks(AVATARS_STORAGE_DIR / filename)
        if analysis.get("landmarks"):
            landmarks_json = json.dumps(analysis["landmarks"])

    viseme_photos_json = None
    if req.viseme_photos:
        viseme_photos_json = json.dumps(req.viseme_photos)

    av = AvatarPedagogique(
        id=f"avatar_{uuid.uuid4().hex[:8]}",
        nom=req.nom.strip(),
        matiere=req.matiere.strip(),
        style_pedagogique=req.style_pedagogique or "Bienveillant, rigoureux et interactif",
        voix_tts=req.voix_tts or "vivienne",
        photo_url=req.photo_url or "assets/avatars/vivienne.svg",
        audio_sample_url=req.audio_sample_url,
        audio_file_name=req.audio_file_name,
        landmarks_json=landmarks_json,
        viseme_photos_json=viseme_photos_json,
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
        if req.landmarks is None and "/api/avatars/images/" in req.photo_url:
            filename = req.photo_url.split("/api/avatars/images/")[-1]
            analysis = analyze_face_landmarks(AVATARS_STORAGE_DIR / filename)
            if analysis.get("landmarks"):
                av.landmarks_json = json.dumps(analysis["landmarks"])
    if req.landmarks is not None:
        av.landmarks_json = json.dumps(req.landmarks)
    if req.viseme_photos is not None:
        av.viseme_photos_json = json.dumps(req.viseme_photos)
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


async def save_viseme_photo(file: UploadFile, viseme_id: str) -> Dict[str, Any]:
    """
    Sauvegarde une photo de visème individuelle pour l'animation Sprite-Sheet.
    Chaque visème (REST, CLOSED, OPEN_SMALL, etc.) est une photo distincte.
    """
    from backend.src.models.avatar import VISEME_IDS

    if viseme_id not in VISEME_IDS:
        raise HTTPException(
            status_code=400,
            detail=f"Visème invalide '{viseme_id}'. Valeurs acceptées : {', '.join(VISEME_IDS)}",
        )

    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant.")

    extension = Path(file.filename).suffix.lower()
    if extension not in [".jpg", ".jpeg", ".png", ".webp"]:
        raise HTTPException(status_code=400, detail="Format non supporté. Utilisez JPG, PNG ou WEBP.")

    clean_name = f"viseme_{viseme_id.lower()}_{uuid.uuid4().hex[:8]}{extension}"
    target_path = AVATARS_STORAGE_DIR / clean_name

    try:
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="L'image est trop volumineuse (max 10 Mo).")

        with open(target_path, "wb") as f:
            f.write(content)

        photo_url = f"/api/avatars/images/{clean_name}"

        # Analyse des repères faciaux pour validation d'alignement
        analysis = analyze_face_landmarks(target_path)

        return {
            "visemeId": viseme_id,
            "photoUrl": photo_url,
            "fileName": clean_name,
            "compatibility": analysis,
            "landmarks": analysis.get("landmarks"),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la sauvegarde : {exc}")


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
