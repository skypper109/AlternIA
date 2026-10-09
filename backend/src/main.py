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
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
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
    esp32_router,
    culture_router,
    duel_router,
    podcast_router,
)



from backend.src.routes.esp32_routes import manager as esp32_manager
from backend.src.middlewares.esp32_access_middleware import ESP32AccessControlMiddleware


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

# Activation CORS complète et conforme pour le mobile Flutter, Alta et Device Kiosk
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://alterniamali.com",
        "https://admin.alterniamali.com",
        "https://device.alterniamali.com",
        "https://api.alterniamali.com",
        "http://localhost",
        "http://localhost:8000",
        "http://localhost:4200",
        "http://localhost:5173",
        "http://127.0.0.1:8000",
        "*",
    ],
    allow_origin_regex=r"^https?://.*(alterniamali\.com|trycloudflare\.com|localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Contrôle d'accès exclusif : device.alterniamali.com n'est accessible que connecté au Point d'Accès ESP32
app.add_middleware(ESP32AccessControlMiddleware, esp32_manager=esp32_manager)


@app.middleware("http")
async def disable_cache_for_kiosk(request: Request, call_next):
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
app.include_router(esp32_router)
app.include_router(culture_router)
app.include_router(duel_router)
app.include_router(podcast_router)



# ==============================================================================
# HÉBERGEMENT DES INTERFACES WEB : DEVICE (KIOSK BOÎTIER) & ALTA (PORTAIL ANGULAR)
# ROUTAGE INTELLIGENT PAR SOUS-DOMAINE (LWS / CLOUDFLARE) :
# - admin.alterniamali.com  -> Backoffice Alta
# - device.alterniamali.com -> Interface tactile/vocale Kiosk
# - api.alterniamali.com    -> Endpoints API & Mobile Sync
# ==============================================================================

ALTA_BROWSER_DIR = PROJECT_ROOT / "alta" / "dist" / "alternia" / "browser"
DEVICE_FRONTEND_DIR = PROJECT_ROOT / "device" / "frontend" / "dist"


def get_request_host(request: Request) -> str:
    """Extrait l'hôte sans port depuis X-Forwarded-Host (Cloudflare/Proxy) ou Host."""
    raw = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
    return raw.split(":")[0].strip().lower()


def is_device_subdomain(host: str) -> bool:
    """Détecte les requêtes destinées à l'interface élève (device.alterniamali.com)."""
    return host.startswith("device.") or host == "device.alterniamali.com"


def is_admin_subdomain(host: str) -> bool:
    """Détecte les requêtes destinées au backoffice admin Alta (admin.alterniamali.com)."""
    return host.startswith("admin.") or host == "admin.alterniamali.com"


def is_api_subdomain(host: str) -> bool:
    """Détecte les requêtes dédiées à l'API / Mobile (api.alterniamali.com)."""
    return host.startswith("api.") or host == "api.alterniamali.com"


if DEVICE_FRONTEND_DIR.exists():
    # Montage statique standard pour /device (rétrocompatibilité locale et chemins absolus)
    app.mount("/device", StaticFiles(directory=str(DEVICE_FRONTEND_DIR), html=True), name="device_kiosk")
    app.mount("/app", StaticFiles(directory=str(DEVICE_FRONTEND_DIR), html=True), name="device_app")
    app.mount("/kiosk", StaticFiles(directory=str(DEVICE_FRONTEND_DIR), html=True), name="device_kiosk_alias")

    @app.get("/device")
    @app.get("/app")
    @app.get("/kiosk")
    async def redirect_to_device():
        """Redirige /device vers /device/ pour assurer la résolution des modules ES6 relatifs."""
        return RedirectResponse(url="/device/", status_code=307)

    @app.get("/esp32")
    async def redirect_to_esp32_dashboard():
        """Accès direct au tableau de bord ESP32."""
        return RedirectResponse(url="/api/esp32/dashboard", status_code=307)



@app.get("/")
async def root_router(request: Request):
    """
    Routage dynamique intelligent à la racine selon le nom de sous-domaine reçu :
    - device.alterniamali.com -> Interface tactile/vocale Kiosk élève
    - admin.alterniamali.com  -> Backoffice d'administration Alta
    - api.alterniamali.com    -> Statut API et annuaire des points d'accès
    - alterniamali.com / IP   -> Redirection par défaut vers Alta ou Kiosk
    """
    host = get_request_host(request)

    # 1. Sous-domaine Kiosk Élève : device.alterniamali.com
    if is_device_subdomain(host):
        device_index = DEVICE_FRONTEND_DIR / "index.html"
        if device_index.exists():
            return FileResponse(str(device_index))
        return {"service": "AlternIA Device Kiosk", "status": "running"}

    # 2. Sous-domaine Backoffice Admin : admin.alterniamali.com
    if is_admin_subdomain(host):
        if (ALTA_BROWSER_DIR / "index.html").exists():
            return RedirectResponse(url="/etablissement/tableau-de-bord", status_code=307)
        return {"service": "AlternIA Admin Backoffice", "status": "running"}

    # 3. Sous-domaine API & Sync Mobile : api.alterniamali.com
    if is_api_subdomain(host):
        return JSONResponse({
            "application": "AlternIA Cloud API",
            "version": "2.0.0",
            "status": "online",
            "domain": "alterniamali.com",
            "endpoints": {
                "api": "https://api.alterniamali.com",
                "admin_backoffice": "https://admin.alterniamali.com",
                "device_kiosk": "https://device.alterniamali.com",
                "docs": "https://api.alterniamali.com/docs",
                "health": "https://api.alterniamali.com/health",
                "mobile_ping": "https://api.alterniamali.com/api/info"
            }
        })

    # 4. Domaine par défaut (alterniamali.com, localhost:8000, 127.0.0.1)
    if (ALTA_BROWSER_DIR / "index.html").exists():
        return RedirectResponse(url="/etablissement/tableau-de-bord", status_code=307)
    elif (DEVICE_FRONTEND_DIR / "index.html").exists():
        return RedirectResponse(url="/device/", status_code=307)
    return {"application": "AlternIA", "status": "running"}


