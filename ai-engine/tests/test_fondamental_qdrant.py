import pytest
from pathlib import Path

from alternia.core.models import KnowledgeChunk, StudentClass, Subject
from alternia.core.pedagogical_chunk import PedagogicalChunk
from alternia.ingestion.metadata.structure import PedagogicalMetadata
from alternia.ingestion.metadata.subject_resolver import SubjectResolver
from alternia.rag.vector_store import (
    CLASS_HIERARCHY,
    LocalVectorStore,
    is_chunk_allowed,
)
from alternia.rag.qdrant_vector_store import QdrantVectorStore
from alternia.rag.indexer import KnowledgeIndexer
from alternia.scripts.index_knowledge import (
    detect_class,
    detect_series,
    detect_subject,
)


def test_student_class_fundamental_support():
    assert StudentClass.SIX.value == "6eme"
    assert StudentClass.SEVEN.value == "7eme"
    assert StudentClass.EIGHT.value == "8eme"
    assert StudentClass.NINE.value == "9eme"

    # Test from_str tolérance
    assert StudentClass.from_str("6eme") == StudentClass.SIX
    assert StudentClass.from_str("6e") == StudentClass.SIX
    assert StudentClass.from_str("6ème") == StudentClass.SIX
    assert StudentClass.from_str("7eme") == StudentClass.SEVEN
    assert StudentClass.from_str("8eme") == StudentClass.EIGHT
    assert StudentClass.from_str("9eme") == StudentClass.NINE
    assert StudentClass.from_str("def") == StudentClass.NINE
    assert StudentClass.from_str("10eme") == StudentClass.TEN
    assert StudentClass.from_str("12eme") == StudentClass.TWELVE
    assert StudentClass.from_str("tse") == StudentClass.TWELVE


def test_subject_fundamental_support():
    assert Subject.ECM.value == "ecm"
    assert Subject.AGRICULTURE.value == "agriculture"
    assert Subject.DESSIN.value == "dessin"

    assert Subject.from_str("ecm") == Subject.ECM
    assert Subject.from_str("civique") == Subject.ECM
    assert Subject.from_str("agriculture") == Subject.AGRICULTURE
    assert Subject.from_str("agri") == Subject.AGRICULTURE
    assert Subject.from_str("dessin") == Subject.DESSIN
    assert Subject.from_str("dictee") == Subject.FRANCAIS
    assert Subject.from_str("dict-quest") == Subject.FRANCAIS
    assert Subject.from_str("phy-chi") == Subject.PHYSIQUE
    assert Subject.from_str("mahts") == Subject.MATHEMATIQUES
    assert Subject.from_str("sciences-naturelles") == Subject.BIOLOGIE


def test_subject_resolver_fundamental():
    resolver = SubjectResolver()
    assert resolver.resolve("", filename="BK_6-eme-annale-AGRICULTURE.pdf") == Subject.AGRICULTURE
    assert resolver.resolve("", filename="BK-DEF-ECM-2023.pdf") == Subject.ECM
    assert resolver.resolve("", filename="BK_9-eme-COMP-DESSIN.pdf") == Subject.DESSIN
    assert resolver.resolve("", filename="BK_6-eme-annale-DICTEE.pdf") == Subject.FRANCAIS
    assert resolver.resolve("", filename="BK_7-eme-exos-corriges-MAHTS.pdf") == Subject.MATHEMATIQUES
    assert resolver.resolve("", filename="BK_9-eme-ANNALE-PHY-CHI.pdf") == Subject.PHYSIQUE


def test_index_knowledge_metadata_detection():
    # 6ème Agriculture
    p6_agri = Path("knowledge-base/fondamental/6eme/pdf/BK_6-eme-annale-AGRICULTURE-LA-CLE-DE-LA-7eme-Y-TRAORE.pdf")
    assert detect_class(p6_agri) == StudentClass.SIX
    assert detect_series(p6_agri) == "generale"
    assert detect_subject(p6_agri) == Subject.AGRICULTURE

    # 6ème Dictée
    p6_dict = Path("knowledge-base/fondamental/6eme/pdf/annal-dictee-questions.pdf")
    assert detect_class(p6_dict) == StudentClass.SIX
    assert detect_subject(p6_dict) == Subject.FRANCAIS

    # 7ème Maths
    p7_math = Path("knowledge-base/fondamental/7eme/pdf/BK_7-eme-exos-corriges-MAHTS.pdf")
    assert detect_class(p7_math) == StudentClass.SEVEN
    assert detect_subject(p7_math) == Subject.MATHEMATIQUES

    # 8ème Histoire
    p8_hist = Path("knowledge-base/fondamental/8eme/pdf/BK_8-eme-cours-HISTOIRE-M-CISSE.pdf")
    assert detect_class(p8_hist) == StudentClass.EIGHT
    assert detect_subject(p8_hist) == Subject.HISTOIRE

    # 9ème DEF ECM
    p9_ecm = Path("knowledge-base/fondamental/9eme/pdf/BK-DEF-ECM-2023.pdf")
    assert detect_class(p9_ecm) == StudentClass.NINE
    assert detect_subject(p9_ecm) == Subject.ECM

    # 9ème Anglais
    p9_anglais = Path("knowledge-base/fondamental/9eme/pdf/Lecon-danglais-9eme-annee.pdf")
    assert detect_class(p9_anglais) == StudentClass.NINE
    assert detect_subject(p9_anglais) == Subject.ANGLAIS

    # Lycée 10ème Tronc commun
    p10 = Path("knowledge-base/10eme/sciences/cours.pdf")
    assert detect_class(p10) == StudentClass.TEN
    assert detect_series(p10) == "generale"
    assert detect_subject(p10) == Subject.SCIENCES


