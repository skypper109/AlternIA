from dataclasses import dataclass, field
from typing import Any


@dataclass
class PedagogicalResponse:
    """
    Réponse produite par le moteur pédagogique AlternIA.
    """

    answer: str

    intent: str

    student_class: str

    subject: str | None = None

    sources: list[Any] = field(default_factory=list)

    should_ask_followup: bool = False

    followup_question: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)
