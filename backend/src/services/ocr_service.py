"""
Service OCR Pédagogique pour AlternIA — Extraction de texte d'exercices & documents scolaires.
Supporte Apple Vision (macOS natif), Deep Learning EasyOCR (photos mobiles & écritures),
PyMuPDF (PDF vectoriels) et Tesseract multi-langues avec prétraitement d'images OpenCV.
"""

import os
import sys
import io
import re
import json
import time
import shutil
import logging
import asyncio
import unicodedata
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, List, Tuple, Any, Dict

# Intégration du moteur IA AlternIA dans le path
ROOT_DIR = Path(__file__).resolve().parents[3]
AI_ENGINE_DIR = ROOT_DIR / "ai-engine" / "src"
for p in (ROOT_DIR, AI_ENGINE_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

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


# ==============================================================================
# 6. VALIDATION & FILTRAGE ACADÉMIQUE DE DOCUMENTS SCOLAIRES
# ==============================================================================
FINANCIAL_RECEIPT_TERMS = [
    "transaction", "montant", "frais", "fcfa", "xof", "cfa", "solde",
    "ref bill", "reçu de", "recu de", "ticket de caisse", "retrait", "dépôt", "depot",
    "orange money", "wave", "moov money", "sama money", "facture",
    "carte sim", "numéro de téléphone", "numero de telephone", "carte d'identité",
    "permis de conduire", "passeport", "bancaire", "virement", "guichet"
]

ACADEMIC_EXERCISE_INDICATORS = [
    "exercice", "problème", "probleme", "devoir", "question", "calculer",
    "démontrer", "demontrer", "montrer que", "justifier", "déterminer", "determiner",
    "résoudre", "resoudre", "équation", "equation", "fonction", "théorème", "theoreme",
    "formule", "suite", "intégrale", "integrale", "dérivée", "derivee", "vecteur",
    "vitesse", "accélération", "acceleration", "force", "tension", "courant",
    "chimie", "atome", "molécule", "molecule", "acide", "base", "ph", "solution",
    "cellule", "adn", "génétique", "genetique", "chromosome", "svt", "biologie",
    "dissertation", "commentaire", "texte", "strophe", "auteur", "philosophie",
    "histoire", "géographie", "geographie", "siècle", "siecle", "empire", "mali"
]


def is_valid_academic_document(text: str) -> Tuple[bool, str, str, str]:
    """
    Vérifie si le texte scanné est lisible et correspond bien à un exercice
    ou document scolaire du programme.
    Retourne (is_valid, status, topic, message).
    """
    clean_text = (text or "").strip()
    if not clean_text or len(clean_text) < 5:
        return (
            False,
            "unreadable",
            "Image illisible ou vide",
            "Le document scanné ne contient aucun texte exploitable. Assurez-vous de bien éclairer la feuille et de photographier l'énoncé de près avec netteté."
        )

    norm_text = clean_text.lower()
    non_acad_matches = sum(1 for term in FINANCIAL_RECEIPT_TERMS if term in norm_text)
    acad_matches = sum(1 for term in ACADEMIC_EXERCISE_INDICATORS if term in norm_text)

    is_math_formula = bool(re.search(r"(=|<|>|\+|\*|\^|\b[xyz]\b|f\s*\([a-z]\)|\b(?:lim|sqrt|cos|sin|tan|ln|log)\b)", clean_text, re.IGNORECASE))
    if is_math_formula:
        acad_matches += 1

    has_strong_academic = bool(re.search(r"\b(?:exercice|probl[eè]me|devoir|d[eé]montrer|r[eé]soudre|[eé]quation|th[eé]or[eè]me|bac|d[eé]riv[eé]e|int[eé]grale|dissertation|commentaire)\b", clean_text, re.IGNORECASE))

    # Détection des reçus financiers / tickets non académiques
    if non_acad_matches >= 2 and not has_strong_academic:
        return (
            False,
            "not_curriculum",
            "Reçu ou document financier",
            "Ce document ne correspond pas au programme scolaire (reçu de paiement, ticket financier ou document commercial détecté). Veuillez scanner une page de cours ou un exercice scolaire (Mathématiques, Physique-Chimie, SVT, Français, Philosophie, etc.)."
        )

    # Rejet si aucun indicateur académique ni formule après un texte long
    if acad_matches == 0 and len(clean_text) > 40:
        # Recherche si des mots-clés du programme sont présents
        try:
            from alternia.pedagogical.curriculum_keywords import detect_malian_curriculum_subject
            sub = detect_malian_curriculum_subject(clean_text)
            if not sub:
                return (
                    False,
                    "not_curriculum",
                    "Hors programme scolaire",
                    "Le texte détecté ne semble pas être un énoncé d'exercice ou un extrait de cours conforme au programme du collège ou du lycée. Cadrez directement l'exercice à résoudre."
                )
        except Exception:
            pass

    return (True, "success", "Exercice académique valide", "")


# ==============================================================================
# 7. CLASSIFICATION DISCIPLINAIRE & EXTRACTION DE CONTENU SCOLAIRE
# ==============================================================================
SUBJECT_DISPLAY_NAMES = {
    "biologie": "SVT / Biologie",
    "chimie": "Physique-Chimie",
    "physique": "Physique-Chimie",
    "mathematiques": "Mathématiques",
    "philosophie": "Philosophie",
    "histoire-geographie": "Histoire-Géographie",
    "histoire": "Histoire-Géographie",
    "geographie": "Histoire-Géographie",
    "francais": "Français",
    "anglais": "Anglais",
    "economie": "Économie",
    "comptabilite": "Comptabilité",
    "droit": "Droit & Éducation civique",
}


def detect_exercise_curriculum_profile(clean_text: str, user_subject: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyse en profondeur le texte extrait pour classifier précisément la matière,
    le type de document (problème, commentaire, dissertation, etc.), le chapitre/thème
    et extrait les entités clés (questions, nombres, symboles).
    """
    norm_text = clean_text.lower()
    canonical_subject = None

    try:
        from alternia.pedagogical.curriculum_keywords import MALIAN_CURRICULUM_KEYWORDS, normalize_curriculum_text
        norm_kw_text = normalize_curriculum_text(clean_text)

        # Calcul d'un score pondéré par matière
        scores: Dict[str, int] = {}
        for subj, kw_list in MALIAN_CURRICULUM_KEYWORDS.items():
            s = 0
            for kw in kw_list:
                kw_norm = normalize_curriculum_text(kw)
                if len(kw_norm) < 3:
                    continue
                pattern = r"\b" + re.escape(kw_norm) + r"\b"
                if re.search(pattern, norm_kw_text):
                    s += 3 if (" " in kw or "-" in kw) else 1
            if s > 0:
                scores[subj] = s

        # Bonus contextuels majeurs (résolution des collisions lexicales comme "corps" ou "force")
        if re.search(r"\b(génétique|genetique|drosophile|croisement|allèle|allele|chromosome|mendel|lignée pure|monohybridisme|dihybridisme|f1|f2|phénotype|phenotype|génotype|genotype|mitose|méiose|adn|cellule)\b", norm_text):
            scores["biologie"] = scores.get("biologie", 0) + 10
        if re.search(r"\b(dosage|titrage|solution aqueuse|acide chlorhydrique|hydroxyde de sodium|soude|indicateur coloré|équivalence|stœchiométrie|stoechiometrie|oxydoréduction|oxydant|réducteur)\b", norm_text):
            scores["chimie"] = scores.get("chimie", 0) + 10
        if re.search(r"\b(loi de newton|lois de newton|accélération|acceleration|chute libre|plan incliné|référentiel galiléen|circuit rlc|condensateur|bobine|loi d'ohm|lentille)\b", norm_text):
            scores["physique"] = scores.get("physique", 0) + 10
        if re.search(r"\b(fonction|f\(x\)|dérivée|derivee|limite|asymptote|intégrale|integrale|suite numérique|nombre complexe|équation différentielle)\b", norm_text):
            scores["mathematiques"] = scores.get("mathematiques", 0) + 10
        if re.search(r"\b(commentaire composé|dissertation littéraire|poème|poeme|strophe|vers|alexandrin|figure de style|métaphore|senghor|césaire)\b", norm_text):
            scores["francais"] = scores.get("francais", 0) + 10
        if re.search(r"\b(dissertation philosophique|inconscient|morale|justice|vérité|autrui|éthique|socrate|descartes|kant)\b", norm_text):
            scores["philosophie"] = scores.get("philosophie", 0) + 10
        if re.search(r"\b(empire du mali|soundiata|mansa moussa|décolonisation|guerre froide|fleuve niger|climat sahélien)\b", norm_text):
            scores["histoire"] = scores.get("histoire", 0) + 10

        if scores:
            canonical_subject = max(scores, key=scores.__getitem__)
    except Exception as e:
        logger.debug(f"Détection curriculum_keywords en secours heuristique : {e}")

    # Fallback heuristique si non détecté
    if not canonical_subject:
        if any(w in norm_text for w in ["f(x)", "intégrale", "dérivée", "équation", "suite", "triangle", "cos", "sin", "matrice", "probabilité", "vecteur"]):
            canonical_subject = "mathematiques"
        elif any(w in norm_text for w in ["newton", "force", "masse", "vitesse", "circuit", "tension", "ampère", "joule", "onde", "lentille"]):
            canonical_subject = "physique"
        elif any(w in norm_text for w in ["acide", "base", "ph", "solution", "titrage", "dosage", "oxydant", "réducteur", "mol/l", "estérification"]):
            canonical_subject = "chimie"
        elif any(w in norm_text for w in ["cellule", "chromosome", "allèle", "adn", "mitose", "méiose", "plante", "chlorophylle", "sol", "roche"]):
            canonical_subject = "biologie"
        elif any(w in norm_text for w in ["conscience", "inconscient", "liberté", "morale", "justice", "vérité", "socrate", "descartes", "kant"]):
            canonical_subject = "philosophie"
        elif any(w in norm_text for w in ["poème", "strophe", "vers", "métaphore", "alexandrin", "césaire", "senghor", "camara laye", "hampâté bâ"]):
            canonical_subject = "francais"
        elif any(w in norm_text for w in ["empire du mali", "soundiata", "décolonisation", "guerre", "fleuve niger", "climat"]):
            canonical_subject = "histoire"
        elif user_subject and user_subject.strip().lower() not in {"général", "general", "non défini"}:
            canonical_subject = user_subject.strip().lower()
        else:
            canonical_subject = "mathematiques"

    display_subject = SUBJECT_DISPLAY_NAMES.get(canonical_subject, canonical_subject.capitalize())
    if user_subject and user_subject.strip() and user_subject.strip().lower() not in {"général", "general", "sciences & mathématiques"}:
        display_subject = user_subject.strip()

    # Détection du type de document
    doc_type = "Problème scientifique"
    if canonical_subject in ("francais", "philosophie"):
        if any(w in norm_text for w in ["dissertation", "dans quelle mesure", "pensez-vous que", "partagez-vous"]):
            doc_type = "Dissertation littéraire / philosophique"
        elif any(w in norm_text for w in ["commentaire", "texte ci-dessous", "extrait", "strophe", "vers"]):
            doc_type = "Commentaire de texte littéraire"
        else:
            doc_type = "Étude de texte / Questionnaire"
    elif canonical_subject in ("histoire", "geographie", "histoire-geographie"):
        if any(w in norm_text for w in ["document 1", "document 2", "carte", "source :", "extrait de"]):
            doc_type = "Étude critique de document"
        else:
            doc_type = "Sujet de synthèse / Dissertation"
    elif canonical_subject in ("biologie",):
        if any(w in norm_text for w in ["croisement", "f1", "f2", "parents", "descendance", "mendel"]):
            doc_type = "Problème de génétique"
        elif any(w in norm_text for w in ["schéma", "figure", "légender", "cellule", "microscope"]):
            doc_type = "Étude de schéma / Document cellulaire"
        else:
            doc_type = "Problème scientifique de SVT"

    # Détection précise du chapitre / thème
    topic = "Méthodologie & Résolution"
    if canonical_subject == "mathematiques":
        if any(w in norm_text for w in ["suite", "u_n", "u_{n+1}", "récurrence"]):
            topic = "Suites numériques & Raisonnement par récurrence"
        elif any(w in norm_text for w in ["f(x)", "dériv", "limite", "asymptote", "variation"]):
            topic = "Étude de fonctions, Dérivation & Asymptotes"
        elif any(w in norm_text for w in ["intégrale", "primitive", "aire", "dx"]):
            topic = "Calcul intégral, Primitives & Aires"
        elif any(w in norm_text for w in ["complexe", "imaginaire", "module", "argument", "affixe"]):
            topic = "Nombres complexes & Géométrie dans le plan"
        elif any(w in norm_text for w in ["probab", "dénombrement", "combinaison", "urne", "variable aléatoire"]):
            topic = "Probabilités conditionnelles & Dénombrement"
        elif any(w in norm_text for w in ["vecteur", "droite", "plan", "espace", "produit scalaire"]):
            topic = "Géométrie vectorielle & Produit scalaire"
        elif any(w in norm_text for w in ["pgcd", "congruence", "arithmétique", "premier", "bézout"]):
            topic = "Arithmétique & Congruences"
        else:
            topic = "Algèbre & Résolution d'équations"
    elif canonical_subject in ("physique", "chimie"):
        if any(w in norm_text for w in ["newton", "force", "accélér", "chute libre", "mouvement", "vitesse", "trajectoire"]):
            topic = "Cinématique & Lois de Newton"
        elif any(w in norm_text for w in ["circuit", "rlc", "condensateur", "bobine", "tension", "loi d'ohm"]):
            topic = "Électrocinétique, Circuits RLC & Énergie"
        elif any(w in norm_text for w in ["acide", "base", "ph", "dosage", "titrage", "équivalence"]):
            topic = "Réactions acido-basiques & Dosage volumétrique"
        elif any(w in norm_text for w in ["oxyd", "réduct", "redox", "pile", "électrolyse"]):
            topic = "Oxydoréduction, Piles & Électrolyse"
        elif any(w in norm_text for w in ["ester", "alcool", "acide carboxylique", "organique", "saponification"]):
            topic = "Chimie organique & Réaction d'estérification"
        elif any(w in norm_text for w in ["onde", "lentille", "optique", "fréquence", "diffraction"]):
            topic = "Optique géométrique & Ondes mécaniques"
        elif any(w in norm_text for w in ["noyau", "radioactiv", "demi-vie", "fission"]):
            topic = "Physique nucléaire & Décroissance radioactive"
    elif canonical_subject in ("biologie", "svt"):
        if any(w in norm_text for w in ["crois", "généti", "geneti", "mendel", "allèle", "allele", "dihybridisme", "monohybridisme", "lignée", "f1", "f2", "drosophile", "phénotype", "génotype"]):
            topic = "Génétique mendélienne & Hérédité"
        elif any(w in norm_text for w in ["cellule", "mitose", "méiose", "chromosome", "caryotype", "adn"]):
            topic = "Biologie cellulaire, Mitose & Méiose"
        elif any(w in norm_text for w in ["anticorps", "antigène", "immun", "lymphocyte"]):
            topic = "Immunologie & Défense de l'organisme"
        elif any(w in norm_text for w in ["plante", "photosynthèse", "chlorophylle", "sol"]):
            topic = "Physiologie végétale & Écologie"
    elif canonical_subject == "francais":
        if any(w in norm_text for w in ["poème", "poésie", "vers", "strophe", "alexandrin"]):
            topic = "Commentaire littéraire : Poésie & Rythme"
        elif any(w in norm_text for w in ["roman", "narrateur", "personnage", "récit"]):
            topic = "Analyse littéraire du Roman & Narration"
        elif any(w in norm_text for w in ["théâtre", "didascalie", "réplique", "tragédie"]):
            topic = "Le Texte théâtral & La Représentation"
        else:
            topic = "Méthodologie du Commentaire et de la Dissertation"
    elif canonical_subject == "philosophie":
        if any(w in norm_text for w in ["conscience", "inconscient", "moi", "freud", "descartes"]):
            topic = "La Conscience, l'Inconscient et le Sujet"
        elif any(w in norm_text for w in ["liberté", "déterminisme", "responsabilité"]):
            topic = "La Liberté, la Morale et le Déterminisme"
        elif any(w in norm_text for w in ["état", "justice", "loi", "droit", "politique"]):
            topic = "La Justice, le Droit et l'État"
        elif any(w in norm_text for w in ["vérité", "raison", "science", "démonstration"]):
            topic = "La Vérité, la Raison et la Science"
        else:
            topic = "Dissertation & Analyse conceptuelle philosophique"
    elif canonical_subject in ("histoire", "geographie"):
        if any(w in norm_text for w in ["empire", "soundiata", "mansa", "colonisation", "indépendance", "guerre"]):
            topic = "Histoire du Mali & Dynamiques mondiales contemporaines"
        else:
            topic = "Géographie physique, humaine et aménagement au Mali"

    # Extraction des questions explicites de l'énoncé
    raw_lines = [l.strip() for l in clean_text.split("\n") if l.strip()]
    extracted_questions: List[str] = []
    q_pattern = re.compile(r"^(?:[0-9]{1,2}[\.\)\-]|[a-d]\)|question\s*[0-9]|calculer|démontrer|montrer\s+que|déterminer|en\s+déduire|préciser)\s*(.*)", re.IGNORECASE)
    for line in raw_lines:
        m = q_pattern.match(line)
        if m and len(line) > 10:
            extracted_questions.append(line[:120])
        elif "?" in line and len(line) > 12:
            extracted_questions.append(line[:120])

    # Extraction des nombres et unités
    found_numbers = re.findall(r"\b\d+(?:[.,]\d+)?(?:\s*(?:cm|m|km|s|ms|kg|g|mg|n|j|w|v|a|ma|hz|mol/l|mol|°c|%|fcfa))?\b", clean_text, re.IGNORECASE)
    numbers_snippet = ", ".join(found_numbers[:5]) if found_numbers else "Données littérales / conceptuelles"

    return {
        "canonical_subject": canonical_subject,
        "display_subject": display_subject,
        "document_type": doc_type,
        "topic": topic,
        "extracted_questions": extracted_questions[:4],
        "numbers_snippet": numbers_snippet,
        "first_line": raw_lines[0][:110] if raw_lines else "Énoncé scanné",
    }


# ==============================================================================
# 8. MOTEUR HEURISTIQUE MULTIDISCIPLINAIRE (CONCRET & ADAPTÉ À CHAQUE MATIÈRE)
# ==============================================================================
def generate_heuristic_exercise_guidance(clean_text: str, profile: Dict[str, Any], student_class: str = "11eme") -> Dict[str, Any]:
    """
    Génère une décomposition méthodique rigoureuse et entièrement personnalisée
    en fonction de la matière et du type d'exercice, SANS JAMAIS utiliser de modèle
    générique identique pour tous les documents.
    """
    subj = profile["canonical_subject"]
    topic = profile["topic"]
    disp_subj = profile["display_subject"]
    doc_type = profile["document_type"]
    questions = profile["extracted_questions"]
    first_line = profile["first_line"]
    numbers = profile["numbers_snippet"]

    q1_text = questions[0] if questions else "Résoudre les consignes posées par l'énoncé."
    q2_text = questions[1] if len(questions) > 1 else "Formuler la justification théorique et le calcul exact."

    hints: List[Dict[str, Any]] = []
    summary = ""
    prerequisites: List[str] = []
    final_verification = ""

    # ──────────────────────────────────────────────────────────────────────────
    # A. MATHÉMATIQUES
    # ──────────────────────────────────────────────────────────────────────────
    if subj == "mathematiques":
        if "suite" in topic.lower():
            summary = f"Cet exercice de Mathématiques porte sur les {topic}. Il demande d'étudier le comportement d'une suite (récurrence, sens de variation et limite)."
            prerequisites = [
                "Principe du raisonnement par récurrence (Initialisation, Hérédité, Conclusion)",
                "Étude du signe de u_{n+1} - u_n pour déterminer le sens de variation",
                "Théorème de convergence monotone pour les suites réelles",
            ]
            final_verification = "Vérifie que la limite trouvée est bien cohérente avec les premiers termes calculés (u0, u1, u2)."
            hints = [
                {
                    "step": 1,
                    "type": "observation",
                    "title": "Étape 1 • Analyse des termes initiaux & Nature de la suite",
                    "content": f"Énoncé : « {first_line} ».\nRecherche le premier terme u0 (ou u1) et la relation de récurrence liant u_{{n+1}} à u_n.\nCalcule à la main les deux premiers termes pour anticiper si la suite est croissante ou décroissante.",
                    "question": "Quelle est la valeur du premier terme et quelle conjecture peux-tu formuler sur le sens de variation de la suite ?",
                },
                {
                    "step": 2,
                    "type": "conceptual",
                    "title": "Étape 2 • Démonstration par récurrence",
                    "content": "Rédige rigoureusement les 3 temps indispensables du raisonnement :\n1. Initialisation : montre que la propriété est vraie au rang n = 0.\n2. Hérédité : suppose la propriété vraie au rang k, et démontre qu'elle reste vraie au rang k + 1.\n3. Conclusion : énonce que la propriété est démontrée pour tout entier naturel n.",
                    "question": "Quelle est précisément la proposition P(n) que tu dois poser pour l'hérédité ?",
                },
                {
                    "step": 3,
                    "type": "procedural",
                    "title": "Étape 3 • Étude du sens de variation (u_{n+1} - u_n)",
                    "content": f"Consigne ciblée : « {q1_text} ».\nExprime la différence u_{{n+1}} - u_n en fonction de u_n. Utilise l'inégalité démontrée à l'étape précédente pour fixer le signe de cette différence.\n• Si u_{{n+1}} - u_n > 0 pour tout n, la suite est strictement croissante.",
                    "question": "Quel signe obtiens-tu pour la différence u_{n+1} - u_n sur l'ensemble de définition ?",
                },
                {
                    "step": 4,
                    "type": "solution",
                    "title": "Étape 4 • Convergence & Calcul de la limite ℓ",
                    "content": "Une suite croissante et majorée (ou décroissante et minorée) converge obligatoirement vers une limite finie ℓ.\nRésous l'équation du point fixe f(ℓ) = ℓ issue de la relation de récurrence pour déterminer la valeur exacte de ℓ.",
                    "question": "Quelle valeur finie ℓ obtiens-tu pour la limite de la suite lorsque n tend vers +∞ ?",
                },
            ]
        elif "complexe" in topic.lower():
            summary = "Problème sur les Nombres Complexes : calcul algébrique, module, argument et transformations géométriques."
            prerequisites = [
                "Forme algébrique z = a + ib et conjugué z-barre = a - ib",
                "Module |z| = √(a² + b²) et argument θ = arg(z) modulo 2π",
                "Formule d'Euler et d'Abraham de Moivre : (cos θ + i sin θ)^n = cos(nθ) + i sin(nθ)",
            ]
            final_verification = "Vérifie le signe de cos(θ) et sin(θ) pour t'assurer que l'argument appartient au bon quadrant du plan complexe."
            hints = [
                {
                    "step": 1,
                    "type": "observation",
                    "title": "Étape 1 • Forme algébrique z = a + ib",
                    "content": f"Énoncé : « {first_line} ».\nIsole la partie réelle Re(z) et la partie imaginaire Im(z). Si z est sous forme de fraction, multiplie le numérateur et le dénominateur par le conjugué du dénominateur pour faire disparaître i du dénominateur.",
                    "question": "Quelles sont les valeurs exactes de Re(z) et Im(z) après simplification algébrique ?",
                },
                {
                    "step": 2,
                    "type": "conceptual",
                    "title": "Étape 2 • Calcul du module |z| et de l'argument θ",
                    "content": "Calcule le module : |z| = √(a² + b²).\nFactorise z par son module : z = |z| (a/|z| + i b/|z|).\nIdentifie l'angle θ tel que cos(θ) = a/|z| et sin(θ) = b/|z| en t'aidant du cercle trigonométrique.",
                    "question": "Quel est l'angle θ remarquable associé aux coordonnées trigonométriques obtenues ?",
                },
                {
                    "step": 3,
                    "type": "procedural",
                    "title": "Étape 3 • Résolution d'équation ou transformation géométrique",
                    "content": f"Consigne : « {q1_text} ».\n• Si c'est une équation du second degré az² + bz + c = 0 : calcule le discriminant Δ = b² - 4ac. Si Δ < 0, les racines sont deux complexes conjugués z1, z2 = (-b ± i√|Δ|) / (2a).\n• Si c'est de la géométrie, calcule les distances AB = |zB - zA|.",
                    "question": "Quel est le discriminant Δ et quelles solutions complexes obtiens-tu ?",
                },
                {
                    "step": 4,
                    "type": "solution",
                    "title": "Étape 4 • Interprétation géométrique & Conclusion",
                    "content": "Déduis la nature du triangle ou de la figure géométrique (isocèle, rectangle, équilatéral) d'après les rapports de modules et d'arguments : arg((zC - zA)/(zB - zA)) donne l'angle orienté (AB, AC).",
                    "question": "Quelle est la nature exacte de la figure géométrique formée par les points dans le plan complexe ?",
                },
            ]
        else:
            # Fonctions & Analyse (cas le plus fréquent en 11ème / 12ème)
            summary = f"Exercice d'Analyse mathématique portant sur {topic}. Il s'agit d'étudier les propriétés analytiques et graphiques de la fonction f."
            prerequisites = [
                "Conditions d'existence du domaine Df (dénominateur non nul, argument du logarithme strictement positif)",
                "Règles fondamentales de dérivation : (u·v)' = u'v + uv' et (u/v)' = (u'v - uv')/v²",
                "Signe de la dérivée f'(x) : si f'(x) > 0, f est strictement croissante",
            ]
            final_verification = "Vérifie la cohérence entre les limites aux bornes de Df et les flèches de ton tableau de variations."
            hints = [
                {
                    "step": 1,
                    "type": "observation",
                    "title": "Étape 1 • Domaine de définition Df & Limites aux bornes",
                    "content": f"Énoncé : « {first_line} ».\nDonnées repérées : {numbers}.\n1. Pose les conditions d'existence : dénominateur ≠ 0, intérieur d'une racine ≥ 0, intérieur d'un ln > 0.\n2. Calcule les limites aux bornes de Df en repérant les formes indéterminées éventuelles (0/0, ∞/∞, 0×∞, +∞-∞).",
                    "question": "Quel est l'ensemble de définition Df exact et y a-t-il une valeur interdite à exclure ?",
                },
                {
                    "step": 2,
                    "type": "conceptual",
                    "title": "Étape 2 • Calcul de la dérivée f'(x) & Formule maîtresse",
                    "content": "Identifie la structure de la fonction pour choisir la bonne formule de dérivation :\n• Produit : (u × v)' = u'v + uv'\n• Quotient : (u / v)' = (u'v - uv') / v²\n• Exponentielle : (e^u)' = u' × e^u\n• Logarithme : (ln u)' = u' / u.\nÉcris explicitement les expressions de u(x), v(x) et leurs dérivées.",
                    "question": "Quelle expression développée ou factorisée obtiens-tu pour la dérivée f'(x) ?",
                },
                {
                    "step": 3,
                    "type": "procedural",
                    "title": "Étape 3 • Signe de f'(x) & Tableau de variations complet",
                    "content": f"Consigne : « {q1_text} ».\n1. Résous l'équation f'(x) = 0 pour trouver les extremums locaux.\n2. Étudie le signe de chaque facteur (le dénominateur au carré est toujours strictement positif sur Df).\n3. Dresse le tableau de variations avec la ligne de x, le signe de f'(x) et les flèches de f(x).",
                    "question": "Sur quel(s) intervalle(s) la fonction f est-elle strictement croissante ou strictement décroissante ?",
                },
                {
                    "step": 4,
                    "type": "solution",
                    "title": "Étape 4 • Asymptotes, Tangente & Tracé final",
                    "content": f"Consigne : « {q2_text} ».\n• Asymptote verticale : x = a si lim_{{x→a}} f(x) = ±∞.\n• Asymptote horizontale : y = b si lim_{{x→±∞}} f(x) = b.\n• Équation de la tangente au point d'abscisse x0 : y = f'(x0)(x - x0) + f(x0).",
                    "question": "Quelles sont les équations des éventuelles asymptotes et la conclusion demandée ?",
                },
            ]

    # ──────────────────────────────────────────────────────────────────────────
    # B. PHYSIQUE
    # ──────────────────────────────────────────────────────────────────────────
    elif subj in ("physique", "chimie") and any(w in topic.lower() for w in ["newton", "cinématique", "force", "dynamique", "circuit", "rlc", "optique", "onde", "nucléaire"]):
        if any(w in topic.lower() for w in ["circuit", "rlc", "condensateur", "bobine"]):
            summary = "Exercice d'Électrocinétique : étude de la charge/décharge d'un condensateur ou d'un circuit RLC oscillant."
            prerequisites = [
                "Loi d'Ohm : u_R = R × i",
                "Relation tension-courant d'un condensateur : i = dq/dt = C (du_C/dt)",
                "Loi des mailles et constante de temps τ = R × C",
            ]
            final_verification = "Vérifie que l'unité de la constante de temps τ = RC est bien homogène à des secondes (s)."
            hints = [
                {
                    "step": 1,
                    "type": "observation",
                    "title": "Étape 1 • Schéma du circuit & Conventions électriques",
                    "content": f"Énoncé : « {first_line} ».\nComposants et valeurs : {numbers}.\n1. Trace le schéma du circuit en indiquant le sens conventionnel du courant i.\n2. Flèche les tensions u_C, u_R et la force électromotrice E du générateur en convention récepteur.",
                    "question": "Quels sont les dipôles branchés en série dans la maille et quelle est l'expression de la loi des mailles ?",
                },
                {
                    "step": 2,
                    "type": "conceptual",
                    "title": "Étape 2 • Établissement de l'équation différentielle en u_C(t)",
                    "content": "Applique la loi des mailles : u_R(t) + u_C(t) = E.\nRemplace u_R par R·i, puis remplace i par C·(du_C/dt).\nTu obtiens l'équation différentielle linéaire du 1er ordre : R·C (du_C/dt) + u_C = E.",
                    "question": "Quelle forme canonique prend l'équation différentielle en posant τ = R·C ?",
                },
                {
                    "step": 3,
                    "type": "procedural",
                    "title": "Étape 3 • Résolution & Constante de temps τ",
                    "content": f"Consigne : « {q1_text} ».\nLa solution générale est de la forme u_C(t) = E × (1 - e^(-t/τ)) pour la charge.\nCalcule la valeur numérique de la constante de temps τ = R × C en convertissant les microfarads (µF) en Farads (1 µF = 10^-6 F).",
                    "question": "Quelle valeur numérique obtiens-tu pour la constante de temps τ ?",
                },
                {
                    "step": 4,
                    "type": "solution",
                    "title": "Étape 4 • Énergie emmagasinée & Validation",
                    "content": "Calcule l'énergie maximale emmagasinée dans le condensateur en régime permanent :\nE_C = (1/2) × C × E² (en Joules).\nVérifie que la charge est quasi-complète à t = 5τ (u_C atteint 99% de E).",
                    "question": "Quelle est l'énergie emmagasinée dans le condensateur et que vaut la tension finale ?",
                },
            ]
        else:
            # Mécanique & Newton (majoritaire au Bac malien TSE/TSEXP)
            summary = f"Problème de Mécanique newtonienne ({topic}). Il s'agit d'appliquer les lois du mouvement à un solide en translation."
            prerequisites = [
                "Définition précise du système et du référentiel galiléen",
                "Inventaire des forces extérieures : Poids P = m·g, Réaction normale R, Frottements f",
                "Deuxième loi de Newton (PFD) : Σ F_ext = m · a",
            ]
            final_verification = "Vérifie l'homogénéité des unités (masse en kg, accélération en m·s⁻², force en Newton)."
            hints = [
                {
                    "step": 1,
                    "type": "observation",
                    "title": "Étape 1 • Système d'étude & Référentiel galiléen",
                    "content": f"Énoncé : « {first_line} ».\nGrandeurs et unités repérées : {numbers}.\n1. Précise le système : le solide S de masse m (convertis les grammes en kg : 1 g = 10^-3 kg).\n2. Choisis le référentiel : terrestre supposé galiléen pendant la durée de l'expérience.\n3. Trace le repère orthonormé (O, i, j) aligné avec la trajectoire.",
                    "question": "Quel est le repère d'espace le plus adapté pour projeter les mouvements selon l'axe ?",
                },
                {
                    "step": 2,
                    "type": "conceptual",
                    "title": "Étape 2 • Bilan complet des forces & Schéma clair",
                    "content": "Dresse l'inventaire des forces extérieures appliquées au solide :\n• Le poids P = m·g (toujours vertical, vers le bas)\n• La réaction normale du support R (perpendiculaire au plan de contact)\n• Les forces de frottement éventuelles f (opposées au vecteur vitesse)\n• La tension d'un fil ou d'un ressort T.\nDessine le schéma du solide avec chaque vecteur force orienté correctement.",
                    "question": "Quelles sont les coordonnées du vecteur poids P projeté sur les axes (Ox) et (Oy) ?",
                },
                {
                    "step": 3,
                    "type": "procedural",
                    "title": "Étape 3 • Application de la 2ème loi de Newton (Σ F_ext = m·a)",
                    "content": f"Consigne : « {q1_text} ».\nÉcris la relation vectorielle : P + R + f = m·a.\nProjette cette relation vectorielle sur l'axe du mouvement (Ox) :\n• Si le plan est incliné d'un angle α : m·g·sin(α) - f = m·a_x.\nIsole méthodiquement l'accélération a_x avant tout calcul numérique.",
                    "question": "Quelle formule littérale obtiens-tu pour l'accélération a_x du solide ?",
                },
                {
                    "step": 4,
                    "type": "solution",
                    "title": "Étape 4 • Équations horaires, Calcul de vitesse & Portée",
                    "content": f"Consigne : « {q2_text} ».\nIntègre par rapport au temps t :\n1. Vitesse v(t) = a_x × t + v0.\n2. Position x(t) = (1/2) a_x × t² + v0 × t + x0.\nRéalise l'application numérique avec les valeurs du texte ({numbers}) et encadre ton résultat final avec son unité (m/s ou m).",
                    "question": "Quelle est la valeur numérique calculée pour la vitesse ou la distance parcourue ?",
                },
            ]

    # ──────────────────────────────────────────────────────────────────────────
    # C. CHIMIE (Dosages, pH, Solutions, Redox)
    # ──────────────────────────────────────────────────────────────────────────
    elif subj in ("chimie", "physique"):
        summary = f"Exercice de Chimie ({topic}). Résolution quantitative basée sur la stœchiométrie des réactions en solution aqueuse."
        prerequisites = [
            "Définition de la concentration molaire : C = n / V (avec n en mol et V en L)",
            "Relation à l'équivalence d'un titrage : C_A × V_A = C_B × V_E",
            "Définition du pH : pH = -log[H3O+] et produit ionique de l'eau Ke = [H3O+][OH-] = 10^-14 à 25°C",
        ]
        final_verification = "Vérifie que la concentration trouvée est chimiquement réaliste (souvent comprise entre 10⁻³ et 1 mol/L)."
        hints = [
            {
                "step": 1,
                "type": "observation",
                "title": "Étape 1 • Équation chimique équilibrée de la réaction",
                "content": f"Énoncé : « {first_line} ».\nDonnées chimiques identifiées : {numbers}.\nIdentifie les réactifs : l'espèce titrée dans le bécher et l'espèce titrante dans la burette graduée.\nÉcris l'équation-bilan de la réaction acido-basique ou d'oxydoréduction en vérifiant la conservation des atomes et des charges.",
                "question": "Quelle est l'équation-bilan équilibrée de la réaction chimique étudiée ?",
            },
            {
                "step": 2,
                "type": "conceptual",
                "title": "Étape 2 • Définition de l'équivalence stœchiométrique",
                "content": "Rappelle la définition officielle du programme malien :\nÀ l'équivalence, les réactifs ont été introduits dans les proportions stœchiométriques de l'équation-bilan.\nPour une réaction a A + b B → Produits, la relation fondamentale s'écrit :\nn_A / a = n_B / b soit (C_A × V_A) / a = (C_B × V_E) / b.",
                "question": "Quels sont les coefficients stœchiométriques a et b de la réaction ?",
            },
            {
                "step": 3,
                "type": "procedural",
                "title": "Étape 3 • Calcul littéral & Application numérique de la concentration",
                "content": f"Consigne : « {q1_text} ».\nIsole l'inconnue C_A sous forme littérale avant de calculer :\nC_A = (a / b) × (C_B × V_E / V_A).\nConvertis tous les volumes en Litres (1 mL = 10^-3 L) ou conserve-les en mL si les deux volumes se simplifient.",
                "question": "Quelle valeur numérique obtiens-tu pour la concentration molaire C_A (en mol/L) ?",
            },
            {
                "step": 4,
                "type": "solution",
                "title": "Étape 4 • Choix de l'indicateur coloré & Conclusion",
                "content": f"Consigne : « {q2_text} ».\n• Pour un dosage acide fort / base forte : le pH à l'équivalence vaut 7 à 25°C (le bleu de bromothymol BBT est l'indicateur idéal).\n• Pour un acide faible dosé par une base forte : le pH à l'équivalence est basique (pH_E > 7, la phénolphtaléine convient).",
                "question": "Quel indicateur coloré convient pour ce dosage et pourquoi sa zone de virage est-elle adaptée ?",
            },
        ]

    # ──────────────────────────────────────────────────────────────────────────
    # D. SVT / BIOLOGIE (Génétique, Cellule, Immunologie)
    # ──────────────────────────────────────────────────────────────────────────
    elif subj in ("biologie", "svt"):
        summary = f"Exercice de Sciences de la Vie et de la Terre (SVT) portant sur {topic}. Analyse des mécanismes du vivant et interprétation génétique."
        prerequisites = [
            "Lois de Mendel : uniformité des hybrides de première génération (F1)",
            "Définition des allèles dominants (notés en majuscule) et récessifs (en minuscule)",
            "Échiquier de croisement et calcul des fréquences phénotypiques et génotypiques",
        ]
        final_verification = "Vérifie que la somme des proportions de ton échiquier de croisement est bien égale à 1 (ou 16/16 ou 100%)."
        hints = [
            {
                "step": 1,
                "type": "observation",
                "title": "Étape 1 • Analyse des parents et de la descendance F1",
                "content": f"Énoncé : « {first_line} ».\nDonnées phénotypiques relevées : {numbers}.\n1. Compare le phénotype des parents de lignée pure (P1 × P2).\n2. Analyse les individus de la génération F1 : s'ils présentent tous le même phénotype parental, la 1ère loi de Mendel est vérifiée.\n3. Déduis l'allèle dominant et l'allèle récessif.",
                "question": "Quel allèle est dominant et quel allèle est récessif selon les résultats de la génération F1 ?",
            },
            {
                "step": 2,
                "type": "conceptual",
                "title": "Étape 2 • Définition de la notation & Génotypes parentaux",
                "content": "Adopte une notation génétique conventionnelle claire :\n• Allèle dominant : lettre majuscule (ex: [B] pour Brun)\n• Allèle récessif : lettre minuscule (ex: [b] pour blanc).\nÉcris les génotypes des parents purs : (B // B) et (b // b).\nDétermine les types de gamètes produits par méiose : 100% de gamètes (B) et 100% de gamètes (b).",
                "question": "Quel est le génotype exact des hybrides de première génération F1 ?",
            },
            {
                "step": 3,
                "type": "procedural",
                "title": "Étape 3 • Construction de l'échiquier de croisement (F2 ou Test-Cross)",
                "content": f"Consigne : « {q1_text} ».\nTrace le tableau de croisement à double entrée :\n• Place les gamètes du premier parent en colonnes avec leurs proportions (1/2, 1/2 pour un monohybridisme ou 1/4 × 4 pour un dihybridisme).\n• Place les gamètes du second parent en lignes.\n• Remplis chaque case avec le génotype combiné et écris le phénotype résultant entre crochets.",
                "question": "Quelles sont les fréquences phénotypiques théoriques obtenues dans les cases de l'échiquier ?",
            },
            {
                "step": 4,
                "type": "solution",
                "title": "Étape 4 • Confrontation aux effectifs réels & Conclusion génétique",
                "content": f"Consigne : « {q2_text} ».\nCalcule les pourcentages réels des individus dénombrés dans l'exercice ({numbers}).\nConfronte les ratios observés aux ratios théoriques mendéliens :\n• Si ratio 3/4 [dominant] et 1/4 [récessif] : monohybridisme avec dominance complète.\n• Si ratio 9/16, 3/16, 3/16, 1/16 : dihybridisme avec gènes indépendants portés par des chromosomes distincts.",
                "question": "Les résultats réels confirment-ils l'hypothèse de gènes indépendants ou de gènes liés (linkage) ?",
            },
        ]

    # ──────────────────────────────────────────────────────────────────────────
    # E. FRANÇAIS & LITTÉRATURE (Commentaire composé, Analyse de texte, Dissertation)
    # ──────────────────────────────────────────────────────────────────────────
    elif subj in ("francais", "lettres"):
        summary = f"Exercice de Français / Littérature portant sur {topic} ({doc_type}). Démarche d'analyse stylistique et de rédaction argumentée."
        prerequisites = [
            "Distinction fond et forme : tout procédé stylistique produit un effet de sens précis",
            "Repérage des figures de style majeures (métaphores, comparaisons, anaphores, hyperboles)",
            "Structure du commentaire en 2 ou 3 axes de lecture progressifs",
        ]
        final_verification = "Vérifie que chaque sous-partie contient au moins une citation exacte du texte entre guillemets avec son analyse stylistique."
        hints = [
            {
                "step": 1,
                "type": "observation",
                "title": "Étape 1 • Lecture méthodique, Genre & Tonalité dominante",
                "content": f"Texte scanné : « {first_line} ».\n1. Identifie l'auteur, le titre de l'œuvre et le contexte littéraire (ex: mouvement de la Négritude, Romantisme, Poésie engagée).\n2. Repère la forme du texte : poème en vers (alexandrins, rimes) ou prose narrative/théâtrale.\n3. Caractérise le registre dominant : lyrique, tragique, satirique, polémique ou épique.",
                "question": "Quelle est l'idée directrice ou le sentiment central qui traverse tout l'extrait ?",
            },
            {
                "step": 2,
                "type": "conceptual",
                "title": "Étape 2 • Élaboration de la problématique & Des deux axes de lecture",
                "content": "Construis un projet de lecture dynamique sous forme de question directrice.\nDéfinis deux axes de lecture complémentaires :\n• Axe 1 (La surface / le thème immédiat) : description du réel, peinture de la douleur ou évocation du cadre africain.\n• Axe 2 (La portée symbolique / le sens profond) : célébration de l'identité, combat politique ou transcendance poétique.",
                "question": "Quels sont les deux titres d'axes que tu choisis pour structurer ton analyse ?",
            },
            {
                "step": 3,
                "type": "procedural",
                "title": "Étape 3 • Analyse stylistique détaillée : Citations & Procédés",
                "content": f"Consigne : « {q1_text} ».\nApplique la règle d'or : Citation → Identification du procédé → Analyse du sens produit.\n• Relève les champs lexicaux dominants.\n• Analyse les figures de style : métaphores, anaphores, personnifications.\n• Étudie le rythme des phrases, la ponctuation et le choix des temps verbaux.",
                "question": "Quelle figure de style ou choix de vocabulaire marquant illustre le mieux ton premier axe ?",
            },
            {
                "step": 4,
                "type": "solution",
                "title": "Étape 4 • Rédaction de la conclusion & Ouverture littéraire",
                "content": f"Consigne : « {q2_text} ».\nRédige la conclusion en deux temps obligatoires :\n1. Bilan synthétique : rappelle comment les deux axes ont permis de résoudre la problématique posée.\n2. Ouverture littéraire : crée un écho avec un autre auteur du programme officiel (ex: Léopold Sédar Senghor, Aimé Césaire, Amadou Hampâté Bâ).",
                "question": "Vers quelle autre œuvre littéraire du programme proposes-tu d'ouvrir ta conclusion ?",
            },
        ]

    # ──────────────────────────────────────────────────────────────────────────
    # F. PHILOSOPHIE
    # ──────────────────────────────────────────────────────────────────────────
    elif subj == "philosophie":
        summary = f"Sujet de Philosophie portant sur {topic}. Problématisation conceptuelle, analyse dialectique et synthèse critique."
        prerequisites = [
            "Définition précise et distinction des notions philosophiques au cœur du sujet",
            "Mise au jour du paradoxe : pourquoi la question posée fait-elle problème ?",
            "Démarche dialectique : Thèse (opinion/évidence) → Antithèse (critique/rupture) → Synthèse (dépassement conceptuel)",
        ]
        final_verification = "Vérifie que ta réflexion ne se contente pas de donner ton avis personnel, mais mobilise des arguments conceptuels solides."
        hints = [
            {
                "step": 1,
                "type": "observation",
                "title": "Étape 1 • Analyse conceptuelle des notions & Problématisation",
                "content": f"Sujet scanné : « {first_line} ».\n1. Analyse chaque mot du sujet (le sens commun, le sens philosophique et l'étymologie).\n2. Formule le paradoxe : si la première réponse semble évidente, quelle contradiction ou difficulté surgit dès qu'on approfondit la réflexion ?\n3. Rédige la problématique sous forme d'une interrogation fondamentale.",
                "question": "Quelle est la contradiction fondamentale ou la tension philosophique contenue dans ce sujet ?",
            },
            {
                "step": 2,
                "type": "conceptual",
                "title": "Étape 2 • Première partie (Thèse) : L'évidence ou la thèse classique",
                "content": "Développe la première thèse qui vient à l'esprit ou qui représente la position classique.\nStructure ton argumentation en 2 ou 3 sous-arguments logiques.\nMobilise un auteur de référence pour légitimer la réflexion (ex: Descartes sur le doute méthodique, Platon sur l'illusion des sens, Hobbes sur l'État souverain).",
                "question": "Quel philosophe et quel argument majeur soutiennent cette première approche ?",
            },
            {
                "step": 3,
                "type": "procedural",
                "title": "Étape 3 • Deuxième partie (Antithèse) : La critique philosophique",
                "content": f"Consigne : « {q1_text} ».\nMarque une transition critique : montre les limites, les dangers ou les impasses de la première thèse.\nDéploie l'antithèse en changeant de perspective conceptuelle (ex: oppose le déterminisme inconscient de Freud à la liberté sartrienne, ou la critique marxiste de l'État bourgeois).",
                "question": "Quelle objection décisive vient renverser la première thèse développée ?",
            },
            {
                "step": 4,
                "type": "solution",
                "title": "Étape 4 • Troisième partie (Synthèse) & Conclusion définitive",
                "content": f"Consigne : « {q2_text} ».\nLa synthèse n'est pas un simple compromis mou ('un peu des deux'), mais un dépassement philosophique :\nRedéfinis les notions pour montrer à quelles conditions concrètes ou éthiques le problème posé trouve une solution éclairée.\nConclus en répondant nettement et sans hésitation à la question initiale du sujet.",
                "question": "Quelle réponse finale argumentée apportes-tu pour résoudre définitivement la problématique ?",
            },
        ]

    # ──────────────────────────────────────────────────────────────────────────
    # G. HISTOIRE-GÉOGRAPHIE
    # ──────────────────────────────────────────────────────────────────────────
    else:
        summary = f"Exercice d'Histoire-Géographie portant sur {topic} ({doc_type}). Analyse documentaire critique et restitution de connaissances."
        prerequisites = [
            "Contextualisation précise : repères chronologiques en Histoire, échelles d'analyse en Géographie",
            "Méthode critique : confrontation des sources et distinction faits réels / interprétations",
            "Connaissance du programme malien et africain (empires historiques, fleuve Niger, décolonisation)",
        ]
        final_verification = "Vérifie que tu as bien daté les événements clés et localisé géographiquement les espaces mentionnés."
        hints = [
            {
                "step": 1,
                "type": "observation",
                "title": "Étape 1 • Présentation du document & Contexte historique/spatial",
                "content": f"Document scanné : « {first_line} ».\nPrésente les 4 éléments d'identification fondamentaux :\n1. Nature : discours, traité officiel, carte géographique, tableau statistique ou article de presse.\n2. Auteur et fonction au moment des faits.\n3. Date et contexte historique (ou période géographique).\n4. Thème principal traité.",
                "question": "Quel est le contexte historique ou l'enjeu spatial précis dans lequel ce document a été rédigé ?",
            },
            {
                "step": 2,
                "type": "conceptual",
                "title": "Étape 2 • Décodage des informations & Confrontation aux cours",
                "content": "Ne te contente pas de paraphraser le document.\nPour chaque fait ou donnée mentionnée dans le texte ({numbers}), apporte une explication issue de tes connaissances de cours (causes profondes, chiffres clés du programme, acteurs politiques ou économiques).",
                "question": "Quels événements ou notions clés de ton cours éclairent directement ce document ?",
            },
            {
                "step": 3,
                "type": "procedural",
                "title": "Étape 3 • Analyse critique des causes & Des conséquences",
                "content": f"Consigne : « {q1_text} ».\nStructure l'explication autour de la chaîne causale :\n• Causes immédiates et facteurs structurels à long terme.\n• Répercussions directes sur les populations, les frontières ou l'économie nationale.",
                "question": "Quelles sont les répercussions majeures de l'événement ou du phénomène étudié ?",
            },
            {
                "step": 4,
                "type": "solution",
                "title": "Étape 4 • Synthèse générale & Portée historique / géographique",
                "content": f"Consigne : « {q2_text} ».\nFormule le bilan global de l'analyse :\nQuelle est la portée historique durable du document ou quel enseignement géographique majeur en tire-t-on pour l'aménagement du territoire et le développement du Mali ?",
                "question": "Quelle est la portée finale de ce document dans l'histoire ou la géographie du continent ?",
            },
        ]

    return {
        "status": "success",
        "is_valid": True,
        "subject": disp_subj,
        "class": student_class,
        "topic": topic,
        "document_type": doc_type,
        "summary": summary,
        "prerequisites": prerequisites,
        "hints": hints,
        "final_verification": final_verification,
        "source": "heuristic_curriculum_engine",
    }

_LLM_LAST_FAILURE_TIME: float = 0.0


# ==============================================================================
# 9. ANALYSE PÉDAGOGIQUE IA PROFONDE AVEC DÉCOMPOSITION SOCRATIQUE (LLM)
# ==============================================================================
async def generate_ai_exercise_guidance(clean_text: str, profile: Dict[str, Any], student_class: str = "11eme") -> Optional[Dict[str, Any]]:
    """
    Sollicite le client LLM (Groq / Gemini / Qwen local) avec un prompt d'élite
    pour inspecter en profondeur l'énoncé scanné et produire des consignes concrètes.
    Retourne la décomposition JSON si le modèle répond avec succès dans un délai imparti.
    """
    global _LLM_LAST_FAILURE_TIME
    from backend.src.services.orchestrator_service import get_orchestrator

    now = time.time()
    # Si le LLM a échoué récemment (clés API expirées ou hors-ligne), bascule immédiate
    # sur le moteur heuristique expert pour garantir une latence sous 10ms.
    if (now - _LLM_LAST_FAILURE_TIME) < 60.0:
        return None

    disp_subj = profile["display_subject"]
    topic = profile["topic"]
    doc_type = profile["document_type"]

    system_prompt = (
        "Tu es AlternIA, le professeur tuteur d'élite et mentor pédagogique pour les élèves du Mali "
        f"(programme officiel du secondaire en classe de {student_class}).\n"
        "L'élève a pris en photo son véritable exercice scolaire. Ton rôle est de lui expliquer exactement "
        "la démarche et de lui dicter ce qu'il doit concrètement faire et écrire sur sa feuille, sans jamais lui "
        "donner une réponse stéréotypée ou abstraite.\n\n"
        "RÈGLES D'OR STRICTES :\n"
        "1. Analyse en profondeur les données réelles de l'énoncé : cite les vraies fonctions, équations, réactifs, "
        "valeurs numériques ou textes de l'extrait.\n"
        "2. Fournis 3 à 4 étapes progressives numérotées.\n"
        "3. Pour chaque étape, dis-lui explicitement : « Ce que tu dois faire : ... » avec la formule ou la règle exacte.\n"
        "4. Pose une question de réflexion socratique pour qu'il trouve par lui-même la réponse intermédiaire.\n"
        "5. Retourne STRICTEMENT un objet JSON valide, sans texte d'introduction ni balises superflues."
    )

    user_prompt = f"""Analyse cet énoncé scolaire scanné :
        Matière : {disp_subj}
        Chapitre pressenti : {topic}
        Type de document : {doc_type}
        Classe : {student_class}

        Texte extrait de l'exercice :
        \"\"\"
        {clean_text[:1800]}
        \"\"\"

        Génère la décomposition pédagogique au format JSON pur :
        {{
        "subject": "{disp_subj}",
        "topic": "{topic}",
        "document_type": "{doc_type}",
        "summary": "Résumé en 2 phrases de ce qui est concrètement demandé dans l'énoncé.",
        "prerequisites": ["Théorème ou formule 1", "Règle 2"],
        "hints": [
        {{
            "step": 1,
            "type": "observation",
            "title": "Étape 1 • Titre direct et concret spécifique à cet énoncé",
            "content": "Explication pédagogique détaillée avec les formules et données de l'exercice.",
            "question": "Question socratique ciblée guidant l'élève vers le résultat."
        }},
        {{
            "step": 2,
            "type": "conceptual",
            "title": "Étape 2 • Titre concret",
            "content": "Explication et formule maîtresse.",
            "question": "Question de guidage."
        }},
        {{
            "step": 3,
            "type": "procedural",
            "title": "Étape 3 • Procédure de calcul ou de rédaction",
            "content": "Ce que l'élève doit écrire étape par étape sur sa copie.",
            "question": "Question de vérification intermédiaire."
        }},
        {{
            "step": 4,
            "type": "solution",
            "title": "Étape 4 • Synthèse & Validation du résultat",
            "content": "Vérification de cohérence et encadrement du résultat.",
            "question": "Question finale."
        }}
        ],
        "final_verification": "Astuce concrète pour vérifier l'exactitude du résultat avant de rendre la copie."
        }}"""

    try:
        orch = get_orchestrator()
        llm = orch.llm_client
        if not llm:
            return None

        # Pour le scanner d'exercices, on sollicite exclusivement les LLM Cloud rapides (Groq / Gemini < 2s).
        # Si seul le modèle GGUF local est disponible ou si le Cloud échoue (ex: 401),
        # le moteur heuristique expert prend le relais instantanément (< 5ms) sans saturer le CPU.
        if "local" in llm.__class__.__name__.lower():
            return None

        detached = []
        curr = llm
        while curr:
            fb = getattr(curr, "fallback_client", None)
            if fb and "local" in fb.__class__.__name__.lower():
                setattr(curr, "fallback_client", None)
                detached.append((curr, fb))
            curr = fb

        raw_res = None
        try:
            loop = asyncio.get_running_loop()
            raw_res = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: llm.generate(
                        prompt=user_prompt,
                        system_prompt=system_prompt,
                        temperature=0.2,
                        max_tokens=450,
                    )
                ),
                timeout=3.5
            )
        finally:
            # Restauration garantie de la chaîne de secours
            for node, fb in detached:
                setattr(node, "fallback_client", fb)

        if not raw_res or not raw_res.strip():
            _LLM_LAST_FAILURE_TIME = time.time()
            return None

        # Nettoyage et extraction robuste du JSON
        cleaned = re.sub(r"```(?:json)?\s*", "", raw_res)
        cleaned = re.sub(r"```\s*", "", cleaned)
        cleaned = re.sub(r"//.*", "", cleaned)
        cleaned = re.sub(r",\s*([\]}])", r"\1", cleaned)

        json_match = re.search(r"\{[\s\S]*\}", cleaned)
        if json_match:
            parsed = json.loads(json_match.group(0), strict=False)
            hints = parsed.get("hints", [])
            if isinstance(hints, list) and len(hints) >= 2:
                # Normalisation des hints
                formatted_hints: List[Dict[str, Any]] = []
                for i, h in enumerate(hints):
                    if isinstance(h, dict):
                        text_val = str(h.get("content") or h.get("text") or "Explication en cours.")
                        formatted_hints.append({
                            "step": int(h.get("step") or (i + 1)),
                            "type": str(h.get("type") or "procedural"),
                            "title": str(h.get("title") or f"Étape {i + 1} • Méthode"),
                            "content": text_val,
                            "text": text_val,
                            "question": str(h.get("question") or "Quelle est ton hypothèse pour cette étape ?"),
                        })

                if formatted_hints:
                    return {
                        "status": "success",
                        "is_valid": True,
                        "subject": str(parsed.get("subject") or disp_subj),
                        "class": student_class,
                        "topic": str(parsed.get("topic") or topic),
                        "document_type": str(parsed.get("document_type") or doc_type),
                        "summary": str(parsed.get("summary") or ""),
                        "prerequisites": [str(p) for p in parsed.get("prerequisites", []) if isinstance(p, str)],
                        "hints": formatted_hints,
                        "final_verification": str(parsed.get("final_verification") or ""),
                        "source": "ai_llm_engine",
                    }
    except asyncio.TimeoutError:
        _LLM_LAST_FAILURE_TIME = time.time()
        logger.info("⚡ [OCR Exercise] Timeout LLM dépassé -> activation instantanée du moteur heuristique expert.")
    except Exception as e:
        _LLM_LAST_FAILURE_TIME = time.time()
        logger.warning(f"Note génération IA exercice (secours automatique activé) : {e}")

    return None


# ==============================================================================
# 10. PIPELINE COMPLET D'ANALYSE D'EXERCICES (POINT D'ENTRÉE MAÎTRE)
# ==============================================================================
async def analyze_and_decompose_exercise(
    image_bytes: Optional[bytes] = None,
    text: Optional[str] = None,
    filename: str = "document.jpg",
    student_class: str = "11eme",
    subject_hint: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Point d'entrée maître pour le traitement réel des exercices scolaires :
    1. OCR haute fidélité si une image est fournie.
    2. Contrôle de lisibilité et filtrage des reçus/documents hors programme.
    3. Classification disciplinaire experte (Mali DEF/Lycée).
    4. Tentative d'analyse approfondie par LLM (Groq / Gemini / Local).
    5. Fallback immédiat sur le moteur heuristique multidisciplinaire spécialisé.
    """
    from backend.src.services.orchestrator_service import normalize_student_class
    norm_class = normalize_student_class(student_class or "11eme")

    extracted_text = (text or "").strip()

    # 1. OCR si des octets d'image ou PDF sont transmis
    if image_bytes and len(image_bytes) > 0:
        try:
            loop = asyncio.get_running_loop()
            ocr_res = await loop.run_in_executor(
                None,
                lambda: perform_ocr_on_image(image_bytes, filename=filename)
            )
            if ocr_res and ocr_res.strip():
                extracted_text = ocr_res.strip() if not extracted_text else f"{extracted_text}\n" + ocr_res.strip()
        except Exception as ocr_err:
            logger.warning(f"Erreur pendant l'extraction OCR : {ocr_err}")

    # 2. Validation académique du document
    is_valid, status, err_topic, err_msg = is_valid_academic_document(extracted_text)
    if not is_valid:
        return {
            "status": status,
            "is_valid": False,
            "subject": "Illisible" if status == "unreadable" else "Document non académique",
            "class": norm_class,
            "topic": err_topic,
            "extracted_text": extracted_text,
            "message": err_msg,
            "hints": [],
        }

    # 3. Profilage disciplinaire du document
    profile = detect_exercise_curriculum_profile(extracted_text, user_subject=subject_hint)

    # 4. Tentative d'analyse pédagogique par le LLM
    ai_result = await generate_ai_exercise_guidance(extracted_text, profile, student_class=norm_class)
    if ai_result:
        ai_result["extracted_text"] = extracted_text
        ai_result["message"] = f"Exercice analysé avec succès en {ai_result['subject']} ({ai_result['topic']})."
        return ai_result

    # 5. Moteur heuristique expert multidisciplinaire en secours haute performance
    heuristic_res = generate_heuristic_exercise_guidance(extracted_text, profile, student_class=norm_class)
    heuristic_res["extracted_text"] = extracted_text
    heuristic_res["message"] = f"Exercice analysé avec succès en {heuristic_res['subject']} ({heuristic_res['topic']})."

    # Duplication de content dans text pour rétrocompatibilité totale
    for h in heuristic_res["hints"]:
        h["text"] = h["content"]

    return heuristic_res

