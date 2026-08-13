import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alternia.core.models import (
    KnowledgeChunk,
    StudentClass,
    StudentQuestion,
    Subject,
)

from alternia.rag.local_retriever import LocalRetriever


def test_retriever_respects_class():

    retriever = LocalRetriever()

    documents = [
        KnowledgeChunk(
            chunk_id="10-math-001",
            content="Équations niveau 10ème",
            student_class=StudentClass.TEN,
            subject=Subject.MATHEMATIQUES,
            chapter="Equations",
            title="Equations",
            source="programme_10eme",
        ),
        KnowledgeChunk(
            chunk_id="11-math-001",
            content="Équations niveau 11ème",
            student_class=StudentClass.ELEVEN,
            subject=Subject.MATHEMATIQUES,
            chapter="Equations",
            title="Equations",
            source="programme_11eme",
        ),
    ]

    retriever.add_documents(documents)

    question = StudentQuestion(
        student_id="student_001",
        student_class=StudentClass.TEN,
        subject=Subject.MATHEMATIQUES,
        question="Comment résoudre une équation ?",
    )

    results = retriever.search(question)

    assert len(results) == 1
    assert results[0].student_class == StudentClass.TEN