from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StudentProfile:
    """
    Profil pédagogique d'un élève.

    Ce profil permet au moteur pédagogique
    d'adapter progressivement ses réponses.
    """

    student_id: Optional[str] = None

    student_class: str = "10eme"

    preferred_language: str = "fr"

    level: Optional[str] = None

    strengths: list[str] = field(default_factory=list)

    weaknesses: list[str] = field(default_factory=list)

    mastered_topics: list[str] = field(default_factory=list)

    topics_to_review: list[str] = field(default_factory=list)

    questions_asked: int = 0


@dataclass
class QuestionAnalysis:
    """
    Analyse pédagogique d'une question élève.
    """

    original_question: str

    intent: str

    student_class: str

    subject: Optional[str] = None

    chapter: Optional[str] = None

    lesson: Optional[str] = None

    difficulty: Optional[str] = None


@dataclass
class PedagogicalRequest:
    """
    Requête complète envoyée au moteur pédagogique.
    """

    question: str

    profile: StudentProfile

    analysis: QuestionAnalysis

    context: str = ""


@dataclass
class PedagogicalResponse:
    """
    Réponse produite par le moteur pédagogique.
    """

    answer: str

    student_class: str

    subject: Optional[str] = None

    intent: Optional[str] = None

    sources_used: list[str] = field(default_factory=list)

    needs_follow_up: bool = False

    follow_up_question: Optional[str] = None
