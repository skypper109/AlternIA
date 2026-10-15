from pathlib import Path

from alternia.config.settings import PROJECT_ROOT
from alternia.core.models import StudentClass, Subject
from alternia.indexing.document_registry import DocumentRegistry
from alternia.ingestion.loaders.pdf import PDFDocumentLoader
from alternia.ingestion.metadata.document_parser import (
    DocumentStructureParser,
)
from alternia.ingestion.metadata.structure_detector import (
    StructureDetector,
)
from alternia.ingestion.metadata.subject_resolver import (
    SubjectResolver,
)
from alternia.ingestion.chunking.pedagogical_chunker import (
    PedagogicalChunker,
)
from alternia.rag.embeddings import EmbeddingService
from alternia.rag.embeddings import EmbeddingService
from alternia.rag.indexer import KnowledgeIndexer
from alternia.rag.qdrant_vector_store import QdrantVectorStore


KNOWLEDGE_BASE = (
    PROJECT_ROOT / "knowledge-base"
)

INDEX_DIRECTORY = (
    PROJECT_ROOT
    / "ai-engine"
    / "data"
    / "index"
)

QDRANT_STORAGE_PATH = (
    PROJECT_ROOT
    / "ai-engine"
    / "data"
    / "qdrant"
)

VECTOR_STORE_PATH = (
    INDEX_DIRECTORY
    / "vector_store.json"
)

DOCUMENT_REGISTRY_PATH = (
    INDEX_DIRECTORY
    / "document_registry.json"
)


# =============================================================
# DÉTECTION MÉTADONNÉES
# =============================================================

import re

def detect_series(
    path: Path,
) -> str:
    """
    Détecte la filière / série d'après le chemin ou le nom du fichier PDF.
    Exemples :
    Fondamental (6e-9e) & 10ème : 'generale' (Tronc Commun)
    11ème : '11s' (Sciences), '11l' (Lettres), '11seco' (Économie/Tertiaire), 'generale'
    12ème : 'tse' (Sciences Exactes), 'tsexp' (Sciences Expérimentales), 'tseco' (Sciences Éco), 'tss' (Sciences Sociales), 'tll' (Lettres), 'generale'
    """
    path_str = str(path).lower()
    stem = path.stem.lower()

    # Fondamental (6e, 7e, 8e, 9e) & 10ème -> Tronc Commun / Général
    if any(k in path_str for k in ["fondamental", "6eme", "6e", "7eme", "7e", "8eme", "8e", "9eme", "9e", "10eme", "10e", "def"]):
        return "generale"

    # 12ème / Terminale
    if "12eme" in path_str or "12e" in path_str:
        if re.search(r"\btsexp\b|expérimentale|experimentale", stem + " " + path_str):
            return "tsexp"
        if re.search(r"\btseco\b|economie|économie", stem + " " + path_str):
            return "tseco"
        if re.search(r"\btss\b|sociale|sociologie", stem + " " + path_str):
            return "tss"
        if re.search(r"\btll\b|linguistique|littéraire|litteraire", stem + " " + path_str):
            return "tll"
        if re.search(r"\btse\b", stem + " " + path_str):
            return "tse"
        if "francais" in path_str:
            return "tll"
        if "physique" in path_str or "chimie" in path_str:
            return "tse_tsexp"
        if "biologie" in path_str or "svt" in path_str:
            return "tsexp"
        return "generale"

    # 11ème
    if "11eme" in path_str or "11e" in path_str:
        if re.search(r"\bte\b|\bseco\b|economie|économie|tertiaire", stem + " " + path_str):
            return "11seco"
        if re.search(r"\b11l\b|\bsh\b|\bll\b|lettre", stem + " " + path_str):
            return "11l"
        if re.search(r"\b11s\b|science|sces|biologie|chimie|physique|svt", stem + " " + path_str):
            return "11s"
        return "generale"

    return "generale"


