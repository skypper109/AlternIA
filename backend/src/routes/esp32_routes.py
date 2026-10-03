"""
Routes et WebSocket pour la connexion et la synchronisation temps réel de l'ESP32 avec AlternIA.
Gère :
- La connexion persistante WebSocket /ws/esp32
- Le pilotage des LEDs d'état (Vert = Connecté, Blanc = Classe sélectionnée + Micro prêt, etc.)
- La détection et le streaming audio du microphone
- L'API REST de pilotage et de télémétrie
- La synchronisation avec le Kiosk et le portail Alta
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Set
from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger("alternia.esp32")

router = APIRouter(tags=["ESP32 IoT & Matériel"])


# ==============================================================================
# MODÈLES DE DONNÉES
# ==============================================================================

class ESP32StateRequest(BaseModel):
    state: str = Field(..., description="État : CONNECTED, CLASS_SELECTED, LISTENING, THINKING, SPEAKING, IDLE, DISCONNECTED")
    selected_class: Optional[str] = Field(None, description="Ex: 10eme, 11eme, TSE")
    mic_plugged: Optional[bool] = Field(None, description="True si le micro est branché/actif")
    led_color: Optional[str] = Field(None, description="GREEN, WHITE, BLUE, RED, OFF")
    message: Optional[str] = Field(None, description="Message informatif pour l'ESP32")


class ESP32Telemetry(BaseModel):
    device_id: str = "ESP32-ALT-01"
    ip: Optional[str] = None
    rssi: Optional[int] = None
    free_heap: Optional[int] = None
    battery_level: Optional[int] = 100
    mic_plugged: bool = False
    selected_class: Optional[str] = None
    state: str = "DISCONNECTED"
    led: str = "OFF"
    last_seen: float = 0.0


# ==============================================================================
# GESTIONNAIRE CENTRALISÉ DES CONNEXIONS ESP32 (SINGLETON)
# ==============================================================================

class ESP32ConnectionManager:
    """Gère le pool de connexions WebSocket ESP32 et les tableaux de bord abonnés."""

    def __init__(self):
        self.esp32_sockets: Set[WebSocket] = set()
        self.dashboard_sockets: Set[WebSocket] = set()
        self.current_state: str = "DISCONNECTED"
        self.selected_class: Optional[str] = "10eme"
        self.mic_plugged: bool = True  # Par défaut actif pour la simulation
        self.current_led: str = "OFF"
        self.last_telemetry: Dict[str, Any] = {
            "device_id": "ESP32-ALT-01",
            "connected": False,
            "ip": None,
            "rssi": None,
            "free_heap": None,
            "battery_level": 95,
            "mic_plugged": True,
            "selected_class": "10eme",
            "state": "DISCONNECTED",
            "led": "OFF",
            "last_seen": 0,
        }

    async def connect_esp32(self, websocket: WebSocket, client_info: Dict[str, Any]):
        """Enregistre une nouvelle connexion physique ESP32."""
        await websocket.accept()
        self.esp32_sockets.add(websocket)
        self.current_state = "CONNECTED"
        self.current_led = "GREEN"  # Dès la connexion, LED Verte !
        self.last_telemetry.update({
            "connected": True,
            "device_id": client_info.get("device_id", "ESP32-ALT-01"),
            "ip": client_info.get("ip", "192.168.100.x"),
            "state": self.current_state,
            "led": self.current_led,
            "last_seen": time.time(),
        })

        # Notifier l'ESP32 : LED Verte immédiate
        await self.send_to_esp32({
            "type": "command",
            "command": "set_state",
            "state": "CONNECTED",
            "led": "GREEN",
            "selected_class": self.selected_class,
            "mic_plugged": self.mic_plugged,
            "message": "Bienvenue sur le serveur distant AlternIA",
        })

        # Notifier les dashboards
        await self.broadcast_to_dashboards({
            "event": "esp32_connected",
            "data": self.last_telemetry,
        })
        logger.info(f"ESP32 connecté avec succès : {client_info}")

    def disconnect_esp32(self, websocket: WebSocket):
        """Retire l'ESP32 déconnecté."""
        if websocket in self.esp32_sockets:
            self.esp32_sockets.remove(websocket)
        if not self.esp32_sockets:
            self.current_state = "DISCONNECTED"
            self.current_led = "OFF"
            self.last_telemetry["connected"] = False
            self.last_telemetry["state"] = "DISCONNECTED"
            self.last_telemetry["led"] = "OFF"

    async def connect_dashboard(self, websocket: WebSocket):
        """Enregistre un tableau de bord web d'observation."""
        await websocket.accept()
        self.dashboard_sockets.add(websocket)
        # Envoyer l'état actuel immédiatement
        await websocket.send_text(json.dumps({
            "event": "initial_state",
            "data": self.last_telemetry,
        }))

    def disconnect_dashboard(self, websocket: WebSocket):
        if websocket in self.dashboard_sockets:
            self.dashboard_sockets.remove(websocket)

    async def send_to_esp32(self, payload: Dict[str, Any]):
        """Envoie un message JSON à tous les ESP32 connectés."""
        if not self.esp32_sockets:
            return
        msg = json.dumps(payload)
        dead = []
        for ws in self.esp32_sockets:
            try:
                await ws.send_text(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect_esp32(ws)

    async def broadcast_to_dashboards(self, payload: Dict[str, Any]):
        """Diffuse un événement à tous les tableaux de bord connectés."""
        if not self.dashboard_sockets:
            return
        msg = json.dumps(payload)
        dead = []
        for ws in self.dashboard_sockets:
            try:
                await ws.send_text(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect_dashboard(ws)

    async def update_state(
        self,
        new_state: Optional[str] = None,
        selected_class: Optional[str] = None,
        mic_plugged: Optional[bool] = None,
        led_color: Optional[str] = None,
        message: Optional[str] = None,
    ):
        """Met à jour l'état logique et synchronise l'ESP32 et les tableaux de bord."""
        if selected_class is not None:
            self.selected_class = selected_class
            self.last_telemetry["selected_class"] = selected_class

        if mic_plugged is not None:
            self.mic_plugged = mic_plugged
            self.last_telemetry["mic_plugged"] = mic_plugged

        if new_state:
            self.current_state = new_state
            self.last_telemetry["state"] = new_state

        # Détermination automatique de la couleur de LED si non explicitement fournie
        # RÈGLE DU PROJET :
        # - Connecté seul : VERT
        # - Micro branché ET Classe sélectionnée : BLANC
        # - Thinking (RAG/LLM) : BLUE
        # - Speaking (Voix) : YELLOW / PULSE
        if led_color:
            self.current_led = led_color
        else:
            if not self.esp32_sockets and self.current_state == "DISCONNECTED":
                self.current_led = "OFF"
            elif self.current_state in ("THINKING", "PROCESSING"):
                self.current_led = "BLUE"
            elif self.current_state == "SPEAKING":
                self.current_led = "PULSE"
            elif self.mic_plugged and self.selected_class:
                # CLASSE SÉLECTIONNÉE + MICRO BRANCHÉ -> BLANC
                self.current_led = "WHITE"
            elif self.esp32_sockets or self.current_state == "CONNECTED":
                # CONNECTÉ AU SERVEUR -> VERT
                self.current_led = "GREEN"
            else:
                self.current_led = "OFF"

        self.last_telemetry["led"] = self.current_led
        self.last_telemetry["last_seen"] = time.time()

        # Envoi à l'ESP32
        payload = {
            "type": "command",
            "command": "set_state",
            "state": self.current_state,
            "led": self.current_led,
            "selected_class": self.selected_class,
            "mic_plugged": self.mic_plugged,
            "message": message or f"État : {self.current_state} (LED: {self.current_led})",
        }
        await self.send_to_esp32(payload)

        # Envoi au dashboard
        await self.broadcast_to_dashboards({
            "event": "state_changed",
            "data": self.last_telemetry,
        })


manager = ESP32ConnectionManager()


# ==============================================================================
# WEBSOCKET PRINCIPAL : /ws/esp32
# ==============================================================================

@router.websocket("/ws/esp32")
async def websocket_esp32_endpoint(websocket: WebSocket):
    """
    WebSocket duplex temps réel pour le microcontrôleur ESP32 :
    - Dès la connexion : Réception de l'ordre d'allumer la LED Verte (PIN 27).
    - Lors de la sélection d'une classe et micro actif : Passage immédiat en Blanc.
    - Échanges de ping/pong de maintien de liaison.
    - Écoute des événements boutons / audio envoyés par l'ESP32.
    """
    client_info = {
        "device_id": websocket.query_params.get("device_id", "ESP32-ALT-01"),
        "ip": websocket.client.host if websocket.client else "unknown",
        "connected_at": time.time(),
    }

    await manager.connect_esp32(websocket, client_info)

    try:
        while True:
            raw_text = await websocket.receive_text()
            try:
                data = json.loads(raw_text)
            except Exception:
                data = {"type": "raw", "text": raw_text}

            msg_type = data.get("type", "")

            # 1. Ping / Heartbeat
            if msg_type in ("ping", "heartbeat"):
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": time.time(),
                    "state": manager.current_state,
                    "led": manager.current_led,
                }))
                manager.last_telemetry["last_seen"] = time.time()

            # 2. Télémétrie périodique de l'ESP32
            elif msg_type == "telemetry":
                manager.last_telemetry.update({
                    "rssi": data.get("rssi"),
                    "free_heap": data.get("free_heap"),
                    "battery_level": data.get("battery", 95),
                    "mic_plugged": data.get("mic_plugged", manager.mic_plugged),
                    "last_seen": time.time(),
                })
                # Re-vérifier l'état de la LED
                if data.get("mic_plugged") is not None:
                    await manager.update_state(mic_plugged=bool(data.get("mic_plugged")))
                await manager.broadcast_to_dashboards({
                    "event": "telemetry",
                    "data": manager.last_telemetry,
                })

            # 3. Notification d'état du Micro
            elif msg_type == "mic_status":
                plugged = bool(data.get("plugged", True))
                await manager.update_state(mic_plugged=plugged)

            # 4. Détection du bouton physique (ex: Bouton BOOT GPIO 0 ou Push-To-Talk)
            elif msg_type == "button_press":
                btn = data.get("button", "ptt")
                # Si l'utilisateur appuie pour parler
                if btn in ("ptt", "boot", "mic"):
                    await manager.update_state(new_state="LISTENING", led_color="WHITE")
                    await manager.broadcast_to_dashboards({
                        "event": "button_pressed",
                        "button": btn,
                        "message": "Élève a appuyé sur le bouton microphone",
                    })

            # 5. Déclenchement de question vocale / audio
            elif msg_type == "voice_query":
                question = data.get("text", "Bonjour AlternIA")
                await manager.update_state(new_state="THINKING", led_color="BLUE")
                await asyncio.sleep(1.0)  # Simulation réponse IA
                await manager.update_state(new_state="SPEAKING", led_color="PULSE")
                await asyncio.sleep(2.0)
                # Retour à blanc (si classe et micro) ou vert
                await manager.update_state(new_state="IDLE")

    except WebSocketDisconnect:
        manager.disconnect_esp32(websocket)
        logger.info("ESP32 déconnecté")
        await manager.broadcast_to_dashboards({
            "event": "esp32_disconnected",
            "message": "ESP32 déconnecté",
        })
    except Exception as e:
        manager.disconnect_esp32(websocket)
        logger.error(f"Erreur WebSocket ESP32 : {e}")


