from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class StudentClass(str, Enum):
    TEN = "10eme"
    ELEVEN = "11eme"
    TWELVE = "12eme"


class Subject(str, Enum):
    MATHEMATIQUES = "mathematiques"
    PHYSIQUE = "physique"
    CHIMIE = "chimie"
    FRANCAIS = "francais"
    ANGLAIS = "anglais"
    HISTOIRE = "histoire"
    GEOGRAPHIE = "geographie"
    SCIENCES = "sciences"
    AUTRE = "autre"


class StudentProfile(BaseModel):
    student_id: str

    student_class: StudentClass

    current_subject: Optional[Subject] = None

    strengths: list[str] = Field(default_factory=list)

    weaknesses: list[str] = Field(default_factory=list)

    mastered_topics: list[str] = Field(default_factory=list)

    difficult_topics: list[str] = Field(default_factory=list)


class StudentQuestion(BaseModel):
    student_id: str

    student_class: StudentClass

    question: str

    subject: Optional[Subject] = None


class RetrievedDocument(BaseModel):
    document_id: str

    title: str

    content: str

    student_class: StudentClass

    subject: Optional[Subject] = None

    score: float = 0.0


class PedagogicalResponse(BaseModel):
    answer: str

    student_class: StudentClass

    subject: Optional[Subject] = None

    explanation_level: str = "adapted"

    sources: list[str] = Field(default_factory=list)