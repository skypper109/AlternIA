#!/usr/bin/env python3
"""
AlternIA Cloud Server Runner pour Google Colab Pro / AWS GPU
Lance l'API FastAPI et expose un tunnel public HTTPS sécurisé (Cloudflare Tunnel).
"""

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Chemins racine
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "ai-engine" / "src"))

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["PYTHONUNBUFFERED"] = "1"


def print_banner():
    print(r"""
\033[1;36m
   _   _ _                  ___   _    
  /_\ | | |_ ___ _ _ _ _   |_ _| /_\   
 / _ \| |  _/ -_) '_| ' \   | | / _ \  
/_/ \_\_|\__\___|_| |_||_| |___/_/ \_\ 
\033[0m
\033[1;32m🚀 Serveur d'Inférence IA & Générateur d'Avatar Vidéo (Colab Pro / AWS GPU)\033[0m
""")


def detect_hardware():
    """Affiche le matériel GPU détecté."""
    print("🔍 \033[1;33mVérification du matériel d'accélération...\033[0m")
    try:
        import torch
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            total_mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"✅ \033[1;32mGPU Détecté :\033[0m {device_name} ({total_mem:.1f} Go VRAM)")
            print(f"⚡ PyTorch {torch.__version__} avec CUDA {torch.version.cuda}")
        else:
            print("⚠️ \033[1;33mAucun GPU CUDA actif. Exécution en mode CPU.\033[0m")
    except ImportError:
        print("⚠️ PyTorch n'est pas encore installé.")


def install_cloudflared() -> str:
    """Télécharge et installe le binaire cloudflared si absent."""
    cloudflared_path = shutil.which("cloudflared")
    if cloudflared_path:
        return cloudflared_path

    print("📦 Installation de Cloudflare Tunnel (cloudflared)...")
    local_bin = Path("/tmp/cloudflared")
    if not local_bin.exists():
        import urllib.request
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
        urllib.request.urlretrieve(url, str(local_bin))
        local_bin.chmod(0o755)
    return str(local_bin)


def start_tunnel(port: int = 8000) -> tuple[subprocess.Popen, str]:
    """Démarre cloudflared et extrait l'URL HTTPS publique."""
    bin_path = install_cloudflared()
    print(f"🌐 Démarrage du tunnel HTTPS vers le port {port}...")

    cmd = [bin_path, "tunnel", "--url", f"http://127.0.0.1:{port}"]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    public_url = ""
    start_time = time.time()

    # Lecture des logs pour extraire l'URL trycloudflare.com
    if proc.stderr:
        while time.time() - start_time < 30:
            line = proc.stderr.readline()
            if not line and proc.poll() is not None:
                break
            match = re.search(r"(https://[a-zA-Z0-9-]+\.trycloudflare\.com)", line)
            if match:
                public_url = match.group(1)
                break

    if not public_url:
        print("⚠️ Impossible d'obtenir l'URL Cloudflare automatiquement. Vérifiez les logs.")
    return proc, public_url


def main():
    print_banner()
    detect_hardware()

    port = int(os.environ.get("PORT", 8000))

    # 1. Démarrer le tunnel Cloudflare
    tunnel_proc, public_url = start_tunnel(port=port)

    print("\n" + "=" * 76)
    if public_url:
        print(f"🌟 \033[1;32mAlternIA Cloud Server est PRÊT ET EN LIGNE !\033[0m")
        print(f"🔗 \033[1;36mURL PUBLIQUE HTTPS :\033[0m \033[1;4m{public_url}\033[0m")
        print(f"📱 Pour connecter votre boîtier ou le web, utilisez : \033[1m{public_url}\033[0m")
    else:
        print(f"🌟 AlternIA Server démarré localement sur : http://127.0.0.1:{port}")
    print("=" * 76 + "\n")

    # 2. Démarrer FastAPI avec Uvicorn
    import uvicorn
    from backend.src.main import app

    try:
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    finally:
        if tunnel_proc:
            tunnel_proc.terminate()


if __name__ == "__main__":
    main()