# ==============================================================================
# WEBSOCKET DASHBOARD / SIMULATEUR : /ws/esp32/dashboard
# ==============================================================================

@router.websocket("/ws/esp32/dashboard")
async def websocket_dashboard_endpoint(websocket: WebSocket):
    """Permet aux pages web (Kiosk, dashboard de test) de recevoir en temps réel l'état de l'ESP32."""
    await manager.connect_dashboard(websocket)
    try:
        while True:
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_dashboard(websocket)


# ==============================================================================
# ENDPOINTS REST DE PILOTAGE ET SYNCHRONISATION
# ==============================================================================

@router.get("/api/esp32/status")
def get_esp32_status():
    """Retourne l'état complet du boîtier ESP32 connecté."""
    active_count = len(manager.esp32_sockets)
    return {
        "connected": active_count > 0 or manager.last_telemetry.get("connected", False),
        "active_clients": active_count,
        "state": manager.current_state,
        "led": manager.current_led,
        "selected_class": manager.selected_class,
        "mic_plugged": manager.mic_plugged,
        "telemetry": manager.last_telemetry,
        "pinout": {
            "green_led": 27,
            "white_led": 26,
            "red_led": 25,
            "boot_button": 0,
            "mic_pin": 34,
        }
    }


@router.post("/api/esp32/state")
async def set_esp32_state(req: ESP32StateRequest):
    """
    Change l'état de l'ESP32 depuis le serveur ou une interface externe.
    Gère la couleur de la LED (Vert, Blanc, Bleu, etc.) et propage l'ordre instantanément.
    """
    await manager.update_state(
        new_state=req.state,
        selected_class=req.selected_class,
        mic_plugged=req.mic_plugged,
        led_color=req.led_color,
        message=req.message,
    )
    return {
        "status": "success",
        "current_state": manager.current_state,
        "current_led": manager.current_led,
        "selected_class": manager.selected_class,
        "mic_plugged": manager.mic_plugged,
    }