def detect_class(
    path: Path,
) -> StudentClass:
    """
    Détecte la classe depuis le chemin ou nom du PDF.
    Supporte 6ème à 9ème (fondamental) et 10ème à 12ème (lycée).
    """
    stem = path.stem.lower()

    # 1. Vérification dans les parties du chemin (du plus spécifique au plus général)
    for part in reversed(path.parts[:-1]):
        normalized = part.lower().strip()
        c = StudentClass.from_str(normalized)
        if c:
            return c

    # 2. Vérification dans le nom de fichier (stem)
    if re.search(r"\b6[-_]?e(me)?\b", stem) or "6-eme" in stem or "6eme" in stem:
        return StudentClass.SIX
    if re.search(r"\b7[-_]?e(me)?\b", stem) or "7-eme" in stem or "7eme" in stem:
        return StudentClass.SEVEN
    if re.search(r"\b8[-_]?e(me)?\b", stem) or "8-eme" in stem or "8eme" in stem:
        return StudentClass.EIGHT
    if re.search(r"\b9[-_]?e(me)?\b", stem) or "9-eme" in stem or "9eme" in stem or "9e-annee" in stem or "def" in stem:
        return StudentClass.NINE
    if re.search(r"\b10[-_]?e(me)?\b", stem) or "10-eme" in stem or "10eme" in stem:
        return StudentClass.TEN
    if re.search(r"\b11[-_]?e(me)?\b", stem) or "11-eme" in stem or "11eme" in stem:
        return StudentClass.ELEVEN
    if re.search(r"\b12[-_]?e(me)?\b", stem) or "12-eme" in stem or "12eme" in stem or "terminale" in stem or "bac" in stem:
        return StudentClass.TWELVE

    raise ValueError(
        f"Classe impossible à déterminer : {path}"
    )


def detect_subject(
    path: Path,
) -> Subject:
    """
    Détecte la matière depuis le chemin ou le nom du PDF.
    Gère les dossiers explicites (10eme/sciences) ainsi que
    les annales et manuels fondamentaux sans sous-dossier de matière.
    """
    path_str = str(path).lower()
    stem = path.stem.lower()

    # 1. Recherche par dossiers (chemin)
    for part in reversed(path.parts[:-1]):
        normalized = part.lower().strip()
        if normalized in {"pdf", "fondamental", "raw", "processed", "index"}:
            continue
        subj = Subject.from_str(normalized)
        if subj and subj not in {Subject.AUTRE, Subject.SCIENCES}:
            return subj

    # 2. Analyse ciblée du nom de fichier (stem) avec expressions régulières
    text = f"{stem} {path_str}".replace("-", " ").replace("_", " ")

    if re.search(r"\bagriculture\b|\bagri\b", text):
        return Subject.AGRICULTURE

    if re.search(r"\becm\b|\becms\b|\bcivique\b|\bmorale\b", text):
        return Subject.ECM

    if re.search(r"\bdessin\b|\barts?\b", text):
        return Subject.DESSIN

    if re.search(r"\bmaths?\b|\bmathematiques?\b|\bmahts\b|\bmathematics\b|\balgebre\b|\bgeometrie\b", text):
        return Subject.MATHEMATIQUES

    if re.search(r"\bphy chi\b|\bphysique chimie\b|\bsciences physiques\b|\bphysics chemistry\b|\bpc\b", text):
        return Subject.PHYSIQUE

    if re.search(r"\bphysique\b", text):
        return Subject.PHYSIQUE

    if re.search(r"\bchimie\b", text):
        return Subject.CHIMIE

    if re.search(r"\bbiologie\b|\bsvt\b|\bsciences naturelles\b|\bsc nat\b", text):
        return Subject.BIOLOGIE

    if re.search(r"\b(d)?anglais\b|\benglish\b|\bdictation\b", text):
        return Subject.ANGLAIS

    if re.search(r"\bdict(ee|ée)\b|\bredaction\b|\brédaction\b|\bdict quest\b|\bgrammaire\b|\bconjugaison\b|\bvocabulaire\b|\bfrancais\b|\bfrançais\b|\blettres\b", text):
        return Subject.FRANCAIS

    if re.search(r"\bhist(oire)? geo(graphie)?\b|\bhistory geography\b", text):
        return Subject.HISTOIRE

    if re.search(r"\bhistoire\b", text):
        return Subject.HISTOIRE

    if re.search(r"\bgeographie\b|\bgéographie\b", text):
        return Subject.GEOGRAPHIE

    if re.search(r"\bphilo(sophie)?\b", text):
        return Subject.PHILOSOPHIE

    if re.search(r"\beconomie\b|\béconomie\b|\bcomptabilite\b", text):
        return Subject.ECONOMIE

    # 3. Essai avec SubjectResolver
    resolver = SubjectResolver()
    resolved = resolver.resolve(text="", filename=path.name)
    if resolved and resolved != Subject.AUTRE:
        return resolved

    return Subject.SCIENCES


