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
    BIOLOGIE = "biologie"
    SVT = "svt"
    FRANCAIS = "francais"
    PHILOSOPHIE = "philosophie"
    HISTOIRE = "histoire"
    GEOGRAPHIE = "geographie"
    ECONOMIE = "economie"
    COMPTABILITE = "comptabilite"
    LINGUISTIQUE = "linguistique"
    SOCIOLOGIE = "sociologie"
    GEOLOGIE = "geologie"
    DROIT = "droit"
    ANGLAIS = "anglais"
    SCIENCES = "sciences"
    AUTRE = "autre"

    @classmethod
    def from_str(cls, value: str | None) -> Optional["Subject"]:
        """Convertit de manière tolérante une chaîne en valeur d'énumération Subject."""
        if not value:
            return None
        if isinstance(value, Subject):
            return value

        v = str(value).strip().lower()
        mapping = {
            "maths": cls.MATHEMATIQUES,
            "mathematique": cls.MATHEMATIQUES,
            "mathematiques": cls.MATHEMATIQUES,
            "physique": cls.PHYSIQUE,
            "chimie": cls.CHIMIE,
            "physique-chimie": cls.PHYSIQUE,
            "pc": cls.PHYSIQUE,
            "biologie": cls.BIOLOGIE,
            "svt": cls.SVT,
            "bio": cls.BIOLOGIE,
            "francais": cls.FRANCAIS,
            "français": cls.FRANCAIS,
            "philosophie": cls.PHILOSOPHIE,
            "philo": cls.PHILOSOPHIE,
            "histoire": cls.HISTOIRE,
            "geographie": cls.GEOGRAPHIE,
            "géographie": cls.GEOGRAPHIE,
            "histoire-geo": cls.HISTOIRE,
            "histoire-géo": cls.HISTOIRE,
            "economie": cls.ECONOMIE,
            "économie": cls.ECONOMIE,
            "seco": cls.ECONOMIE,
            "comptabilite": cls.COMPTABILITE,
            "comptabilité": cls.COMPTABILITE,
            "linguistique": cls.LINGUISTIQUE,
            "sociologie": cls.SOCIOLOGIE,
            "geologie": cls.GEOLOGIE,
            "géologie": cls.GEOLOGIE,
            "droit": cls.DROIT,
            "anglais": cls.ANGLAIS,
            "sciences": cls.SCIENCES,
        }
        if v in mapping:
            return mapping[v]

        for item in cls:
            if item.value == v:
                return item
        return cls.AUTRE


class StudentProfile(BaseModel):

    student_id: str

    student_class: StudentClass

    series: Optional[str] = None

    current_subject: Optional[Subject] = None

    strengths: list[str] = Field(
        default_factory=list
    )

    weaknesses: list[str] = Field(
        default_factory=list
    )

    mastered_topics: list[str] = Field(
        default_factory=list
    )

    difficult_topics: list[str] = Field(
        default_factory=list
    )


class StudentQuestion(BaseModel):

    student_id: str

    student_class: StudentClass

    series: Optional[str] = None

    question: str

    subject: Optional[Subject] = None


class RetrievedDocument(BaseModel):

    document_id: str

    title: str

    content: str

    student_class: StudentClass

    series: Optional[str] = None

    subject: Optional[Subject] = None

    score: float = 0.0


class PedagogicalResponse(BaseModel):

    answer: str

    student_class: StudentClass

    series: Optional[str] = None

    subject: Optional[Subject] = None

    explanation_level: str = "adapted"

    sources: list[str] = Field(
        default_factory=list
    )


class KnowledgeChunk(BaseModel):

    chunk_id: str

    content: str

    student_class: StudentClass

    series: Optional[str] = None

    subject: Subject

    chapter: str

    title: str

    source: str

    source_version: Optional[str] = None

    lesson: Optional[str] = None

    section: Optional[str] = None

    page_start: Optional[int] = None

    page_end: Optional[int] = None