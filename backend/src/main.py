import os
import sys
from pathlib import Path

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Résolution automatique des chemins racine et ai-engine
ROOT_DIR = Path(__file__).resolve().parents[2]
AI_ENGINE_DIR = ROOT_DIR / "ai-engine" / "src"

for p in (ROOT_DIR, AI_ENGINE_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from alternia.config.settings import PROJECT_ROOT, settings
from backend.src.db.database import init_db
from backend.src.services.orchestrator_service import get_orchestrator, normalize_student_class
from backend.src.routes import (
    alertes_router,
    apprenants_router,
    auth_router,
    avatars_router,
    boitiers_router,
    chat_router,
    device_router,
    insights_router,
    parent_router,
    rapports_router,
    revision_router,
    vocal_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise la base de données alta_db et précharge les moteurs au démarrage."""
    try:
        init_db()
    except Exception as e:
        print(f"[DB Init Warning] {e}")
    try:
        get_orchestrator()
    except Exception as e:
        print(f"[Startup Warning] Le préchargement immédiat a échoué: {e}")
    yield


app = FastAPI(
    title="AlternIA Backend API",
    description="API pédagogique intelligente connectant les dispositifs physiques et le portail Alta.",
    version="1.0.0",
    lifespan=lifespan,
)

# Activation CORS totale pour l'application Flutter et le portail Web Alta
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def disable_cache_for_kiosk(request, call_next):
    """Désactive le cache navigateur pour l'interface de développement Kiosk."""
    response = await call_next(request)
    if request.url.path.startswith(("/device", "/app", "/kiosk")):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Inclusion des routeurs modulaires
app.include_router(device_router)
app.include_router(chat_router)
app.include_router(auth_router)
app.include_router(boitiers_router)
app.include_router(apprenants_router)
app.include_router(avatars_router)
app.include_router(vocal_router)
app.include_router(alertes_router)
app.include_router(insights_router)
app.include_router(parent_router)
app.include_router(rapports_router)
app.include_router(revision_router)

# ==============================================================================
# HÉBERGEMENT DES INTERFACES WEB : DEVICE (KIOSK BOÎTIER) & ALTA (PORTAIL ANGULAR)
# ==============================================================================

ALTA_BROWSER_DIR = PROJECT_ROOT / "alta" / "dist" / "alternia" / "browser"
DEVICE_FRONTEND_DIR = PROJECT_ROOT / "device" / "frontend"

if DEVICE_FRONTEND_DIR.exists():
    # Montage de l'interface Kiosk du boîtier tactile pour les élèves
    app.mount("/device", StaticFiles(directory=str(DEVICE_FRONTEND_DIR), html=True), name="device_kiosk")
    app.mount("/app", StaticFiles(directory=str(DEVICE_FRONTEND_DIR), html=True), name="device_app")
    app.mount("/kiosk", StaticFiles(directory=str(DEVICE_FRONTEND_DIR), html=True), name="device_kiosk_alias")

    @app.get("/device")
    @app.get("/app")
    @app.get("/kiosk")
    async def redirect_to_device():
        """Redirige /device ou /app vers /device/ pour que les modules ES6 relatifs se chargent."""
        return RedirectResponse(url="/device/", status_code=307)


@app.get("/")
async def root_redirect():
    """Redirection par défaut à la racine : portail Alta ou interface Kiosk élève."""
    if (ALTA_BROWSER_DIR / "index.html").exists():
        return RedirectResponse(url="/etablissement/tableau-de-bord", status_code=307)
    elif (DEVICE_FRONTEND_DIR / "index.html").exists():
        return RedirectResponse(url="/device/", status_code=307)
    return {"application": "AlternIA", "status": "running"}


if ALTA_BROWSER_DIR.exists():
    @app.get("/{file_path:path}")
    async def serve_alta_spa(file_path: str):
        # Ne pas intercepter les routes API, Device ou Health
        if (
            file_path.startswith("api/")
            or file_path.startswith("device")
            or file_path.startswith("app")
            or file_path.startswith("kiosk")
            or file_path.startswith("ws/")
            or file_path == "health"
        ):
            raise HTTPException(status_code=404, detail="Route not found")

        # Fichier statique existant dans le bundle Angular (JS, CSS, SVGs, etc.)
        target_file = ALTA_BROWSER_DIR / file_path
        if file_path and target_file.is_file():
            return FileResponse(str(target_file))

        # Redirection HTML5 client-side pour Angular (/etablissement/*, /parent/*, /auth/*)
        index_file = ALTA_BROWSER_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))

        raise HTTPException(status_code=404, detail="File not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.src.main:app", host=settings.backend_host, port=settings.backend_port, reload=True)
