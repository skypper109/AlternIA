"""
Service OCR Pédagogique pour AlternIA — Extraction de texte d'exercices & documents scolaires.
Supporte Apple Vision (macOS natif), Deep Learning EasyOCR (photos mobiles & écritures),
PyMuPDF (PDF vectoriels) et Tesseract multi-langues avec prétraitement d'images OpenCV.
"""

import os
import sys
import io
import shutil
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, List, Tuple, Any

logger = logging.getLogger("AlternIA.OCRService")

# ==============================================================================
# 1. APPLE VISION (macOS Natif Haute Fidélité)
# ==============================================================================
SWIFT_OCR_CODE = """
import Foundation
import Vision

guard CommandLine.arguments.count > 1 else {
    exit(1)
}

let imagePath = CommandLine.arguments[1]
let fileURL = URL(fileURLWithPath: imagePath)

let request = VNRecognizeTextRequest { request, error in
    guard let observations = request.results as? [VNRecognizedTextObservation], error == nil else {
        return
    }
    let recognizedStrings = observations.compactMap { observation in
        observation.topCandidates(1).first?.string
    }
    print(recognizedStrings.joined(separator: "\\n"))
}

request.recognitionLevel = .accurate
request.usesLanguageCorrection = true
request.recognitionLanguages = ["fr-FR", "en-US"]

let handler = VNImageRequestHandler(url: fileURL, options: [:])
try? handler.perform([request])
"""

_SWIFT_SCRIPT_PATH: Optional[Path] = None
_SWIFT_BINARY_PATH: Optional[Path] = None


def _get_swift_script_path() -> Path:
    global _SWIFT_SCRIPT_PATH
    if _SWIFT_SCRIPT_PATH and _SWIFT_SCRIPT_PATH.exists():
        return _SWIFT_SCRIPT_PATH

    script_dir = Path(__file__).resolve().parent / ".ocr_cache"
    script_dir.mkdir(parents=True, exist_ok=True)
    script_file = script_dir / "vision_ocr.swift"
    script_file.write_text(SWIFT_OCR_CODE, encoding="utf-8")
    _SWIFT_SCRIPT_PATH = script_file
    return script_file


