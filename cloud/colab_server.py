#!/usr/bin/env python3
"""
AlternIA Cloud Server Runner pour Google Colab Pro / AWS GPU
Lance l'API FastAPI et expose un tunnel public HTTPS sécurisé (Cloudflare Tunnel).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Chemins racine
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "ai-engine" / "src"))

CONFIG_PATH = PROJECT_ROOT / "data" / "tunnel_config.json"
COLAB_DRIVE_CONFIG = Path("/content/drive/MyDrive/alternia_tunnel.json")

# Chargement automatique des variables du fichier .env
env_file = PROJECT_ROOT / ".env"
if env_file.exists():
    try:
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("\"'")
                    if k not in os.environ:
                        os.environ[k] = v
    except Exception:
        pass

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
            cuda_ver = getattr(torch, "version", None)
            cuda_str = getattr(cuda_ver, "cuda", None) if cuda_ver else None
            print(f"⚡ PyTorch {torch.__version__} avec CUDA {cuda_str}")
        else:
            print("⚠️ \033[1;33mAucun GPU CUDA actif. Exécution en mode CPU.\033[0m")
    except ImportError:
        print("⚠️ PyTorch n'est pas encore installé.")


def ensure_environment():
    """Vérifie et installe automatiquement les dépendances manquantes."""
    # 1. Vérification et réparation stricte de la pile NumPy / SciPy / Transformers
    needs_numpy_repair = False
    try:
        import numpy as np
        if int(np.__version__.split(".")[0]) >= 2:
            needs_numpy_repair = True
        else:
            # Tester l'intégrité des C-extensions SciPy & Scikit-Learn
            import scipy.sparse
            import sklearn
    except Exception:
        needs_numpy_repair = True

    if needs_numpy_repair:
        print("⚡ Correction de compatibilité NumPy 1.26.4 / SciPy / Scikit-Learn...")
        subprocess.run(
            [
                sys.executable, "-m", "pip", "install", "-q",
                "numpy==1.26.4",
                "scipy==1.13.1",
                "scikit-learn>=1.4.0,<1.6.0",
                "opencv-python-headless>=4.8.0,<4.11.0",
            ],
            check=False
        )
        import importlib
        importlib.invalidate_caches()

    # 2. Vérification de PyTorch
    try:
        import torch
    except ImportError:
        print("⚡ Installation de PyTorch...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "torch>=2.4.0", "torchvision", "torchaudio"], check=False)

    # 3. Dépendances requises avec verrouillage de compatibilité
    required = [
        ("uvicorn", "uvicorn[standard]"),
        ("fastapi", "fastapi"),
        ("pydantic_settings", "pydantic-settings"),
        ("sqlalchemy", "sqlalchemy"),
        ("pymysql", "pymysql"),
        ("sentence_transformers", "sentence-transformers>=3.0.0"),
        ("edge_tts", "edge-tts"),
        ("multipart", "python-multipart"),
        ("cv2", "opencv-python-headless>=4.8.0,<4.11.0"),
        ("faster_whisper", "faster-whisper"),
        ("simli", "simli-ai"),
    ]
    missing = []
    for mod_name, pkg_name in required:
        try:
            __import__(mod_name)
        except Exception:
            missing.append(pkg_name)

    if missing:
        print(f"📦 Installation des dépendances manquantes : {', '.join(missing)}...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q"] + missing + ["numpy==1.26.4"], check=False)

    # 4. Vérification et auto-réparation de sentence-transformers
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as exc:
        print(f"⚡ Réparation sentence-transformers / transformers ({exc})...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "--upgrade",
             "transformers>=4.44.0", "sentence-transformers>=3.0.0", "huggingface-hub>=0.24.0", "numpy==1.26.4"],
            check=False
        )
        import importlib
        importlib.invalidate_caches()

    # 5. Vérification du support GPU CUDA dans llama-cpp-python
    is_llama_ready = False
    try:
        import llama_cpp
        is_llama_ready = True
    except Exception:
        is_llama_ready = False

    if not is_llama_ready:
        print("⚡ Compilation de llama-cpp-python avec accélération matérielle CUDA...")
        env = os.environ.copy()
        env["CMAKE_ARGS"] = "-DGGML_CUDA=on -DGGML_AVX512=off"
        # --no-binary force pip à compiler le code source localement au lieu de télécharger le wheel PyPI (CPU)
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--no-cache-dir", "--force-reinstall", "--no-binary", "llama-cpp-python", "llama-cpp-python", "numpy==1.26.4"],
            env=env,
            check=False
        )
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


def load_tunnel_config() -> dict:
    """Charge la configuration persistante du tunnel (local ou Google Drive)."""
    if COLAB_DRIVE_CONFIG.exists():
        try:
            with open(COLAB_DRIVE_CONFIG, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    return {}


def save_tunnel_config(config: dict):
    """Sauvegarde la configuration du tunnel pour qu'elle persiste aux prochains redémarrages."""
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception:
        pass

    if Path("/content/drive/MyDrive").exists():
        try:
            with open(COLAB_DRIVE_CONFIG, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            print("💾 Configuration du tunnel sauvegardée sur Google Drive.")
        except Exception:
            pass


def install_cloudflared() -> str:
    """Télécharge et installe le binaire cloudflared si absent."""
    cloudflared_path = shutil.which("cloudflared")
    if cloudflared_path:
        return cloudflared_path

    local_bin = Path("/tmp/cloudflared")
    if local_bin.exists():
        return str(local_bin)

    print("📦 Installation de Cloudflare Tunnel (cloudflared)...")
    import urllib.request
    import tarfile
    
    # Détection architecture Linux / macOS
    machine = os.uname().machine.lower()
    if sys.platform == "darwin":
        arch = "darwin-arm64" if "arm" in machine else "darwin-amd64"
        url = f"https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-{arch}.tgz"
        try:
            tar_path = Path("/tmp/cloudflared.tgz")
            urllib.request.urlretrieve(url, str(tar_path))
            with tarfile.open(tar_path, "r:gz") as tar:
                tar.extract("cloudflared", path="/tmp")
            local_bin.chmod(0o755)
            if tar_path.exists():
                tar_path.unlink()
            return str(local_bin)
        except Exception as e:
            print(f"⚠️ Erreur lors du téléchargement de cloudflared pour macOS ({e}).")
    else:
        arch = "linux-arm64" if "aarch" in machine or "arm" in machine else "linux-amd64"
        url = f"https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-{arch}"
        try:
            urllib.request.urlretrieve(url, str(local_bin))
            local_bin.chmod(0o755)
            return str(local_bin)
        except Exception as e:
            print(f"⚠️ Erreur lors du téléchargement de cloudflared ({e}). Essai avec le binaire par défaut...")
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
            try:
                urllib.request.urlretrieve(url, str(local_bin))
                local_bin.chmod(0o755)
                return str(local_bin)
            except Exception:
                pass

    return str(local_bin)


def start_tunnel(
    port: int = 8000,
    cli_token: str | None = None,
    cli_hostname: str | None = None,
    force_quick: bool = False
) -> tuple[subprocess.Popen | None, str, bool]:
    """
    Démarre le tunnel Cloudflare.
    - Si force_quick est True : Démarre directement le tunnel Quick Tunnel temporaire (trycloudflare.com).
    - Si un Token (CLOUDFLARE_TUNNEL_TOKEN) ET un nom de domaine (CLOUDFLARE_HOSTNAME) sont configurés :
      Démarre le tunnel permanent avec URL fixe (qui ne change JAMAIS).
    - Sinon :
      Démarre un tunnel Quick Tunnel temporaire gratuit (trycloudflare.com).
    Retourne : (processus, public_url, is_fixed_url)
    """
    bin_path = install_cloudflared()
    cfg = load_tunnel_config()

    # 1. Vérification automatique dans les Secrets Google Colab si présent
    colab_token = None
    colab_hostname = None
    try:
        from google.colab import userdata  # pyright: ignore[reportMissingImports]  # type: ignore
        colab_token = userdata.get("CLOUDFLARE_TUNNEL_TOKEN")
        colab_hostname = userdata.get("CLOUDFLARE_HOSTNAME")
    except Exception:
        pass

    # Priorités : Arguments CLI > Variables d'environnement > Colab Secrets > Configuration persistante
    tunnel_token = (
        cli_token
        or os.environ.get("CLOUDFLARE_TUNNEL_TOKEN")
        or os.environ.get("TUNNEL_TOKEN")
        or colab_token
        or cfg.get("tunnel_token", "").strip()
    )
    fixed_hostname = (
        cli_hostname
        or os.environ.get("CLOUDFLARE_HOSTNAME")
        or os.environ.get("TUNNEL_HOSTNAME")
        or colab_hostname
        or cfg.get("fixed_hostname", "").strip()
    )

    log_path = Path(tempfile.gettempdir()) / "cloudflared.log"

    # =========================================================================
    # OPTION A : TUNNEL NOMMÉ FIXE (URL PERMANENTE GARANTIE PAR TOKEN + DOMAINE)
    # =========================================================================
    # Règle vitale : Un tunnel nommé avec token nécessite OBLIGATOIREMENT un nom
    # de domaine public associé dans Cloudflare Zero Trust (ex: https://gpu.mondomaine.com).
    # Si le token est présent mais sans domaine, on bascule automatiquement sur trycloudflare.com
    # pour que l'utilisateur obtienne une URL réelle fonctionnelle au lieu d'un placeholder vide.
    has_valid_hostname = bool(fixed_hostname and "[Votre-Domaine" not in fixed_hostname and fixed_hostname.strip())

    if tunnel_token and not force_quick:
        if not has_valid_hostname:
            print("\n" + "─" * 76)
            print("⚠️  \033[1;33mToken Cloudflare détecté, mais aucun nom de domaine (CLOUDFLARE_HOSTNAME) configuré.\033[0m")
            print("ℹ️  Pour une URL fixe permanente, vous devez associer votre domaine public dans")
            print("   Cloudflare Zero Trust (dash.cloudflare.com) et renseigner CLOUDFLARE_HOSTNAME.")
            print("🔄 \033[1;32mBasculement automatique sur le Quick Tunnel gratuit (trycloudflare.com)...\033[0m")
            print("─" * 76 + "\n")
        else:
            print(f"🌐 \033[1;32mDémarrage du tunnel FIXE Cloudflare (URL Permanente)...\033[0m")
            if log_path.exists():
                try:
                    log_path.unlink()
                except Exception:
                    pass

            log_file = open(log_path, "w", encoding="utf-8")
            cmd = [bin_path, "tunnel", "run", "--token", tunnel_token]
            proc = subprocess.Popen(
                cmd,
                stdout=log_file,
                stderr=log_file,
                text=True,
            )

            time.sleep(3)
            if proc.poll() is not None:
                log_file.close()
                err = ""
                if log_path.exists():
                    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                        err = f.read()
                print(f"⚠️ Échec du tunnel fixe avec le token : {err.strip()[:300]}")
                print("🔄 Basculement automatique sur le tunnel temporaire trycloudflare.com...")
            else:
                log_file.close()
                public_url = fixed_hostname.strip()
                if not public_url.startswith("http"):
                    public_url = f"https://{public_url}"
                return proc, public_url, True

    # =========================================================================
    # OPTION B : QUICK TUNNEL TEMPORAIRE (trycloudflare.com)
    # =========================================================================
    print(f"🌐 Démarrage du tunnel temporaire Cloudflare vers le port {port}...")
    if log_path.exists():
        try:
            log_path.unlink()
        except Exception:
            pass

    log_file = open(log_path, "w", encoding="utf-8")
    cmd = [bin_path, "tunnel", "--url", f"http://127.0.0.1:{port}"]
    proc = subprocess.Popen(
        cmd,
        stdout=log_file,
        stderr=log_file,
        text=True,
    )

    public_url = ""
    start_time = time.time()

    while time.time() - start_time < 35:
        if proc.poll() is not None:
            break
        if log_path.exists():
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                matches = re.findall(r"(https://[a-zA-Z0-9-]+\.trycloudflare\.com)", content)
                if matches:
                    public_url = matches[-1]
                    break
        time.sleep(0.5)

    if not public_url:
        # Dernière tentative de lecture du log
        if log_path.exists():
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                matches = re.findall(r"(https://[a-zA-Z0-9-]+\.trycloudflare\.com)", content)
                if matches:
                    public_url = matches[-1]

    if not public_url:
        print(f"⚠️ Impossible d'obtenir l'URL Cloudflare automatiquement. Vérifiez les logs : {log_path}")
    return proc, public_url, False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="AlternIA Cloud Server Runner")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)), help="Port d'écoute local")
    parser.add_argument("--token", type=str, default=None, help="Token Cloudflare Tunnel pour URL fixe permanente")
    parser.add_argument("--hostname", type=str, default=None, help="Nom de domaine public associé au tunnel fixe")
    parser.add_argument("--quick", action="store_true", help="Forcer l'utilisation du tunnel temporaire gratuit (trycloudflare.com)")
    args, _ = parser.parse_known_args()

    print_banner()
    ensure_environment()
    detect_hardware()

    port = args.port

    # Démarrer le tunnel Cloudflare (fixe ou temporaire)
    tunnel_proc, public_url, is_fixed = start_tunnel(
        port=port,
        cli_token=args.token,
        cli_hostname=args.hostname,
        force_quick=args.quick
    )

    print("\n" + "=" * 76)
    if public_url:
        if is_fixed:
            print(f"🌟 \033[1;32mAlternIA Cloud Server est EN LIGNE avec une URL FIXE PERMANENTE !\033[0m")
            print(f"🔗 \033[1;36mURL PUBLIQUE HTTPS (FIXE) :\033[0m \033[1;4m{public_url}\033[0m")
            print(f"🔒 \033[1;33mCe lien ne changera JAMAIS, même après un redémarrage du serveur.\033[0m")
        else:
            print(f"🌟 \033[1;32mAlternIA Cloud Server est PRÊT ET EN LIGNE !\033[0m")
            print(f"🔗 \033[1;36mURL PUBLIQUE HTTPS (TEMPORAIRE) :\033[0m \033[1;4m{public_url}\033[0m")
            print(f"ℹ️ \033[1;33mPour fixer ce lien définitivement, configurez CLOUDFLARE_TUNNEL_TOKEN dans .env\033[0m")
        print(f"📱 Pour connecter votre boîtier physique ou le web : \033[1m{public_url}/device\033[0m")
    else:
        print(f"🌟 AlternIA Server démarré localement sur : http://127.0.0.1:{port}")
    print("=" * 76 + "\n")

    # Démarrer FastAPI avec Uvicorn
    import uvicorn
    from backend.src.main import app

    try:
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    finally:
        if tunnel_proc:
            tunnel_proc.terminate()


if __name__ == "__main__":
    main()