API_PATH_PREFIXES = (
    "api/",
    "ws/",
    "docs",
    "openapi.json",
    "redoc",
    "chat/",
    "vocal/",
    "auth/",
    "boitiers/",
    "apprenants/",
    "avatars/",
    "alertes/",
    "insights/",
    "parent/",
    "rapports/",
    "revision/",
)


@app.get("/{file_path:path}")
async def serve_subdomain_spa_or_assets(request: Request, file_path: str):
    """
    Sert les applications Single Page (SPA) et fichiers statiques selon le sous-domaine :
    - device.alterniamali.com sert les assets et l'index du Kiosk Élève
    - admin.alterniamali.com sert les chunks et pages du portail Alta
    - Les routes d'API ne sont pas interceptées
    """
    if file_path.startswith(API_PATH_PREFIXES) or file_path in ("health", "favicon.ico"):
        raise HTTPException(status_code=404, detail="Route API non trouvée")

    host = get_request_host(request)

    # ── A. SOUS-DOMAINE DEVICE (device.alterniamali.com) ────────────────────
    if is_device_subdomain(host):
        cleaned_path = file_path[len("device/"):].lstrip("/") if file_path.startswith("device/") else file_path
        target = DEVICE_FRONTEND_DIR / cleaned_path
        if cleaned_path and target.is_file():
            return FileResponse(str(target))
        idx = DEVICE_FRONTEND_DIR / "index.html"
        if idx.exists():
            return FileResponse(str(idx))
        raise HTTPException(status_code=404, detail="Interface Kiosk boîtier introuvable")

    # ── B. SOUS-DOMAINE ADMIN (admin.alterniamali.com) ───────────────────────
    if is_admin_subdomain(host):
        target = ALTA_BROWSER_DIR / file_path
        if file_path and target.is_file():
            return FileResponse(str(target))
        idx = ALTA_BROWSER_DIR / "index.html"
        if idx.exists():
            return FileResponse(str(idx))
        raise HTTPException(status_code=404, detail="Portail Admin Alta introuvable")

    # ── C. SOUS-DOMAINE API (api.alterniamali.com) ──────────────────────────
    if is_api_subdomain(host):
        if file_path in ("device", "device/"):
            return RedirectResponse(url="https://device.alterniamali.com/", status_code=307)
        if file_path in ("admin", "admin/"):
            return RedirectResponse(url="https://admin.alterniamali.com/", status_code=307)
        raise HTTPException(status_code=404, detail="Endpoint API inconnu")

    # ── D. CHEMIN EXPLICITE /device (N'IMPORTE QUEL HÔTE) ────────────────────
    if file_path.startswith("device/") or file_path == "device":
        sub = file_path[len("device/"):].lstrip("/") if file_path.startswith("device/") else ""
        target = DEVICE_FRONTEND_DIR / sub
        if sub and target.is_file():
            return FileResponse(str(target))
        idx = DEVICE_FRONTEND_DIR / "index.html"
        if idx.exists():
            return FileResponse(str(idx))

    # ── E. PORTAIL ALTA PAR DÉFAUT (DOMAINE RACINE OU LOCALHOST) ─────────────
    if ALTA_BROWSER_DIR.exists():
        target = ALTA_BROWSER_DIR / file_path
        if file_path and target.is_file():
            return FileResponse(str(target))
        idx = ALTA_BROWSER_DIR / "index.html"
        if idx.exists():
            return FileResponse(str(idx))

    # ── F. FALLBACK DEVICE SI ALTA ABSENT ────────────────────────────────────
    if DEVICE_FRONTEND_DIR.exists():
        target = DEVICE_FRONTEND_DIR / file_path
        if file_path and target.is_file():
            return FileResponse(str(target))
        idx = DEVICE_FRONTEND_DIR / "index.html"
        if idx.exists():
            return FileResponse(str(idx))

    raise HTTPException(status_code=404, detail="Page introuvable")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.src.main:app", host=settings.backend_host, port=settings.backend_port, reload=True)
