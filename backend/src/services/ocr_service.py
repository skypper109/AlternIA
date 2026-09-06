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
import Cocoa
import Vision

guard CommandLine.arguments.count > 1 else {
    exit(1)
}

let imagePath = CommandLine.arguments[1]
let fileURL = URL(fileURLWithPath: imagePath)

guard let image = NSImage(contentsOf: fileURL),
      let tiffData = image.tiffRepresentation,
      let bitmap = NSBitmapImageRep(data: tiffData),
      let cgImage = bitmap.cgImage else {
    exit(1)
}

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
request.recognitionLanguages = ["fr-FR", "en-US"]

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
try? handler.perform([request])
"""

_SWIFT_SCRIPT_PATH: Optional[Path] = None


def _get_swift_script_path() -> Path:
    global _SWIFT_SCRIPT_PATH
    if _SWIFT_SCRIPT_PATH and _SWIFT_SCRIPT_PATH.exists():
        return _SWIFT_SCRIPT_PATH
    
    script_dir = Path(__file__).resolve().parent / ".ocr_cache"
    script_dir.mkdir(parents=True, exist_ok=True)
    script_file = script_dir / "vision_ocr.swift"
    if not script_file.exists():
        script_file.write_text(SWIFT_OCR_CODE, encoding="utf-8")
    _SWIFT_SCRIPT_PATH = script_file
    return script_file


def perform_ocr_on_image(image_bytes: bytes, filename: str = "document.jpg") -> str:
    """Effectue l'OCR sur les octets d'une image et retourne le texte extrait."""
    with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix or ".jpg", delete=False) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    try:
        # 1. Tentative Apple Vision sur macOS (100% natif, haute précision)
        if sys.platform == "darwin":
            try:
                script_path = _get_swift_script_path()
                proc = subprocess.run(
                    ["swift", str(script_path), tmp_path],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                if proc.returncode == 0 and proc.stdout.strip():
                    extracted = proc.stdout.strip()
                    logger.info(f"✅ OCR Apple Vision réussi ({len(extracted)} car.)")
                    return extracted
            except Exception as e:
                logger.warning(f"Note Apple Vision OCR : {e}")

        # 2. Fallback Tesseract si disponible
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(tmp_path)
            text = pytesseract.image_to_string(img, lang="fra+eng")
            if text.strip():
                return text.strip()
        except Exception:
            pass

        return ""
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
