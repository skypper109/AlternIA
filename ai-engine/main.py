import sys
from pathlib import Path

# Assurer l'accès au code backend et ai-engine
ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend" / "src"
AI_ENGINE_SRC = ROOT_DIR / "ai-engine" / "src"

for p in [str(BACKEND_DIR), str(AI_ENGINE_SRC)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from main import app  # Réexporte l'application FastAPI complète

__all__ = ["app"]

