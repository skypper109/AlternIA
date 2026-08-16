from dataclasses import dataclass, field
from typing import Any


@dataclass
class ContextSource:
    """
    Représente une source pédagogique utilisée
    pour construire le contexte de réponse.
    """

    chunk_id: str
    content: str

    score: float

    student_class: str = ""
    subject: str | None = None
    chapter: str | None = None
    lesson: str | None = None

    source_document: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PedagogicalContext:
    """
    Contexte pédagogique transmis au moteur pédagogique.
    """

    query: str

    student_class: str
    subject: str | None = None

    sources: list[ContextSource] = field(
        default_factory=list
    )

    context_text: str = ""

    max_sources: int = 5

    def is_empty(self) -> bool:
        return len(self.sources) == 0