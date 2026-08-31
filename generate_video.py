import asyncio
from backend.src.db.database import SessionLocal
from backend.src.services.avatar_service import generate_avatar_video, get_active_avatar

async def main():
    db = SessionLocal()
    av = get_active_avatar(db)
    print(f"🎬 Génération de la vidéo LivePortrait pour {av['nom']}...")
    try:
        res = await generate_avatar_video(
            db=db,
            avatar_id=av['id'],
            photo_url=av['photoUrl'],
            phrase=av.get('phrase', f"Bonjour ! Je suis {av['nom']}. Je suis à ta disposition pour t'expliquer toutes les notions de {av.get('matiere', 'SVT')}. Pose-moi toutes tes questions !"),
            nom=av['nom']
        )
        print(f"✅ Vidéo générée avec succès : {res['videoUrl']}")
    except Exception as e:
        print(f"❌ Erreur : {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
