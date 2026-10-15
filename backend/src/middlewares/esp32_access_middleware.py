"""
══════════════════════════════════════════════════════════════════════════════
MIDDLEWARE DE CONTRÔLE D'ACCÈS EXCLUSIF : device.alterniamali.com
══════════════════════════════════════════════════════════════════════════════

Ce middleware garantit la règle matérielle stricte :
« Avoir accès à la page device.alterniamali.com uniquement une fois connecté
  au point d'accès Wi-Fi de notre ESP32 connecté au serveur Runpod. »

Fonctionnement :
1. Vérifie si le boîtier ESP32 physique est connecté en WebSocket (/ws/esp32).
2. Vérifie si le navigateur de l'élève présente le jeton de sécurité délivré par le SoftAP ESP32
   (cookie 'alternia_box_session' ou paramètre d'URL '?token=...' ou '?device_auth=...').
3. Si le client n'est pas connecté au Wi-Fi « AlterniA-Box-Mali » du boîtier :
   Affiche un écran de verrouillage explicite et sécurisé.
"""

from typing import Callable
from fastapi import Request, Response
from fastapi.responses import HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Jeton secret configuré sur l'ESP32 (config.h : DEVICE_AUTH_TOKEN)
VALID_DEVICE_TOKEN = "ALT-ESP32-TOKEN-MALI-8899"


class ESP32AccessControlMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, esp32_manager):
        super().__init__(app)
        self.manager = esp32_manager

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        raw_host = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
        host = raw_host.split(":")[0].strip().lower()
        path = request.url.path

        # Détecter si la requête cible l'interface élève Kiosk
        is_device_subdomain = (
            host == "device.alterniamali.com"
            or host.startswith("device.")
        )
        is_device_path = (
            path == "/device"
            or path.startswith("/device/")
            or path == "/kiosk"
            or path.startswith("/kiosk/")
        )

        is_device_request = is_device_subdomain or is_device_path

        # Autoriser en permanence les assets statiques, scripts, styles, API et WebSocket
        is_asset_or_api = (
            path.startswith("/api/")
            or path.startswith("/ws/")
            or path.startswith("/assets/")
            or path.endswith((".js", ".css", ".svg", ".png", ".jpg", ".jpeg", ".ico", ".woff", ".woff2", ".ttf", ".json"))
        )

        if is_device_request and not is_asset_or_api:
            # 1. Vérification : L'ESP32 est-il connecté au serveur Runpod ?
            esp32_online = (len(self.manager.esp32_sockets) > 0) or bool(self.manager.last_telemetry.get("connected", False))

            # 2. Vérification : Le client présente-t-il le jeton du Point d'Accès ESP32 ?
            token_query = request.query_params.get("token") or request.query_params.get("device_auth")
            token_cookie = request.cookies.get("alternia_box_session")
            has_valid_token = (token_query == VALID_DEVICE_TOKEN) or (token_cookie == VALID_DEVICE_TOKEN)

            # Option de développement local (ex: http://localhost:8000/device/?dev=1)
            is_local_dev = (
                request.client
                and request.client.host in ("127.0.0.1", "localhost", "::1")
                and request.query_params.get("dev") == "1"
            )

            if (esp32_online and has_valid_token) or is_local_dev:
                response = await call_next(request)
                # Persister le cookie si le token a été validé par paramètre d'URL
                if token_query == VALID_DEVICE_TOKEN:
                    response.set_cookie(
                        key="alternia_box_session",
                        value=VALID_DEVICE_TOKEN,
                        max_age=86400,
                        httponly=False,
                        samesite="lax",
                    )
                return response

            # Si non autorisé, afficher l'écran de restriction pédagogique
            return HTMLResponse(
                content=self._render_lock_screen(esp32_online=esp32_online),
                status_code=403,
            )

        return await call_next(request)

    def _render_lock_screen(self, esp32_online: bool) -> str:
        status_badge = (
            "<span style='color:#4ade80;background:rgba(34,197,94,0.15);padding:6px 14px;border-radius:999px;font-weight:700;'>Boîtier Connecté au Serveur ✅</span>"
            if esp32_online
            else "<span style='color:#f87171;background:rgba(239,68,68,0.15);padding:6px 14px;border-radius:999px;font-weight:700;'>Boîtier ESP32 Hors Ligne ❌</span>"
        )

        return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Accès Réservé - Boîtier AlterniA Mali</title>
    <style>
        :root {{ --p:#314999; --s:#40BBCC; --bg:#0D1525; --card:#141B2D; }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, -apple-system, sans-serif; }}
        body {{ background: var(--bg); color: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 20px; }}
        .card {{ background: var(--card); border: 1px solid rgba(255,255,255,0.1); border-radius: 28px; max-width: 480px; width: 100%; padding: 40px 32px; text-align: center; box-shadow: 0 25px 50px rgba(0,0,0,0.6); }}
        .icon-box {{ width: 80px; height: 80px; margin: 0 auto 20px; background: rgba(241,133,31,0.15); border: 1px solid rgba(241,133,31,0.3); border-radius: 24px; display: flex; align-items: center; justify-content: center; font-size: 36px; }}
        h1 {{ font-size: 22px; font-weight: 800; margin-bottom: 12px; }}
        p.desc {{ color: #94a3b8; font-size: 14.5px; line-height: 1.6; margin-bottom: 24px; }}
        .steps-box {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 20px; padding: 20px; text-align: left; margin-bottom: 28px; font-size: 13.5px; color: #cbd5e1; }}
        .step-row {{ display: flex; gap: 12px; margin-bottom: 14px; align-items: flex-start; }}
        .step-row:last-child {{ margin-bottom: 0; }}
        .step-num {{ background: var(--p); color: #fff; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 800; flex-shrink: 0; }}
        .btn-retry {{ display: block; width: 100%; padding: 14px; background: linear-gradient(135deg, var(--p), #0284c7); color: #fff; text-decoration: none; border-radius: 16px; font-weight: 700; font-size: 15px; border: none; cursor: pointer; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="icon-box">🔒</div>
        <h1>Accès Réservé au Point d'Accès AlterniA</h1>
        <div style="margin-bottom: 20px;">{status_badge}</div>
        <p class="desc">
            Pour accéder à l'interface <strong>device.alterniamali.com</strong>,
            vous devez être connecté au réseau Wi-Fi local de notre boîtier intelligent.
        </p>

        <div class="steps-box">
            <div class="step-row">
                <div class="step-num">1</div>
                <div>Activez le Wi-Fi sur votre téléphone, tablette ou ordinateur.</div>
            </div>
            <div class="step-row">
                <div class="step-num">2</div>
                <div>Connectez-vous au réseau Wi-Fi : <strong>AlterniA-Box-Mali</strong>.</div>
            </div>
            <div class="step-row">
                <div class="step-num">3</div>
                <div>Le portail captif du boîtier vous redirigera automatiquement ici avec votre jeton de session.</div>
            </div>
        </div>

        <button class="btn-retry" onclick="window.location.reload()">Recharger la page ➔</button>
    </div>
</body>
</html>"""
