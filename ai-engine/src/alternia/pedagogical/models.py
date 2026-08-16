from dataclasses import dataclass, field
from typing import Optional

@dataclass
class StudentProfile:
    student_id: Optional[str] = None
    student_class: str = "10eme"
    series: Optional[str] = None
    preferred_language: str = "fr"
    level: Optional[str] = None
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    mastered_topics: list[str] = field(default_factory=list)
    topics_to_review: list[str] = field(default_factory=list)
    questions_asked: int = 0


@dataclass
class QuestionAnalysis:
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

    Le profil durable est optionnel.
    Le contexte conversationnel représente la mémoire
    court terme de la session.
    """

    question: str

    profile: StudentProfile

    analysis: QuestionAnalysis

    context: str = ""

    conversation_context: str = ""

@dataclass
class PedagogicalResponse:
    answer: str
    student_class: str
    subject: Optional[str] = None
    intent: Optional[str] = None
    sources_used: list[str] = field(default_factory=list)
    needs_follow_up: bool = False
    follow_up_question: Optional[str] = None