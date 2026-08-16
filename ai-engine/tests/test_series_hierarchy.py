from alternia.core.models import KnowledgeChunk, StudentClass, Subject
from alternia.rag.vector_store import LocalVectorStore, is_chunk_allowed


def test_is_chunk_allowed_rules():
    # 10eme student can ONLY access 10eme
    assert is_chunk_allowed("10eme", "generale", "10eme", "generale") is True
    assert is_chunk_allowed("11eme", "11s", "10eme", "generale") is False
    assert is_chunk_allowed("12eme", "tse", "10eme", "generale") is False

    # 11eme 11s student can access 11s and 10eme, but NOT 11l or 12eme
    assert is_chunk_allowed("10eme", "generale", "11eme", "11s") is True
    assert is_chunk_allowed("11eme", "11s", "11eme", "11s") is True
    assert is_chunk_allowed("11eme", "11l", "11eme", "11s") is False
    assert is_chunk_allowed("11eme", "11seco", "11eme", "11s") is False
    assert is_chunk_allowed("12eme", "tse", "11eme", "11s") is False

    # 12eme TSE student can access 12eme TSE, shared TSE_TSEXP, 11s, and 10eme
    assert is_chunk_allowed("10eme", "generale", "12eme", "tse") is True
    assert is_chunk_allowed("11eme", "11s", "12eme", "tse") is True
    assert is_chunk_allowed("11eme", "11l", "12eme", "tse") is False
    assert is_chunk_allowed("12eme", "tse", "12eme", "tse") is True
    assert is_chunk_allowed("12eme", "tse_tsexp", "12eme", "tse") is True
    assert is_chunk_allowed("12eme", "tsexp", "12eme", "tse") is False
    assert is_chunk_allowed("12eme", "tseco", "12eme", "tse") is False


def test_vector_store_strict_hierarchy_search(tmp_path):
    store = LocalVectorStore(storage_path=tmp_path / "index.json")

    c10 = KnowledgeChunk(
        chunk_id="c10",
        content="Cours de 10eme",
        student_class=StudentClass.TEN,
        series="generale",
        subject=Subject.PHYSIQUE,
        chapter="Mouvements",
        title="10e Physique",
        source="manuel10.pdf",
    )
    c11s = KnowledgeChunk(
        chunk_id="c11s",
        content="Cours de 11eme Sciences",
        student_class=StudentClass.ELEVEN,
        series="11s",
        subject=Subject.PHYSIQUE,
        chapter="Cinématique 11S",
        title="11S Physique",
        source="manuel11s.pdf",
    )
    c11l = KnowledgeChunk(
        chunk_id="c11l",
        content="Cours de 11eme Lettres",
        student_class=StudentClass.ELEVEN,
        series="11l",
        subject=Subject.FRANCAIS,
        chapter="Grammaire 11L",
        title="11L Français",
        source="manuel11l.pdf",
    )
    c12tse = KnowledgeChunk(
        chunk_id="c12tse",
        content="Cours de Terminale TSE",
        student_class=StudentClass.TWELVE,
        series="tse",
        subject=Subject.PHYSIQUE,
        chapter="Oscillations TSE",
        title="TSE Physique",
        source="manuel12tse.pdf",
    )

    vec = [1.0, 0.0, 0.0]
    store.add(c10, vec)
    store.add(c11s, vec)
    store.add(c11l, vec)
    store.add(c12tse, vec)

    # 1. 10eme search should ONLY find c10
    res_10 = store.search(query_vector=vec, top_k=10, student_class="10eme", student_series="generale")
    ids_10 = [doc.chunk_id for doc, _ in res_10]
    assert "c10" in ids_10
    assert "c11s" not in ids_10
    assert "c11l" not in ids_10
    assert "c12tse" not in ids_10

    # 2. 11eme 11s search should find c11s and c10, NOT c11l or c12tse
    res_11s = store.search(query_vector=vec, top_k=10, student_class="11eme", student_series="11s")
    ids_11s = [doc.chunk_id for doc, _ in res_11s]
    assert "c11s" in ids_11s
    assert "c10" in ids_11s
    assert "c11l" not in ids_11s
    assert "c12tse" not in ids_11s

    # 3. 12eme TSE search should find c12tse, c11s, c10, NOT c11l
    res_12 = store.search(query_vector=vec, top_k=10, student_class="12eme", student_series="tse")
    ids_12 = [doc.chunk_id for doc, _ in res_12]
    assert "c12tse" in ids_12
    assert "c11s" in ids_12
    assert "c10" in ids_12
    assert "c11l" not in ids_12
