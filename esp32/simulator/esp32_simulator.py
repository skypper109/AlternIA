#!/usr/bin/env python3
"""
AlternIA - Simulateur Logiciel ESP32 & Console Matérielle
Permet de tester et simuler l'ESP32 avec le serveur distant AlternIA :
- Se connecte en WebSocket sur /ws/esp32
- Affiche l'état des LEDs virtuelles (🟢 VERT, ⚪ BLANC, 🔵 BLEU)
- Permet de simuler le bouton BOOT physique, la sélection de classe et le microphone
- Envoie la télémétrie comme un véritable microcontrôleur
"""

import argparse
import asyncio
import json
import os
import sys
import time

try:
    import websockets
except ImportError:
    print("Installation du module websockets...")
    os.system(f"{sys.executable} -m pip install websockets")
    import websockets


# Couleurs ANSI pour l'affichage console
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[1;32m"
WHITE = "\033[1;37m"
BLUE = "\033[1;34m"
RED = "\033[1;31m"
YELLOW = "\033[1;33m"
CYAN = "\033[1;36m"
MAGENTA = "\033[1;35m"


class ESP32Simulator:
    def __init__(self, server_url: str, device_id: str = "ESP32-SIM-01"):
        self.server_url = server_url
        self.device_id = device_id
        self.ws = None
        self.running = True
        self.current_state = "DISCONNECTED"
        self.current_led = "OFF"
        self.selected_class = "10eme"
        self.mic_plugged = True
        self.battery = 96

    def print_led_display(self):
        """Affiche graphiquement l'état des LEDs physiques de l'ESP32."""
        g_led = f"{GREEN}● VERT (PIN 27) [ON]{RESET}" if self.current_led == "GREEN" else f"{RED}○ VERT (PIN 27) [OFF]{RESET}"
        w_led = f"{WHITE}● BLANC (PIN 26) [ON]{RESET}" if self.current_led == "WHITE" else f"{YELLOW}○ BLANC (PIN 26) [OFF]{RESET}"
        b_led = f"{BLUE}● BLEU (PIN 33) [ON]{RESET}" if self.current_led in ("BLUE", "PULSE") else f"○ BLEU (PIN 33) [OFF]"

        print("\n" + "═" * 70)
        print(f"📟 {BOLD}ÉTAT PHYSIQUE ESP32 ({self.device_id}){RESET}")
        print(f"   Connexion : {GREEN if self.current_state != 'DISCONNECTED' else RED}{self.current_state}{RESET}")
        print(f"   Classe    : {CYAN}{self.selected_class}{RESET}")
        print(f"   Micro     : {GREEN if self.mic_plugged else RED}{'Branché' if self.mic_plugged else 'Débranché'}{RESET}")
        print(f"   LEDs      : {g_led}  |  {w_led}  |  {b_led}")
        print("═" * 70 + "\n")

    async def telemetry_loop(self):
        """Envoie périodiquement des données de télémétrie au serveur."""
        while self.running:
            try:
                if self.ws and not self.ws.closed:
                    payload = {
                        "type": "telemetry",
                        "device_id": self.device_id,
                        "battery": self.battery,
                        "rssi": -58,
                        "free_heap": 182400,
                        "mic_plugged": self.mic_plugged,
                        "current_class": self.selected_class,
                        "state": self.current_state,
                    }
                    await self.ws.send(json.dumps(payload))
            except Exception:
                pass
            await asyncio.sleep(5.0)

    async def receive_loop(self):
        """Écoute les commandes envoyées par le serveur AlternIA."""
        while self.running:
            try:
                msg_str = await self.ws.recv()
                data = json.loads(msg_str)
                msg_type = data.get("type", "")
                cmd = data.get("command", "")

                if cmd == "set_state" or msg_type == "command":
                    old_led = self.current_led
                    self.current_state = data.get("state", self.current_state)
                    self.current_led = data.get("led", self.current_led)
                    self.selected_class = data.get("selected_class", self.selected_class)
                    self.mic_plugged = data.get("mic_plugged", self.mic_plugged)

                    print(f"\n📥 {CYAN}[Serveur -> ESP32]{RESET} Ordre reçu : État={BOLD}{self.current_state}{RESET} | LED={BOLD}{self.current_led}{RESET}")
                    if self.current_led != old_led:
                        self.print_led_display()

                elif msg_type == "pong":
                    pass

            except websockets.ConnectionClosed:
                print(f"{RED}⚠️ Connexion WebSocket perdue avec le serveur.{RESET}")
                self.current_state = "DISCONNECTED"
                self.current_led = "OFF"
                self.print_led_display()
                break
            except Exception as e:
                print(f"Erreur réception : {e}")
                break

    async def interactive_cli(self):
        """Menu interactif en console pour déclencher des événements."""
        loop = asyncio.get_running_loop()
        while self.running:
            print(f"""
{BOLD}Actions de Simulation ESP32 :{RESET}
  [1] 🎓 Sélectionner classe 10ème Année
  [2] 🎓 Sélectionner classe 11ème Année
  [3] 🎓 Sélectionner classe Terminale TSE
  [4] 🎤 Basculer l'état du micro ({'Débrancher' if self.mic_plugged else 'Brancher'})
  [5] 🔘 Appuyer sur le bouton physique BOOT (Prendre la parole)
  [6] 🟢 Simuler connexion serveur réussie (Forcer LED Verte)
  [q] ❌ Quitter le simulateur
""")
            choice = await loop.run_in_executor(None, sys.stdin.readline)
            choice = choice.strip()

            if choice == "1":
                self.selected_class = "10eme"
                await self.send_class_selected("10eme")
            elif choice == "2":
                self.selected_class = "11eme"
                await self.send_class_selected("11eme")
            elif choice == "3":
                self.selected_class = "TSE"
                await self.send_class_selected("TSE")
            elif choice == "4":
                self.mic_plugged = not self.mic_plugged
                print(f"🎤 Micro désormais {'Branché' if self.mic_plugged else 'Débranché'}")
                if self.ws and not self.ws.closed:
                    await self.ws.send(json.dumps({"type": "mic_status", "plugged": self.mic_plugged}))
                # Si classe sélectionnée et micro branché -> BLANC
                if self.mic_plugged and self.selected_class:
                    self.current_led = "WHITE"
                else:
                    self.current_led = "GREEN"
                self.print_led_display()
            elif choice == "5":
                print(f"🔘 {YELLOW}Appui sur le bouton BOOT (Demande de parole de l'élève)...{RESET}")
                if self.ws and not self.ws.closed:
                    await self.ws.send(json.dumps({
                        "type": "button_press",
                        "button": "boot",
                        "device_id": self.device_id,
                        "class": self.selected_class
                    }))
            elif choice == "6":
                self.current_state = "CONNECTED"
                self.current_led = "GREEN"
                self.print_led_display()
            elif choice.lower() == "q":
                self.running = False
                break

    async def send_class_selected(self, class_name: str):
        print(f"🎓 Notification sélection classe : {class_name}")
        if self.ws and not self.ws.closed:
            await self.ws.send(json.dumps({
                "type": "class_change",
                "class": class_name,
                "mic_plugged": self.mic_plugged
            }))
        # Si le micro est branché, la LED passe en blanc !
        if self.mic_plugged:
            self.current_led = "WHITE"
            self.current_state = "CLASS_SELECTED"
        else:
            self.current_led = "GREEN"
        self.print_led_display()

    async def start(self):
        print(f"\n🚀 {BOLD}Démarrage du Simulateur ESP32 AlternIA...{RESET}")
        print(f"📡 Tentative de connexion vers : {CYAN}{self.server_url}{RESET}")

        try:
            async with websockets.connect(self.server_url) as ws:
                self.ws = ws
                self.current_state = "CONNECTED"
                self.current_led = "GREEN"  # Dès la connexion -> LED VERTE !
                print(f"✅ {GREEN}CONNECTÉ AVEC SUCCÈS AU SERVEUR ALTERNIA !{RESET}")
                self.print_led_display()

                # Tâches asynchrones
                telemetry_task = asyncio.create_task(self.telemetry_loop())
                recv_task = asyncio.create_task(self.receive_loop())
                cli_task = asyncio.create_task(self.interactive_cli())

                done, pending = await asyncio.wait(
                    [recv_task, cli_task],
                    return_when=asyncio.FIRST_COMPLETED
                )

                for task in pending:
                    task.cancel()
                telemetry_task.cancel()

        except Exception as e:
            print(f"{RED}❌ Impossible de se connecter au serveur AlternIA ({self.server_url}) : {e}{RESET}")
            print("👉 Vérifiez que le serveur AlternIA est bien démarré (colab_server.py ou backend/src/main.py).")


def main():
    parser = argparse.ArgumentParser(description="Simulateur matériel ESP32 pour AlternIA")
    parser.add_argument("--url", default="ws://127.0.0.1:8000/ws/esp32", help="URL WebSocket du serveur")
    parser.add_argument("--device-id", default="ESP32-ALT-01", help="ID matériel")
    args = parser.parse_args()

    sim = ESP32Simulator(server_url=args.url, device_id=args.device_id)
    try:
        asyncio.run(sim.start())
    except KeyboardInterrupt:
        print("\nArrêt du simulateur.")


if __name__ == "__main__":
    main()
