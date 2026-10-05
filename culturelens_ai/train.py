#!/usr/bin/env python3
"""Script CLI d'entraînement et de ré-indexation du modèle CultureLens."""

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
    from culturelens_ai.src.trainer import train_and_index_monuments
except ImportError:
    try:
        from src.trainer import train_and_index_monuments
    except ImportError:
        from .src.trainer import train_and_index_monuments


def main():
    parser = argparse.ArgumentParser(
        description="Entraîne le modèle CultureLens AI sur les monuments de Bamako et du Mali."
    )
    parser.add_argument(
        "--augmentations",
        type=int,
        default=20,
        help="Nombre de variations augmentées à générer par image de référence (défaut : 20)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="Device d'exécution : 'cpu', 'mps' (Mac M1/M2/M3), ou 'cuda'",
    )

    args = parser.parse_args()

    try:
        results = train_and_index_monuments(
            num_augmentations=args.augmentations,
            device=args.device,
        )
        print(f"\n🎉 Entraînement terminé avec succès : {results['num_monuments']} monuments indexés !")
        print(f"Pour tester une image, lancez : python infer.py dataset/test_images/test_independance.jpg")
    except Exception as e:
        print(f"\n❌ Erreur pendant l'entraînement : {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