@router.post("/api/esp32/select-class")
async def select_class_endpoint(
    classe: str = Query(..., description="10eme, 11eme, TSE, etc."),
    mic_connected: bool = Query(True, description="Indique si le micro est branché")
):
    """
    Appelé lors de la sélection d'une classe (depuis le Kiosk tactile ou le tableau de bord) :
    Si le micro est branché, la LED passe immédiatement en BLANC !
    """
    await manager.update_state(
        new_state="CLASS_SELECTED",
        selected_class=classe,
        mic_plugged=mic_connected,
    )
    return {
        "status": "success",
        "selected_class": manager.selected_class,
        "mic_plugged": manager.mic_plugged,
        "led": manager.current_led,
        "message": f"Classe {classe} sélectionnée. LED passée en {manager.current_led} !"
    }


@router.post("/api/esp32/toggle-mic")
async def toggle_mic_endpoint(plugged: bool = Query(..., description="État du micro")):
    """Simule ou notifie le branchement / débranchement du micro sur l'ESP32."""
    await manager.update_state(mic_plugged=plugged)
    return {
        "status": "success",
        "mic_plugged": manager.mic_plugged,
        "led": manager.current_led,
        "message": f"Micro {'branché' if plugged else 'débranché'}. LED : {manager.current_led}"
    }


