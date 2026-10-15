#!/usr/bin/env python3
"""
══════════════════════════════════════════════════════════════════════════════
Agent de Télémétrie & Heartbeat pour Raspberry Pi 5 (Alta-Box)
══════════════════════════════════════════════════════════════════════════════

Ce service :
1. Collecte l'état du matériel (température CPU, RAM 8 Go, élèves connectés au Wi-Fi Alta-box1, IP).
2. Transmet un battement de cœur toutes les 30 secondes à https://api.alterniamali.com/api/boitiers/heartbeat.
3. Met à jour en direct le tableau de bord Direction/Établissement et Parents dans le portail Alta.
4. Active l'indicateur LED dès que la liaison avec le serveur AWS est confirmée.
"""

import os
import sys
import time
import json
import socket
import subprocess
from pathlib import Path

try:
    import urllib.request
except ImportError:
    pass

SERVER_URL = os.environ.get("ALTERNIA_API_URL", "https://api.alterniamali.com")
BOITIER_ID = os.environ.get("BOITIER_ID", "Alta-box1")
ETABLISSEMENT_ID = os.environ.get("ETABLISSEMENT_ID", "etab-lbad-bamako")
WIFI_SSID = os.environ.get("WIFI_SSID", "Alta-box1")

SERVER_STATUS_FLAG = Path("/tmp/alta_server_connected.flag")
ACTIVITY_FLAG = Path("/tmp/alta_activity.flag")


def get_cpu_temp() -> float:
    """Mesure la température du CPU du Raspberry Pi 5."""
    try:
        thermal_file = Path("/sys/class/thermal/thermal_zone0/temp")
        if thermal_file.exists():
            return round(float(thermal_file.read_text().strip()) / 1000.0, 1)
        res = subprocess.check_output(["vcgencmd", "measure_temp"], text=True)
        return float(res.replace("temp=", "").replace("'C", "").strip())
    except Exception:
        return 45.0


def get_ram_stats():
    """Mesure l'utilisation de la RAM (8 Go sur Pi 5)."""
    try:
        meminfo = Path("/proc/meminfo").read_text()
        total_kb = 0
        avail_kb = 0
        for line in meminfo.splitlines():
            if line.startswith("MemTotal:"):
                total_kb = int(line.split()[1])
            elif line.startswith("MemAvailable:"):
                avail_kb = int(line.split()[1])
        used_mo = round((total_kb - avail_kb) / 1024.0, 1)
        total_mo = round(total_kb / 1024.0, 1)
        return used_mo, total_mo
    except Exception:
        return 1200.0, 8192.0


def count_connected_wifi_clients() -> int:
    """Compte les élèves/smartphones connectés au Wi-Fi Alta-box1."""
    count = 0
    try:
        # Méthode 1 : Table ARP ou baux dnsmasq
        leases_file = Path("/var/lib/misc/dnsmasq.leases")
        if leases_file.exists():
            return len(leases_file.read_text().strip().splitlines())

        # Méthode 2 : Stations iw sur wlan0
        out = subprocess.check_output(["iw", "dev", "wlan0", "station", "dump"], stderr=subprocess.DEVNULL, text=True)
        count = out.count("Station ")
    except Exception:
        pass
    return max(count, 0)


def get_local_ip() -> str:
    """Obtient l'IP de la passerelle Wi-Fi du boîtier."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "10.42.0.1"


def get_pi_serial() -> str:
    """Extrait le numéro de série unique du processeur Pi 5."""
    try:
        cpuinfo = Path("/proc/cpuinfo").read_text()
        for line in cpuinfo.splitlines():
            if line.startswith("Serial"):
                return line.split(":")[1].strip()
    except Exception:
        pass
    return "RPI5-ALTA-001"


def send_heartbeat():
    """Envoie la télémétrie complète au backend AWS AlternIA."""
    used_ram, total_ram = get_ram_stats()
    clients = count_connected_wifi_clients()
    temp = get_cpu_temp()
    ip = get_local_ip()
    serial = get_pi_serial()

    # Si des élèves sont connectés, marquer une interaction
    if clients > 0:
        ACTIVITY_FLAG.touch(exist_ok=True)

    payload = {
        "boitier_id": BOITIER_ID,
        "numero_serie": serial,
        "modele": "Raspberry Pi 5 (8GB RAM)",
        "firmware": "v3.0-Pi5-Bookworm-Edge",
        "ip_locale": ip,
        "wifi_ssid": WIFI_SSID,
        "eleves_connectes": clients,
        "cpu_temp": temp,
        "ram_utilisee_mo": used_ram,
        "ram_totale_mo": total_ram,
        "batterie": 100,
        "statut": "en_ligne",
        "etablissement_id": ETABLISSEMENT_ID,
    }

    url = f"{SERVER_URL.rstrip('/')}/api/boitiers/heartbeat"
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "AltaBox-Agent/3.0"}
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status in (200, 201):
                # Marquer le statut serveur connecté pour la LED
                SERVER_STATUS_FLAG.touch(exist_ok=True)
                print(f"💓 [Heartbeat OK] {BOITIER_ID} | IP: {ip} | Élèves: {clients} | CPU: {temp}°C | RAM: {used_ram}/{total_ram} Mo")
                return True
    except Exception as exc:
        print(f"⚠️ [Heartbeat Échec] Serveur AWS non joignable ({exc}) - Mode local actif.")
        if SERVER_STATUS_FLAG.exists():
            try:
                SERVER_STATUS_FLAG.unlink()
            except Exception:
                pass
    return False


def main():
    print(f"🚀 Démarrage de l'agent de télémétrie AlternIA Box ({BOITIER_ID}) vers {SERVER_URL}")
    while True:
        send_heartbeat()
        time.sleep(30)


if __name__ == "__main__":
    main()
