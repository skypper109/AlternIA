#!/usr/bin/env python3
"""
Script utilitaire pour initialiser et peupler la base de données alta_db.
Usage :
  python scripts/seed_db.py
"""

import sys
from pathlib import Path

# Définition de la racine du projet
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.src.db.database import init_db, SessionLocal
from backend.src.db.seed import seed_initial_data

if __name__ == "__main__":
    print("🌱 Initialisation des tables alta_db...")
    init_db()
    db = SessionLocal()
    try:
        seed_initial_data(db)
    finally:
        db.close()
    print("✨ Opération terminée avec succès.")