@router.post("/api/esp32/simulate-press")
async def simulate_button_press(button: str = Query("boot", description="boot ou ptt")):
    """Simule l'appui sur le bouton BOOT (GPIO 0) de l'ESP32."""
    await manager.send_to_esp32({
        "type": "command",
        "command": "trigger_button",
        "button": button,
    })
    await manager.broadcast_to_dashboards({
        "event": "button_pressed",
        "button": button,
        "message": "Simulation : Appui sur le bouton BOOT déclenché !",
    })
    return {"status": "success", "button": button}


# ==============================================================================
# TABLEAU DE BORD DE TEST & SIMULATION WEB INTÉGRÉ
# Accessible sur : http://localhost:8000/api/esp32/dashboard
# ==============================================================================

@router.get("/api/esp32/dashboard", response_class=HTMLResponse)
def get_dashboard_html():
    """Interface interactive élégante pour visualiser et piloter la connexion ESP32 en direct."""
    html_content = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AlternIA ESP32 Live Bridge & Simulator</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #090d16;
      --card-bg: rgba(18, 24, 38, 0.75);
      --card-border: rgba(255, 255, 255, 0.08);
      --primary: #3b82f6;
      --accent: #10b981;
      --led-green: #22c55e;
      --led-white: #f8fafc;
      --led-blue: #38bdf8;
      --led-red: #ef4444;
      --text: #f1f5f9;
      --text-muted: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: radial-gradient(circle at 50% 0%, #172554 0%, var(--bg) 70%);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 2rem 1rem;
    }
    .container {
      width: 100%;
      max-width: 1000px;
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }
    header {
      text-align: center;
      margin-bottom: 0.5rem;
    }
    header h1 {
      font-size: 2.2rem;
      font-weight: 800;
      background: linear-gradient(135deg, #60a5fa, #34d399, #f8fafc);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 0.4rem;
    }
    header p {
      color: var(--text-muted);
      font-size: 0.95rem;
    }
    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.5rem;
    }
    @media (max-width: 768px) {
      .grid { grid-template-columns: 1fr; }
    }
    .card {
      background: var(--card-bg);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid var(--card-border);
      border-radius: 1.25rem;
      padding: 1.75rem;
      box-shadow: 0 20px 40px -15px rgba(0,0,0,0.5);
    }
    .card-title {
      font-size: 1.1rem;
      font-weight: 700;
      margin-bottom: 1.2rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    /* ESP32 Physical Layout Simulation */
    .esp-box {
      background: #0f172a;
      border: 2px solid #334155;
      border-radius: 1rem;
      padding: 1.5rem;
      position: relative;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 1.2rem;
      box-shadow: inset 0 2px 10px rgba(0,0,0,0.6);
    }
    .esp-badge {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.75rem;
      background: #1e293b;
      padding: 0.25rem 0.6rem;
      border-radius: 0.5rem;
      color: #94a3b8;
    }
    /* LED Visualizer */
    .led-cluster {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 2rem;
      padding: 1rem;
      width: 100%;
    }
    .led-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.8rem;
      color: var(--text-muted);
    }
    .led-bulb {
      width: 44px;
      height: 44px;
      border-radius: 50%;
      background: #1e293b;
      border: 3px solid #334155;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
    }
    .led-bulb.active-green {
      background: #22c55e;
      border-color: #86efac;
      box-shadow: 0 0 30px #22c55e, 0 0 60px rgba(34, 197, 94, 0.4);
    }
    .led-bulb.active-white {
      background: #ffffff;
      border-color: #f1f5f9;
      box-shadow: 0 0 35px #ffffff, 0 0 70px rgba(255, 255, 255, 0.6);
    }
    .led-bulb.active-blue {
      background: #38bdf8;
      border-color: #bae6fd;
      box-shadow: 0 0 30px #38bdf8, 0 0 60px rgba(56, 189, 248, 0.4);
    }
    .led-bulb.active-red {
      background: #ef4444;
      border-color: #fca5a5;
      box-shadow: 0 0 30px #ef4444, 0 0 60px rgba(239, 68, 68, 0.4);
    }
    .led-tag {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.75rem;
      font-weight: 600;
    }
    /* Interactive Controls */
    .btn-group {
      display: flex;
      flex-wrap: wrap;
      gap: 0.6rem;
    }
    button {
      font-family: inherit;
      font-size: 0.88rem;
      font-weight: 600;
      padding: 0.65rem 1.1rem;
      border-radius: 0.75rem;
      border: 1px solid rgba(255,255,255,0.12);
      background: #1e293b;
      color: #f8fafc;
      cursor: pointer;
      transition: all 0.2s;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
    }
    button:hover {
      background: #334155;
      border-color: rgba(255,255,255,0.25);
      transform: translateY(-1px);
    }
    button.primary {
      background: linear-gradient(135deg, #2563eb, #1d4ed8);
      border-color: #3b82f6;
    }
    button.primary:hover {
      background: linear-gradient(135deg, #1d4ed8, #1e40af);
      box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4);
    }
    button.success {
      background: linear-gradient(135deg, #059669, #047857);
      border-color: #10b981;
    }
    button.success:hover {
      background: linear-gradient(135deg, #047857, #065f46);
      box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
    }
    /* Status Pills */
    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.35rem 0.8rem;
      border-radius: 2rem;
      font-size: 0.8rem;
      font-weight: 700;
      background: rgba(255,255,255,0.06);
      margin-bottom: 0.5rem;
    }
    .status-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: #94a3b8;
    }
    .status-badge.online .status-dot {
      background: #22c55e;
      box-shadow: 0 0 10px #22c55e;
    }
    .status-badge.offline .status-dot {
      background: #ef4444;
    }
    /* Terminal Console */
    .terminal {
      background: #050811;
      border: 1px solid #1e293b;
      border-radius: 0.85rem;
      padding: 1rem;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.78rem;
      color: #94a3b8;
      max-height: 220px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
    }
    .terminal .log-line {
      display: flex;
      gap: 0.5rem;
      word-break: break-all;
    }
    .terminal .time { color: #475569; }
    .terminal .green { color: #4ade80; }
    .terminal .white { color: #f8fafc; font-weight: 600; }
    .terminal .blue { color: #38bdf8; }
    .terminal .yellow { color: #facc15; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>AlternIA ESP32 Live Hub</h1>
      <p>Supervision temps réel et simulation de la liaison matérielle ESP32 ↔ Serveur distant</p>
    </header>

    <div class="grid">
      <!-- Panneau Matériel Virtuel ESP32 -->
      <div class="card">
        <div class="card-title">
          <span>📟</span>
          <span>Boîtier Physique ESP32</span>
          <div style="margin-left: auto;">
            <div id="conn-badge" class="status-badge offline">
              <span class="status-dot"></span>
              <span id="conn-text">Déconnecté</span>
            </div>
          </div>
        </div>

        <div class="esp-box">
          <div class="esp-badge">ESP32 Feather / DevKit (GPIO 27, 26, 25, 0)</div>
          
          <div class="led-cluster">
            <div class="led-item">
              <div id="led-green-bulb" class="led-bulb"></div>
              <span class="led-tag">PIN 27</span>
              <span>VERT (Serveur OK)</span>
            </div>

            <div class="led-item">
              <div id="led-white-bulb" class="led-bulb"></div>
              <span class="led-tag">PIN 26</span>
              <span>BLANC (Classe+Micro)</span>
            </div>

            <div class="led-item">
              <div id="led-blue-bulb" class="led-bulb"></div>
              <span class="led-tag">PIN 33</span>
              <span>BLEU (IA Calcul)</span>
            </div>
          </div>

          <div style="font-size: 0.85rem; color: var(--text-muted); text-align: center;">
            État Actuel : <strong id="lbl-state" style="color: #60a5fa;">DISCONNECTED</strong> | 
            Classe : <strong id="lbl-class" style="color: #f8fafc;">10ème</strong> | 
            Micro : <strong id="lbl-mic" style="color: #34d399;">Branché</strong>
          </div>
        </div>

        <div style="margin-top: 1.2rem;">
          <label style="font-size: 0.85rem; font-weight: 600; color: var(--text-muted); display: block; margin-bottom: 0.5rem;">
            Simulation Matérielle Physique (Bouton BOOT GPIO 0) :
          </label>
          <button id="btn-boot" class="primary" style="width: 100%;">
            🔘 Simuler Appui sur Bouton BOOT (Parler au micro)
          </button>
        </div>
      </div>

      <!-- Panneau Commandes Serveur -->
      <div class="card">
        <div class="card-title">
          <span>🎮</span>
          <span>Scénarios & Pilotage Serveur</span>
        </div>

        <div style="display: flex; flex-direction: column; gap: 1rem;">
          <div>
            <label style="font-size: 0.85rem; font-weight: 600; color: var(--text-muted); display: block; margin-bottom: 0.4rem;">
              1. Tester Connexion Serveur (Actionne LED Verte) :
            </label>
            <div class="btn-group">
              <button class="success" onclick="sendState('CONNECTED', 'GREEN')">🟢 Forcer État Connecté (LED Verte)</button>
              <button onclick="sendState('DISCONNECTED', 'OFF')">🔴 Déconnecter (LED Éteinte)</button>
            </div>
          </div>

          <div>
            <label style="font-size: 0.85rem; font-weight: 600; color: var(--text-muted); display: block; margin-bottom: 0.4rem;">
              2. Sélectionner Classe (Actionne LED Blanche si micro actif) :
            </label>
            <div class="btn-group">
              <button onclick="selectClass('10eme')">🎓 10ème Année</button>
              <button onclick="selectClass('11eme')">🎓 11ème Année</button>
              <button onclick="selectClass('TSE')">🎓 Terminale TSE</button>
            </div>
          </div>

          <div>
            <label style="font-size: 0.85rem; font-weight: 600; color: var(--text-muted); display: block; margin-bottom: 0.4rem;">
              3. État du Microphone :
            </label>
            <div class="btn-group">
              <button onclick="toggleMicro(true)">🎤 Brancher Micro (Passe en Blanc)</button>
              <button onclick="toggleMicro(false)">❌ Débrancher Micro (Revient en Vert)</button>
            </div>
          </div>

          <div>
            <label style="font-size: 0.85rem; font-weight: 600; color: var(--text-muted); display: block; margin-bottom: 0.4rem;">
              4. Cycle d'Apprentissage IA :
            </label>
            <div class="btn-group">
              <button onclick="sendState('THINKING', 'BLUE')">🔵 IA Réfléchit (Bleu)</button>
              <button onclick="sendState('SPEAKING', 'PULSE')">🟣 IA Parle (Pulse)</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Journal des Événements WebSocket -->
    <div class="card">
      <div class="card-title">
        <span>📜</span>
        <span>Journal des Trames WebSocket & Télémétrie en Direct</span>
        <button style="margin-left: auto; padding: 0.3rem 0.6rem; font-size: 0.75rem;" onclick="document.getElementById('console-logs').innerHTML = '';">Effacer</button>
      </div>
      <div id="console-logs" class="terminal">
        <div class="log-line"><span class="time">[INIT]</span><span class="blue">Initialisation du tableau de bord AlternIA ESP32...</span></div>
      </div>
    </div>
  </div>

  <script>
    const logsEl = document.getElementById('console-logs');
    const ledGreen = document.getElementById('led-green-bulb');
    const ledWhite = document.getElementById('led-white-bulb');
    const ledBlue = document.getElementById('led-blue-bulb');
    const connBadge = document.getElementById('conn-badge');
    const connText = document.getElementById('conn-text');
    const lblState = document.getElementById('lbl-state');
    const lblClass = document.getElementById('lbl-class');
    const lblMic = document.getElementById('lbl-mic');

    function log(msg, colorClass = '') {
      const time = new Date().toLocaleTimeString();
      const div = document.createElement('div');
      div.className = 'log-line';
      div.innerHTML = `<span class="time">[${time}]</span> <span class="${colorClass}">${msg}</span>`;
      logsEl.appendChild(div);
      logsEl.scrollTop = logsEl.scrollHeight;
    }

    function updateLEDs(color) {
      ledGreen.className = 'led-bulb' + (color === 'GREEN' ? ' active-green' : '');
      ledWhite.className = 'led-bulb' + (color === 'WHITE' ? ' active-white' : '');
      ledBlue.className = 'led-bulb' + (color === 'BLUE' || color === 'PULSE' ? ' active-blue' : '');
    }

    function applyState(data) {
      if (!data) return;
      const connected = !!data.connected;
      connBadge.className = 'status-badge ' + (connected ? 'online' : 'offline');
      connText.textContent = connected ? 'Connecté (ESP32 Actif)' : 'En attente ESP32';
      
      lblState.textContent = data.state || 'DISCONNECTED';
      lblClass.textContent = data.selected_class || 'Non définie';
      lblMic.textContent = data.mic_plugged ? 'Branché / Prêt' : 'Débranché';

      updateLEDs(data.led);
    }

    // Connexion WebSocket
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${proto}//${window.location.host}/ws/esp32/dashboard`;
    let ws;

    function initWS() {
      ws = new WebSocket(wsUrl);
      ws.onopen = () => {
        log("✅ Connecté au flux WebSocket du serveur AlternIA", "green");
      };
      ws.onmessage = (evt) => {
        try {
          const payload = JSON.parse(evt.data);
          if (payload.event === 'initial_state' || payload.event === 'state_changed') {
            applyState(payload.data);
            log(`🔄 Synchronisation état: ${payload.data.state} | LED: ${payload.data.led}`, payload.data.led === 'WHITE' ? 'white' : 'green');
          } else if (payload.event === 'esp32_connected') {
            log("🟢 ESP32 physique s'est connecté au serveur ! LED Verte activée.", "green");
            applyState(payload.data);
          } else if (payload.event === 'button_pressed') {
            log(`🔘 ${payload.message}`, "yellow");
          }
        } catch(e) {
          log(evt.data);
        }
      };
      ws.onclose = () => {
        log("⚠️ Déconnecté du flux serveur. Reconnexion...", "yellow");
        setTimeout(initWS, 2000);
      };
    }
    initWS();

    // Commandes REST
    async function sendState(state, led) {
      log(`Envoi ordre état : ${state} (LED ${led})...`);
      await fetch('/api/esp32/state', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ state, led_color: led })
      });
    }

    async function selectClass(cls) {
      log(`Sélection de la classe ${cls}...`, "white");
      await fetch(`/api/esp32/select-class?classe=${cls}&mic_connected=true`, { method: 'POST' });
    }

    async function toggleMicro(plugged) {
      log(`Modification état micro : ${plugged ? 'Branché' : 'Débranché'}...`);
      await fetch(`/api/esp32/toggle-mic?plugged=${plugged}`, { method: 'POST' });
    }

    document.getElementById('btn-boot').onclick = async () => {
      log("Simulation appui bouton BOOT...", "yellow");
      await fetch('/api/esp32/simulate-press?button=boot', { method: 'POST' });
    };

    // Chargement initial du statut
    fetch('/api/esp32/status')
      .then(res => res.json())
      .then(data => {
        applyState(data);
      });
  </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)
