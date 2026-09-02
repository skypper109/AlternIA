#!/usr/bin/env python3
"""
AlternIA — Lanceur Hybride Universel (Local & Cloud GPU).

Permet de démarrer le serveur en local ou de basculer l'interface vers un serveur Cloud GPU (RunPod / Colab / AWS).
"""

import os
import sys
import webbrowser
from pathlib import Path

# Résolution des chemins racines
PROJECT_ROOT = Path(__file__).resolve().parent
AI_ENGINE_DIR = PROJECT_ROOT / "ai-engine" / "src"
BACKEND_DIR = PROJECT_ROOT / "backend" / "src"

for p in (PROJECT_ROOT, AI_ENGINE_DIR, BACKEND_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


def print_banner():
    print("""\033[1;36m
   _   _ _                  ___   _  
  /_\ | | |_ ___ _ _ _ _   |_ _| /_\ 
 / _ \| |  _/ -_) '_| ' \   | | / _ \
/_/ \_\_|\__\___|_| |_||_| |___/_/ \_\
\033[0m
\033[1;32m🌟 AlternIA — Système Pédagogique Intelligent du Mali\033[0m
""")


def start_local_server(port: int = 8000, open_browser: bool = True):
    """Lance le serveur FastAPI local avec RAG, Base SQLite et Kiosk."""
    import uvicorn
    from backend.src.main import app

    url = f"http://127.0.0.1:{port}/device/"
    print(f"\n🚀 Démarrage du serveur local AlternIA sur \033[1;32m{url}\033[0m...")
    print(f"📖 Interface Kiosk tactile : \033[1;36m{url}\033[0m")
    print(f"🔑 Portail Backoffice Alta  : \033[1;35mhttp://127.0.0.1:{port}/auth/connexion\033[0m")
    print(f"📚 Documentation Swagger    : \033[1;33mhttp://127.0.0.1:{port}/docs\033[0m\n")

    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


def connect_to_cloud():
    """Configure la connexion de l'interface locale vers un serveur Cloud GPU."""
    print("\n☁️  \033[1;33mMode Connexion Cloud GPU\033[0m")
    print("Entrez l'URL publique HTTPS générée par votre serveur RunPod / Cloudflare.")
    print("Exemple : https://mon-serveur-cloud.trycloudflare.com\n")

    cloud_url = input("🔗 URL du serveur Cloud : ").strip()
    if not cloud_url:
        print("❌ Aucune URL fournie. Annulation.")
        return

    if not cloud_url.startswith("http"):
        cloud_url = "https://" + cloud_url

    kiosk_url = f"{cloud_url}/device/"
    backoffice_url = f"{cloud_url}/auth/connexion"

    print(f"\n✅ Connexion configurée vers : \033[1;32m{cloud_url}\033[0m")
    print(f"📱 Interface Kiosk Élève : \033[1;36m{kiosk_url}\033[0m")
    print(f"🔑 Portail Backoffice    : \033[1;35m{backoffice_url}\033[0m\n")

    try:
        webbrowser.open(kiosk_url)
    except Exception:
        pass


def show_mobile_instructions():
    """Affiche les étapes pour connecter l'application mobile Flutter."""
    print("""
\033[1;35m📱 INSTRUCTIONS DE CONNEXION POUR L'APPLICATION MOBILE\033[0m
============================================================================
1. Récupérez l'URL HTTPS de votre serveur Cloud (RunPod / Cloudflare Tunnel)
   Exemple : https://votre-tunnel.trycloudflare.com

2. Dans l'application mobile AlternIA :
   - Ouvrez les Réglages > Adresse du Serveur
   - Collez l'URL complète
   - Appuyez sur 'Tester la connexion'

3. Les révisions, quiz, et l'avatar enseignant se synchroniseront en temps réel !
============================================================================
""")


def main():
    print_banner()
    print("Sélectionnez votre mode d'exécution :")
    print(" [1] 🏠 Démarrer le serveur local complet (FastAPI + RAG + Kiosk)")
    print(" [2] ☁️  Connecter l'interface à un serveur Cloud GPU (RunPod / Colab)")
    print(" [3] 📱 Afficher les instructions de connexion Mobile")
    print(" [4] ❌ Quitter")

    choice = input("\nVotre choix [1/2/3/4] (Défaut: 1) : ").strip() or "1"

    if choice == "1":
        start_local_server()
    elif choice == "2":
        connect_to_cloud()
    elif choice == "3":
        show_mobile_instructions()
    else:
        print("Au revoir !")


if __name__ == "__main__":
    main()