def _get_swift_binary_path() -> Optional[Path]:
    global _SWIFT_BINARY_PATH
    if _SWIFT_BINARY_PATH and _SWIFT_BINARY_PATH.exists() and os.access(str(_SWIFT_BINARY_PATH), os.X_OK):
        return _SWIFT_BINARY_PATH

    script_dir = Path(__file__).resolve().parent / ".ocr_cache"
    script_dir.mkdir(parents=True, exist_ok=True)
    script_file = _get_swift_script_path()
    bin_file = script_dir / "vision_ocr"

    if not bin_file.exists() or (script_file.stat().st_mtime > bin_file.stat().st_mtime):
        try:
            res = subprocess.run(
                ["swiftc", "-O", str(script_file), "-o", str(bin_file)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if res.returncode == 0 and bin_file.exists():
                bin_file.chmod(0o755)
        except Exception as e:
            logger.warning(f"Échec compilation swiftc native : {e}")

    if bin_file.exists() and os.access(str(bin_file), os.X_OK):
        _SWIFT_BINARY_PATH = bin_file
        return bin_file
    return None


# ==============================================================================
# 2. PRÉTRAITEMENT INTELLIGENT DE L'IMAGE (Orientation EXIF & Contraste OpenCV)
# ==============================================================================
def _preprocess_image(image_bytes: bytes, suffix: str = ".jpg") -> Tuple[str, Optional[str]]:
    """
    Normalise l'orientation de l'image (correction EXIF smartphone) et génère
    une version à contraste rehaussé (CLAHE / débruitage) pour maximiser la
    détection d'écriture manuscrite ou sur papier quadrillé.
    Retourne (chemin_image_orientee, chemin_image_rehaussee).
    """
    from PIL import Image, ImageOps

    # 1. Correction d'orientation EXIF via PIL (essentiel pour les photos smartphone)
    raw_img = Image.open(io.BytesIO(image_bytes))
    oriented_img = ImageOps.exif_transpose(raw_img)
    if oriented_img.mode not in ("RGB", "L"):
        oriented_img = oriented_img.convert("RGB")

    with tempfile.NamedTemporaryFile(suffix=suffix or ".jpg", delete=False) as f_norm:
        oriented_path = f_norm.name
        oriented_img.save(oriented_path, quality=95)

    enhanced_path: Optional[str] = None
    try:
        import cv2
        import numpy as np

        # Charger l'image avec OpenCV en niveaux de gris
        gray = cv2.imread(oriented_path, cv2.IMREAD_GRAYSCALE)
        if gray is not None:
            h, w = gray.shape[:2]

            # Si l'image est petite, la redimensionner (DPI insuffisant pour l'écriture)
            if max(h, w) < 1600:
                scale = 1600.0 / max(h, w)
                gray = cv2.resize(gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

            # Élimination des ombres d'éclairage et rehaussement local du contraste (CLAHE)
            clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)

            # Léger flou bilatéral pour lisser le grain sans altérer les traits d'encre
            enhanced = cv2.bilateralFilter(enhanced, d=5, sigmaColor=50, sigmaSpace=50)

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f_enh:
                enhanced_path = f_enh.name
                cv2.imwrite(enhanced_path, enhanced)
    except Exception as cv_err:
        logger.debug(f"Prétraitement OpenCV optionnel non appliqué : {cv_err}")

    return oriented_path, enhanced_path


# ==============================================================================
# 3. MOTEUR DEEP LEARNING EASYOCR (Singleton & Gestion VRAM / CPU)
# ==============================================================================
_EASYOCR_READER: Optional[Any] = None
_EASYOCR_ATTEMPTED: bool = False


def _get_easyocr_reader() -> Optional[Any]:
    """Initialise un singleton EasyOCR en évitant les crashs CUDA de mémoire."""
    global _EASYOCR_READER, _EASYOCR_ATTEMPTED
    if _EASYOCR_READER is not None:
        return _EASYOCR_READER
    if _EASYOCR_ATTEMPTED:
        return None

    _EASYOCR_ATTEMPTED = True
    try:
        import easyocr  # type: ignore
        import torch

        use_gpu = False
        if torch.cuda.is_available():
            try:
                # Vérifier si au moins 800 Mo de VRAM sont disponibles
                free_bytes, _ = torch.cuda.mem_get_info()
                if free_bytes > 800 * 1024 * 1024:
                    use_gpu = True
            except Exception:
                use_gpu = False

        logger.info(f"Initialisation EasyOCR (mode {'GPU' if use_gpu else 'CPU'})...")
        _EASYOCR_READER = easyocr.Reader(["fr", "en"], gpu=use_gpu)
        logger.info("✅ EasyOCR prêt pour la reconnaissance de documents.")
        return _EASYOCR_READER
    except Exception as e:
        logger.warning(f"EasyOCR non disponible : {e}")
        return None


def _run_easyocr(image_path: str) -> str:
    """Exécute EasyOCR sur une image et retourne le texte assemblé."""
    reader = _get_easyocr_reader()
    if not reader:
        return ""
    try:
        results = reader.readtext(image_path, detail=0, paragraph=True)
        if isinstance(results, list):
            text = "\n".join(str(r) for r in results).strip()
            return text
    except Exception as e:
        logger.warning(f"Erreur d'inférence EasyOCR : {e}")
    return ""


# ==============================================================================
# 4. MOTEUR TESSERACT (Multi-modes & Détection d'erreurs claire)
# ==============================================================================
def _run_tesseract(image_path: str) -> Tuple[str, Optional[str]]:
    """
    Exécute Tesseract sur une image avec diagnostic d'installation.
    Retourne (texte_extrait, message_erreur_eventuel).
    """
    try:
        import pytesseract  # type: ignore
        from PIL import Image
    except ImportError:
        return "", "Bibliothèque Python pytesseract non installée (faire : pip install pytesseract)"

    # Localisation du binaire tesseract
    tess_cmd = shutil.which("tesseract")
    if not tess_cmd:
        for common_path in ["/usr/bin/tesseract", "/usr/local/bin/tesseract", "/opt/homebrew/bin/tesseract"]:
            if os.path.exists(common_path) and os.access(common_path, os.X_OK):
                tess_cmd = common_path
                pytesseract.pytesseract.tesseract_cmd = common_path
                break

    if not tess_cmd:
        return "", "Binaire tesseract absent du système Linux (faire : apt-get install -y tesseract-ocr)"

    try:
        img = Image.open(image_path)
    except Exception as img_err:
        return "", f"Impossible de charger l'image pour Tesseract : {img_err}"

    best_text = ""
    last_err: Optional[str] = None

    # Tester les modes de segmentation adaptés aux devoirs : psm 3 (auto) et psm 6 (bloc de texte)
    for psm in ["--psm 3", "--psm 6"]:
        for lang_opt in ["fra+eng", "fra", "eng", None]:
            config = f"{psm}"
            kwargs = {"config": config}
            if lang_opt:
                kwargs["lang"] = lang_opt
            try:
                text = str(pytesseract.image_to_string(img, **kwargs)).strip()
                if len(text) > len(best_text):
                    best_text = text
                if len(best_text) >= 20:
                    return best_text, None
            except Exception as e:
                last_err = str(e)
                continue

    return best_text, last_err


# ==============================================================================
# 5. PIPELINE OCR PRINCIPAL
# ==============================================================================
def perform_ocr_on_image(image_bytes: bytes, filename: str = "document.jpg") -> str:
    """
    Effectue l'OCR sur les octets d'une image ou d'un document PDF.
    Stratégie en cascade :
    1. macOS Apple Vision (si darwin)
    2. PyMuPDF (si PDF)
    3. EasyOCR (Deep Learning adapté aux photos mobiles et écritures manuscrites)
    4. Tesseract OCR (avec prétraitement de contraste CLAHE)
    """
    if not image_bytes:
        return ""

    # Support direct pour fichiers PDF
    if filename.lower().endswith(".pdf") or image_bytes.startswith(b"%PDF"):
        try:
            import fitz  # PyMuPDF
            with fitz.open(stream=image_bytes, filetype="pdf") as doc:
                pdf_texts = [str(page.get_text()) for page in doc]
            extracted_pdf = "\n".join(pdf_texts).strip()
            if extracted_pdf:
                logger.info(f"✅ OCR/Extraction PDF réussie ({len(extracted_pdf)} car.)")
                return extracted_pdf
        except Exception as pdf_err:
            logger.warning(f"Note extraction PDF : {pdf_err}")

    suffix = Path(filename).suffix or ".jpg"
    oriented_path, enhanced_path = _preprocess_image(image_bytes, suffix=suffix)

    try:
        # 1. Tentative Apple Vision sur macOS
        if sys.platform == "darwin":
            try:
                bin_path = _get_swift_binary_path()
                target_proc = [str(bin_path), oriented_path] if bin_path else None
                if not target_proc:
                    script_path = _get_swift_script_path()
                    target_proc = ["swift", str(script_path), oriented_path]

                proc = subprocess.run(target_proc, capture_output=True, text=True, timeout=12)
                if proc.returncode == 0 and proc.stdout.strip():
                    extracted = proc.stdout.strip()
                    logger.info(f"✅ OCR Apple Vision réussi ({len(extracted)} car.)")
                    return extracted
            except Exception as e:
                logger.debug(f"Apple Vision OCR non disponible ou échec : {e}")

        # 2. EasyOCR (Deep Learning) : Idéal sur photos de smartphones et écritures
        for p in [oriented_path, enhanced_path]:
            if not p:
                continue
            text_easy = _run_easyocr(p)
            if text_easy and len(text_easy) >= 6:
                logger.info(f"✅ OCR EasyOCR réussi ({len(text_easy)} car.)")
                return text_easy

        # 3. Tesseract avec images prétraitées
        tess_diagnostic: Optional[str] = None
        for p in [oriented_path, enhanced_path]:
            if not p:
                continue
            text_tess, err = _run_tesseract(p)
            if err and not tess_diagnostic:
                tess_diagnostic = err
            if text_tess and len(text_tess) >= 6:
                logger.info(f"✅ OCR Tesseract réussi ({len(text_tess)} car.)")
                return text_tess

        if tess_diagnostic:
            logger.warning(f"⚠️ Diagnostic OCR Serveur : {tess_diagnostic}")
        else:
            logger.warning(
                "⚠️ Aucun texte exploitable extrait. Recommandation serveur : installez easyocr (pip install easyocr) "
                "ou tesseract-ocr (apt-get install -y tesseract-ocr tesseract-ocr-fra)."
            )
        return ""

    finally:
        for temp_p in [oriented_path, enhanced_path]:
            if temp_p and os.path.exists(temp_p):
                try:
                    os.remove(temp_p)
                except Exception:
                    pass
