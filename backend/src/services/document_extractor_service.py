"""
Service d'extraction de texte à partir de documents de cours importés (Module E : Podcasts).
Prend en charge : PDF, DOCX (Word), PPTX (PowerPoint), TXT et Markdown.
Extraction robuste et sécurisée avec gestion des erreurs et limites de taille.
"""

import io
import logging
import os
import re
import xml.etree.ElementTree as ET
import zipfile
from typing import Tuple

logger = logging.getLogger("AlternIA.DocumentExtractor")

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 Mo max
EXTENSIONS_AUTORISEES = {".pdf", ".docx", ".pptx", ".txt", ".md"}


def valider_fichier_cours(filename: str, taille_octets: int):
    """Valide l'extension et la taille du fichier importé."""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in EXTENSIONS_AUTORISEES:
        raise ValueError(
            f"Format de fichier non pris en charge ({ext}). Formats acceptés : PDF, Word (.docx), PowerPoint (.pptx), TXT."
        )
    if taille_octets > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            f"Fichier trop volumineux ({taille_octets / (1024*1024):.1f} Mo). La limite est de 25 Mo."
        )
    if taille_octets == 0:
        raise ValueError("Le fichier importé est vide.")


def extraire_texte_document(filename: str, contenu_bytes: bytes) -> str:
    """
    Extrait le contenu textuel d'un document scolaire importé.
    """
    valider_fichier_cours(filename, len(contenu_bytes))
    ext = os.path.splitext(filename)[1].lower()

    if ext in {".txt", ".md"}:
        try:
            return contenu_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return contenu_bytes.decode("latin-1", errors="replace")

    elif ext == ".pdf":
        return _extraire_texte_pdf(contenu_bytes)

    elif ext == ".docx":
        return _extraire_texte_docx(contenu_bytes)

    elif ext == ".pptx":
        return _extraire_texte_pptx(contenu_bytes)

    else:
        raise ValueError(f"Extension non gérée : {ext}")


def _extraire_texte_pdf(contenu_bytes: bytes) -> str:
    """Extraction à partir d'un PDF via pypdf."""
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(contenu_bytes))
        pages_textes = []
        for idx, page in enumerate(reader.pages):
            texte_page = page.extract_text() or ""
            if texte_page.strip():
                pages_textes.append(texte_page.strip())

        texte_complet = "\n\n".join(pages_textes).strip()
        if not texte_complet:
            raise ValueError("Le document PDF ne contient aucun texte extractible (possible document scanné ou image).")
        return texte_complet
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        logger.error(f"Erreur extraction PDF : {e}")
        raise ValueError(f"Impossible de lire le document PDF : {e}")


def _extraire_texte_docx(contenu_bytes: bytes) -> str:
    """Extraction XML native à partir d'un fichier Word (.docx)."""
    try:
        with zipfile.ZipFile(io.BytesIO(contenu_bytes)) as z:
            if "word/document.xml" not in z.namelist():
                raise ValueError("Structure Word (.docx) invalide ou corrompue.")
            xml_content = z.read("word/document.xml")
            root = ET.fromstring(xml_content)
            # Namespace WordprocessingML
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            text_nodes = root.findall(".//w:t", ns)
            textes = [node.text for node in text_nodes if node.text]
            texte_final = " ".join(textes).strip()
            if not texte_final:
                raise ValueError("Le document Word ne contient aucun texte rédigé.")
            return texte_final
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        logger.error(f"Erreur extraction DOCX : {e}")
        raise ValueError(f"Erreur lors de la lecture du document Word : {e}")


def _extraire_texte_pptx(contenu_bytes: bytes) -> str:
    """Extraction XML native à partir d'un fichier PowerPoint (.pptx)."""
    try:
        with zipfile.ZipFile(io.BytesIO(contenu_bytes)) as z:
            slide_names = sorted([f for f in z.namelist() if re.match(r"^ppt/slides/slide\d+\.xml$", f)])
            if not slide_names:
                raise ValueError("Structure PowerPoint (.pptx) invalide : aucune diapositive trouvée.")

            diapo_textes = []
            ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
            for sname in slide_names:
                xml_content = z.read(sname)
                root = ET.fromstring(xml_content)
                text_nodes = root.findall(".//a:t", ns)
                morceaux = [node.text for node in text_nodes if node.text]
                if morceaux:
                    diapo_textes.append(" ".join(morceaux))

            texte_final = "\n\n".join(diapo_textes).strip()
            if not texte_final:
                raise ValueError("La présentation PowerPoint ne contient aucun texte extractible.")
            return texte_final
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        logger.error(f"Erreur extraction PPTX : {e}")
        raise ValueError(f"Erreur lors de la lecture du fichier PowerPoint : {e}")
