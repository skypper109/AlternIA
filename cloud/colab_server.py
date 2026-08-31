#!/usr/bin/env python3
"""
AlternIA Cloud Server Runner pour Google Colab Pro / AWS GPU
Lance l'API FastAPI et expose un tunnel public HTTPS sécurisé (Cloudflare Tunnel).
"""

import tempfile
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

# Configuration persistante et automatique des chemins CUDA pour RunPod / Colab / Linux
for c_dir in ["/usr/local/cuda", "/usr/local/cuda-12", "/usr/local/cuda-12.8", "/usr/local/cuda-12.6"]:
    if os.path.exists(c_dir):
        os.environ["CUDA_HOME"] = c_dir
        if f"{c_dir}/bin" not in os.environ.get("PATH", ""):
            os.environ["PATH"] = f"{c_dir}/bin:{os.environ.get('PATH', '')}"
        cuda_lib = f"{c_dir}/lib64"
        current_ld = os.environ.get("LD_LIBRARY_PATH", "")
        if cuda_lib not in current_ld:
            os.environ["LD_LIBRARY_PATH"] = f"{cuda_lib}:{current_ld}".strip(":")
        break


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


def ensure_environment():
    """Vérifie et installe automatiquement les dépendances manquantes."""
    # 1. Vérification stricte de compatibilité binaire NumPy 1.x (requis pour PyTorch 2.2 et ONNXRuntime)
    try:
        import numpy as np
        if int(np.__version__.split(".")[0]) >= 2:
            print(f"⚡ NumPy {np.__version__} détecté. Rétrogradation vers NumPy 1.26.4 (requis pour ONNXRuntime / PyTorch)...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--force-reinstall", "numpy<2.0.0"], check=False)
            import importlib
            importlib.invalidate_caches()
    except Exception:
        pass

    required = [
        ("uvicorn", "uvicorn[standard]"),
        ("fastapi", "fastapi"),
        ("pydantic_settings", "pydantic-settings"),
        ("sqlalchemy", "sqlalchemy"),
        ("pymysql", "pymysql"),
        ("sentence_transformers", "sentence-transformers"),
        ("edge_tts", "edge-tts"),
        ("multipart", "python-multipart"),
        ("cv2", "opencv-python-headless"),
        ("faster_whisper", "faster-whisper"),
    ]
    missing = []
    for mod_name, pkg_name in required:
        try:
            __import__(mod_name)
        except ImportError:
            missing.append(pkg_name)

    if missing:
        print(f"📦 Installation automatique des dépendances manquantes : {', '.join(missing)}...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q"] + missing, check=False)

    # Vérification et auto-réparation du couplage transformers / sentence-transformers
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as exc:
        print("⚡ Incompatibilité de version détectée (transformers / sentence-transformers). Auto-réparation en cours...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "--upgrade", "transformers>=4.44.0", "sentence-transformers>=3.0.0"],
            check=False
        )
        import importlib
        importlib.invalidate_caches()

    # Vérification intelligente du support GPU CUDA dans llama-cpp-python
    is_llama_cuda_ready = False
    try:
        import llama_cpp
        if hasattr(llama_cpp, "llama_supports_gpu_offload"):
            is_llama_cuda_ready = llama_cpp.llama_supports_gpu_offload()
        else:
            is_llama_cuda_ready = getattr(llama_cpp, "GGML_USE_CUDA", False)
    except Exception:
        is_llama_cuda_ready = False

    if not is_llama_cuda_ready:
        print("⚡ Installation de llama-cpp-python avec accélération matérielle CUDA GPU...")
        # 1. Tenter la wheel pré-compilée CUDA 121 (instantanée, ~10s)
        res = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "--force-reinstall", "--no-cache-dir",
             "llama-cpp-python", "--extra-index-url", "https://abetlen.github.io/llama-cpp-python/whl/cu121"],
            check=False
        )
        # 2. Si échec, compiler avec CMAKE_ARGS="-DGGML_CUDA=on"
        if res.returncode != 0:
            env = os.environ.copy()
            env["CMAKE_ARGS"] = "-DGGML_CUDA=on"
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "--force-reinstall", "--no-cache-dir", "llama-cpp-python"], env=env, check=False)
        import importlib
        importlib.invalidate_caches()

    # Nettoyage automatique des caches temporaires pour préserver l'espace disque
    try:
        tmp_dir = Path(tempfile.gettempdir())
        for p in tmp_dir.glob("avatar_*"):
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            elif p.is_file():
                try:
                    p.unlink()
                except Exception:
                    pass
    except Exception:
        pass

    # Vérification et initialisation du moteur vidéo LivePortrait / SadTalker
    try:
        from alternia.talking_head.liveportrait_service import LivePortraitService
        lp = LivePortraitService()
        if lp.is_available():
            mode = "In-Memory Streaming (Zero-Disk)" if getattr(LivePortraitService, "_in_process_pipeline", None) else "Processus optimisé"
            engine_name = "LivePortrait" if lp.liveportrait_dir else "SadTalker"
            print(f"🎬 \033[1;32mMoteur Vidéo IA :\033[0m {engine_name} ({mode}) prêt pour l'animation photoréaliste.")
        else:
            print("🎬 \033[1;36mMoteur Vidéo IA :\033[0m Générateur vidéo MP4 haute définition en mémoire actif.")
    except Exception as e:
        print(f"ℹ️ Note moteur vidéo : {e}")


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
    ensure_environment()
    detect_hardware()

    port = int(os.environ.get("PORT", 8000))

    # 1. Démarrer le tunnel Cloudflare
    tunnel_proc, public_url = start_tunnel(port=port)

    print("\n" + "=" * 76)
    if public_url:
        print(f"🌟 \033[1;32mAlternIA Cloud Server est PRÊT ET EN LIGNE !\033[0m")
        print(f"🔗 \033[1;36mURL PUBLIQUE HTTPS :\033[0m \033[1;4m{public_url}\033[0m")
        print(f"📱 Pour connecter votre boîtier ou le web, utilisez : \033[1m{public_url}/device\033[0m")
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