# =============================================================
# PROGRAMME PRINCIPAL
# =============================================================

def main():

    print()
    print("=" * 60)
    print(
        "       INDEXATION DES PROGRAMMES ALTERNIA"
    )
    print("=" * 60)
    print()

    print(
        f"Dossier : {KNOWLEDGE_BASE}"
    )

    print(
        f"Index Qdrant: {QDRANT_STORAGE_PATH}"
    )

    print(
        f"Registre    : {DOCUMENT_REGISTRY_PATH}"
    )

    print()

    if not KNOWLEDGE_BASE.exists():

        raise FileNotFoundError(
            "Dossier knowledge-base introuvable : "
            f"{KNOWLEDGE_BASE}"
        )

    # =========================================================
    # 1. RECHERCHE DES PDF
    # =========================================================

    pdf_files = sorted(
        KNOWLEDGE_BASE.rglob("*.pdf")
    )

    print(
        f"Documents PDF trouvés : "
        f"{len(pdf_files)}"
    )

    print()

    if not pdf_files:

        print(
            "Aucun fichier PDF trouvé."
        )

        return

    # =========================================================
    # 2. INITIALISATION
    # =========================================================

    print(
        "[1/6] Initialisation du pipeline..."
    )

    pdf_loader = PDFDocumentLoader()

    structure_detector = (
        StructureDetector()
    )

    subject_resolver = (
        SubjectResolver()
    )

    structure_parser = (
        DocumentStructureParser(
            structure_detector=(
                structure_detector
            ),
            subject_resolver=(
                subject_resolver
            ),
        )
    )

    chunker = PedagogicalChunker(
        max_characters=900,
        min_characters=150,
        overlap_characters=120,
    )

    embedding_service = (
        EmbeddingService()
    )

    vector_store = QdrantVectorStore(
        storage_path=QDRANT_STORAGE_PATH
    )

    indexer = KnowledgeIndexer(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )

    registry = DocumentRegistry(
        storage_path=DOCUMENT_REGISTRY_PATH
    )

    # =========================================================
    # 3. CHARGEMENT INDEX EXISTANT & MIGRATION
    # =========================================================

    print()
    print(
        "[2/6] Chargement de l'index Qdrant existant..."
    )

    loaded = indexer.load()

    # Si Qdrant est vide et qu'un ancien vector_store.json existe, migrer automatiquement
    if indexer.document_count == 0 and VECTOR_STORE_PATH.exists():
        print(
            "Index Qdrant vide détecté. "
            "Migration des chunks existants depuis vector_store.json..."
        )
        migrated = vector_store.migrate_from_json(VECTOR_STORE_PATH)
        if migrated > 0:
            loaded = True

    if loaded:

        print(
            f"Chunks déjà présents dans Qdrant : "
            f"{indexer.document_count}"
        )

    else:

        print(
            "Aucun chunk dans Qdrant (nouvelle base)."
        )

    # =========================================================
    # 4. TRAITEMENT DES PDF
    # =========================================================

    print()
    print(
        "[3/6] Vérification des documents..."
    )
    print()

    documents_indexed = 0
    documents_skipped = 0
    documents_errors = 0

    chunks_added = 0
    chunks_removed = 0

    for pdf_path in pdf_files:

        source = str(pdf_path)

        print(
            f"[PDF] {pdf_path}"
        )

        try:

            student_class = detect_class(
                pdf_path
            )

            subject = detect_subject(
                pdf_path
            )

            series = detect_series(
                pdf_path
            )

            print(
                f"Classe  : "
                f"{student_class.value}"
            )

            print(
                f"Série   : "
                f"{series}"
            )

            print(
                f"Matière : "
                f"{subject.value}"
            )

            # -------------------------------------------------
            # VÉRIFICATION DU REGISTRE
            # -------------------------------------------------

            up_to_date = (
                registry.is_up_to_date(
                    pdf_path
                )
            )

            source_exists = (
                indexer.has_source(
                    source
                )
            )

            if up_to_date and source_exists:

                stored_info = (
                    registry.documents.get(
                        source,
                        {}
                    )
                )

                stored_chunks = (
                    stored_info.get(
                        "chunk_count",
                        0
                    )
                )

                print(
                    "Statut  : "
                    "DÉJÀ INDEXÉ"
                )

                print(
                    f"Chunks  : "
                    f"{stored_chunks}"
                )

                documents_skipped += 1

                print()

                continue

            # -------------------------------------------------
            # DOCUMENT NOUVEAU OU MODIFIÉ
            # -------------------------------------------------

            if up_to_date and not source_exists:

                print(
                    "Registre trouvé mais "
                    "index absent."
                )

            elif source in registry.documents:

                print(
                    "Document modifié."
                )

            else:

                print(
                    "Nouveau document."
                )

            # -------------------------------------------------
            # SUPPRESSION ANCIENNE VERSION
            # -------------------------------------------------

            removed = indexer.remove_source(
                source
            )

            if removed:

                chunks_removed += removed

                print(
                    f"Anciens chunks supprimés : "
                    f"{removed}"
                )

            # -------------------------------------------------
            # CHARGEMENT PDF
            # -------------------------------------------------

            document = pdf_loader.load(
                pdf_path
            )

            # -------------------------------------------------
            # STRUCTURATION PÉDAGOGIQUE
            # -------------------------------------------------

            structured_pages = (
                structure_parser.parse(
                    document
                )
            )

            # Le chemin du fichier reste
            # la source de vérité pour classe/matière/série.

            for page in structured_pages:

                page.metadata.student_class = (
                    student_class.value
                )

                page.metadata.series = series

                page.metadata.subject = (
                    subject.value
                )

            # -------------------------------------------------
            # CHUNKING PÉDAGOGIQUE
            # -------------------------------------------------

            chunks = chunker.chunk(
                pages=structured_pages,
                source_document=source,
                title=pdf_path.stem,
            )

            # -------------------------------------------------
            # SÉCURITÉ MÉTADONNÉES
            # -------------------------------------------------

            for chunk in chunks:

                if not chunk.metadata.student_class:

                    chunk.metadata.student_class = (
                        student_class.value
                    )

                if not chunk.metadata.series:

                    chunk.metadata.series = series

                if not chunk.metadata.subject:

                    chunk.metadata.subject = (
                        subject.value
                    )

            print(
                f"Chunks générés : "
                f"{len(chunks)}"
            )

            # -------------------------------------------------
            # INDEXATION
            # -------------------------------------------------

            documents = (
                indexer.add_pedagogical_chunks(
                    chunks
                )
            )

            chunk_count = len(
                documents
            )

            chunks_added += chunk_count

            documents_indexed += 1

            # -------------------------------------------------
            # ENREGISTREMENT HASH
            # -------------------------------------------------

            registry.register(
                pdf_path,
                chunk_count=chunk_count,
            )

            print(
                "Statut  : INDEXÉ"
            )

            print()

        except Exception as exc:

            documents_errors += 1

            print(
                f"[ERREUR] {pdf_path}"
            )

            print(
                f"         "
                f"{type(exc).__name__}: "
                f"{exc}"
            )

            print()

    # =========================================================
    # 5. SAUVEGARDE
    # =========================================================

    print(
        "[4/6] Sauvegarde de l'index..."
    )

    indexer.save()

    print(
        f"Chunks stockés : "
        f"{indexer.document_count}"
    )

    print(
        f"Stockage Qdrant : "
        f"{QDRANT_STORAGE_PATH}"
    )

    print()

    # =========================================================
    # 6. RÉSUMÉ
    # =========================================================

    print(
        "[5/6] Vérification du registre..."
    )

    registry.save()

    print(
        f"Documents suivis : "
        f"{len(registry.documents)}"
    )

    print()

    print(
        "[6/6] INDEXATION TERMINÉE"
    )

    print("=" * 60)

    print(
        f"Documents trouvés: "
        f"{len(pdf_files)}"
    )

    print(
        f"Documents indexés: "
        f"{documents_indexed}"
    )

    print(
        f"Documents ignorés: "
        f"{documents_skipped}"
    )

    print(
        f"Documents en erreur: "
        f"{documents_errors}"
    )

    print(
        f"Chunks ajoutés: "
        f"{chunks_added}"
    )

    print(
        f"Chunks supprimés: "
        f"{chunks_removed}"
    )

    print(
        f"Chunks dans l'index: "
        f"{indexer.document_count}"
    )

    print("=" * 60)
    print()


if __name__ == "__main__":
    main()