def test_fundamental_class_hierarchy():
    assert CLASS_HIERARCHY["6eme"] == ["6eme"]
    assert CLASS_HIERARCHY["7eme"] == ["6eme", "7eme"]
    assert CLASS_HIERARCHY["8eme"] == ["6eme", "7eme", "8eme"]
    assert CLASS_HIERARCHY["9eme"] == ["6eme", "7eme", "8eme", "9eme"]
    assert "9eme" in CLASS_HIERARCHY["10eme"]
    assert "6eme" in CLASS_HIERARCHY["12eme"]

    # Règle de progression
    assert is_chunk_allowed(chunk_class="6eme", chunk_series="generale", student_class=StudentClass.SIX) is True
    # Un élève de 6ème ne peut pas voir la 7ème ou 9ème
    assert is_chunk_allowed(chunk_class="7eme", chunk_series="generale", student_class=StudentClass.SIX) is False
    assert is_chunk_allowed(chunk_class="9eme", chunk_series="generale", student_class=StudentClass.SIX) is False

    # Un élève de 9ème peut voir 6eme, 7eme, 8eme, 9eme
    assert is_chunk_allowed(chunk_class="6eme", chunk_series="generale", student_class=StudentClass.NINE) is True
    assert is_chunk_allowed(chunk_class="8eme", chunk_series="generale", student_class=StudentClass.NINE) is True
    assert is_chunk_allowed(chunk_class="9eme", chunk_series="generale", student_class=StudentClass.NINE) is True
    assert is_chunk_allowed(chunk_class="10eme", chunk_series="generale", student_class=StudentClass.NINE) is False

    # Un élève de 12ème TSE a accès au fondamental comme prérequis universel
    assert is_chunk_allowed(chunk_class="9eme", chunk_series="generale", student_class=StudentClass.TWELVE, student_series="tse") is True


def test_qdrant_vector_store_operations():
    store = QdrantVectorStore(location=":memory:", dimension=4)
    assert store.count == 0

    chunk1 = KnowledgeChunk(
        chunk_id="chunk-6e-01",
        content="Les fractions en 6ème année",
        student_class=StudentClass.SIX,
        series="generale",
        subject=Subject.MATHEMATIQUES,
        chapter="Nombres",
        title="Fractions",
        source="/path/to/6e_maths.pdf",
    )
    chunk2 = KnowledgeChunk(
        chunk_id="chunk-9e-01",
        content="Théorème de Thalès au DEF",
        student_class=StudentClass.NINE,
        series="generale",
        subject=Subject.MATHEMATIQUES,
        chapter="Géométrie",
        title="Thalès",
        source="/path/to/9e_maths.pdf",
    )
    chunk3 = KnowledgeChunk(
        chunk_id="chunk-9e-ecm",
        content="Les institutions républicaines du Mali",
        student_class=StudentClass.NINE,
        series="generale",
        subject=Subject.ECM,
        chapter="Citoyenneté",
        title="Institutions",
        source="/path/to/9e_ecm.pdf",
    )

    store.add(chunk1, [0.5, 0.5, 0.5, 0.5])
    store.add_many([chunk2, chunk3], [[0.1, 0.9, 0.1, 0.1], [0.1, 0.1, 0.9, 0.1]])

    assert store.count == 3
    assert store.has_source("/path/to/6e_maths.pdf") is True
    assert store.has_source("/path/to/unknown.pdf") is False

    # Recherche pour élève de 6ème en maths
    results_6e = store.search(
        query_vector=[0.5, 0.5, 0.5, 0.5],
        top_k=5,
        student_class="6eme",
        subject="mathematiques",
    )
    assert len(results_6e) == 1
    assert results_6e[0][0].chunk_id == "chunk-6e-01"

    # Recherche pour élève de 9ème en maths (peut voir 6ème et 9ème)
    results_9e = store.search(
        query_vector=[0.1, 0.9, 0.1, 0.1],
        top_k=5,
        student_class="9eme",
        subject="mathematiques",
    )
    assert any(doc.chunk_id == "chunk-9e-01" for doc, _ in results_9e)

    # Suppression par source
    removed = store.remove_by_source("/path/to/9e_ecm.pdf")
    assert removed == 1
    assert store.count == 2
    assert store.has_source("/path/to/9e_ecm.pdf") is False

    store.close()
