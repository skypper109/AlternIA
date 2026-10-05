#!/usr/bin/env python3
"""Script CLI d'inférence et de test pour la reconnaissance de monuments CultureLens."""

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from culturelens_ai.src.recognizer import CultureLensRecognizer
except ImportError:
    try:
        from src.recognizer import CultureLensRecognizer
    except ImportError:
        from .src.recognizer import CultureLensRecognizer


def format_bar(confidence: float, width: int = 30) -> str:
    filled = int(confidence * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {confidence * 100:.1f}%"


def main():
    parser = argparse.ArgumentParser(
        description="Teste la reconnaissance d'un monument à partir d'une photo."
    )
    parser.add_argument(
        "image",
        type=str,
        help="Chemin vers l'image à tester (JPG, PNG, WebP)",
    )
    parser.add_argument(
        "--lat",
        type=float,
        default=None,
        help="Latitude optionnelle du smartphone",
    )
    parser.add_argument(
        "--lon",
        type=float,
        default=None,
        help="Longitude optionnelle du smartphone",
    )

    args = parser.parse_args()
    img_path = Path(args.image)

    if not img_path.exists():
        print(f"❌ Fichier introuvable : {img_path}")
        sys.exit(1)

    recognizer = CultureLensRecognizer.get_instance()
    user_coords = (args.lat, args.lon) if (args.lat and args.lon) else None

    result = recognizer.predict(img_path, user_coords=user_coords)

    print("\n" + "=" * 62)
    print("       RÉSULTAT DE L'IDENTIFICATION CULTURELENS (AI VISION)    ")
    print("=" * 62)
    print(f"📸 Image analysée      : {img_path.name}")
    print(f"⏱️  Temps d'inférence  : {result.get('inference_time_ms', 0)} ms")

    if result["is_identified"]:
        print(f"\n🏛️  MONUMENT CERTIFIÉ  : {result['name'].upper()}")
        print(f"📍 Localisation         : {result['ville']}")
        print(f"🏷️  Catégorie           : {result['category']}")
        print(f"📊 Certitude IA         : {format_bar(result['confidence'])}")
        print(f"🔍 Similarité cosinus   : {result['raw_similarity']:.4f}")
        print(f"✅ Statut               : {result['validation_status']}")

        features = result.get("visual_features", [])
        if features:
            print(f"\n🎨 Indices visuels identifiés :")
            for feat in features:
                print(f"   ✓ {feat}")

        print(f"\n📜 Explication : {result['explanation']}")

        print("\n🏆 Classement des correspondances (Top 3) :")
        for rank, match in enumerate(result.get("top_matches", []), 1):
            star = "⭐" if rank == 1 else "  "
            print(f"   {star} #{rank} {match['name']} ({match['ville']}) : {match['confidence']*100:.1f}%")
    else:
        print(f"\n⚠️ IDENTIFICATION INCERTAINE")
        print(f"📊 Meilleure supposition: {result.get('top_matches', [{}])[0].get('name', 'Inconnu')}")
        print(f"📉 Score de confiance   : {format_bar(result['confidence'])}")
        print(f"ℹ️  Explication         : {result['explanation']}")

    print("=" * 62 + "\n")


if __name__ == "__main__":
    main()
