"""
Service OCR Pédagogique pour AlternIA — Extraction de texte d'exercices & documents scolaires.
Supporte Apple Vision haute précision (macOS natif) et fallback textuel.
"""

import os
import sys
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger("AlternIA.OCRService")

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

    # Compiler en binaire natif si le binaire n'existe pas ou si le script est plus récent
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


def perform_ocr_on_image(image_bytes: bytes, filename: str = "document.jpg") -> str:
    """Effectue l'OCR sur les octets d'une image et retourne le texte extrait."""
    with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix or ".jpg", delete=False) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    try:
        # 1. Tentative Apple Vision sur macOS (100% natif, haute précision)
        if sys.platform == "darwin":
            try:
                bin_path = _get_swift_binary_path()
                if bin_path:
                    proc = subprocess.run(
                        [str(bin_path), tmp_path],
                        capture_output=True,
                        text=True,
                        timeout=8,
                    )
                    if proc.returncode == 0 and proc.stdout.strip():
                        extracted = proc.stdout.strip()
                        logger.info(f"✅ OCR Apple Vision binaire réussi ({len(extracted)} car.)")
                        return extracted

                # Fallback : exécution directe du script swift si binaire non prêt
                script_path = _get_swift_script_path()
                proc = subprocess.run(
                    ["swift", str(script_path), tmp_path],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                if proc.returncode == 0 and proc.stdout.strip():
                    extracted = proc.stdout.strip()
                    logger.info(f"✅ OCR Apple Vision script réussi ({len(extracted)} car.)")
                    return extracted
            except Exception as e:
                logger.warning(f"Note Apple Vision OCR : {e}")

        # 2. Support direct pour fichiers PDF (via PyMuPDF / fitz déjà installé)
        if filename.lower().endswith(".pdf") or image_bytes.startswith(b"%PDF"):
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(stream=image_bytes, filetype="pdf")
                pdf_texts = [page.get_text() for page in doc]
                extracted_pdf = "\n".join(pdf_texts).strip()
                if extracted_pdf:
                    logger.info(f"✅ OCR/Extraction PDF réussie ({len(extracted_pdf)} car.)")
                    return extracted_pdf
            except Exception as pdf_err:
                logger.warning(f"Note extraction PDF : {pdf_err}")

        # 3. Fallback Tesseract multi-langues avec dégradation gracieuse
        try:
            import pytesseract  # type: ignore
            from PIL import Image
            img = Image.open(tmp_path)
            
            # Essayer d'abord fra+eng, puis fra, puis eng, puis défaut système
            for lang_opt in ["fra+eng", "fra", "eng", None]:
                try:
                    kwargs = {"lang": lang_opt} if lang_opt else {}
                    text = pytesseract.image_to_string(img, **kwargs)
                    if text and text.strip():
                        logger.info(f"✅ OCR Tesseract réussi (lang={lang_opt}, {len(text.strip())} car.)")
                        return text.strip()
                except Exception:
                    continue
        except Exception as tess_err:
            logger.warning(f"Note Tesseract OCR : {tess_err}")

        # 4. Fallback EasyOCR si installé
        try:
            import easyocr  # type: ignore
            reader = easyocr.Reader(['fr', 'en'], gpu=True)
            results = reader.readtext(tmp_path, detail=0)
            text_easy = " ".join(results).strip()
            if text_easy:
                logger.info(f"✅ OCR EasyOCR réussi ({len(text_easy)} car.)")
                return text_easy
        except Exception:
            pass

        logger.warning("⚠️ Aucun texte extrait : vérifiez que tesseract-ocr (apt) et pytesseract (pip) sont installés sur le serveur Linux.")
        return ""
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
