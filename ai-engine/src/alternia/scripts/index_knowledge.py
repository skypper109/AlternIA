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
from alternia.rag.indexer import KnowledgeIndexer
from alternia.rag.vector_store import LocalVectorStore


KNOWLEDGE_BASE = (
    PROJECT_ROOT / "knowledge-base"
)

INDEX_DIRECTORY = (
    PROJECT_ROOT
    / "ai-engine"
    / "data"
    / "index"
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
    10ème : 'generale' (Tronc Commun)
    11ème : '11s' (Sciences), '11l' (Lettres), '11seco' (Économie/Tertiaire), 'generale'
    12ème : 'tse' (Sciences Exactes), 'tsexp' (Sciences Expérimentales), 'tseco' (Sciences Éco), 'tss' (Sciences Sociales), 'tll' (Lettres), 'generale'
    """
    path_str = str(path).lower()
    stem = path.stem.lower()

    # 10ème -> Tronc Commun
    if "10eme" in path_str or "10e" in path_str:
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
    Détecte la classe depuis le chemin du PDF.
    """

    for part in path.parts:

        normalized = (
            part.lower().strip()
        )

        try:
            return StudentClass(
                normalized
            )

        except ValueError:
            continue

    raise ValueError(
        f"Classe impossible à déterminer : {path}"
    )


def detect_subject(
    path: Path,
) -> Subject:
    """
    Détecte la matière depuis le chemin du PDF.
    """
    for part in path.parts:
        normalized = part.lower().strip()
        subject = Subject.from_str(normalized)
        if subject and subject != Subject.AUTRE:
            return subject

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
        f"Index   : {VECTOR_STORE_PATH}"
    )

    print(
        f"Registre: {DOCUMENT_REGISTRY_PATH}"
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

    vector_store = LocalVectorStore(
        storage_path=VECTOR_STORE_PATH
    )

    indexer = KnowledgeIndexer(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )

    registry = DocumentRegistry(
        storage_path=DOCUMENT_REGISTRY_PATH
    )

    # =========================================================
    # 3. CHARGEMENT INDEX EXISTANT
    # =========================================================

    print()
    print(
        "[2/6] Chargement de l'index existant..."
    )

    loaded = indexer.load()

    if loaded:

        print(
            f"Chunks déjà présents : "
            f"{indexer.document_count}"
        )

    else:

        print(
            "Aucun index existant."
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
        f"Fichier : "
        f"{VECTOR_STORE_PATH}"
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