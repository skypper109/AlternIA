from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class StudentClass(str, Enum):

    SIX = "6eme"
    SEVEN = "7eme"
    EIGHT = "8eme"
    NINE = "9eme"
    TEN = "10eme"
    ELEVEN = "11eme"
    TWELVE = "12eme"

    @classmethod
    def from_str(cls, value: str | None) -> Optional["StudentClass"]:
        """Convertit de manière tolérante une chaîne en valeur d'énumération StudentClass."""
        if not value:
            return None
        if isinstance(value, StudentClass):
            return value

        v = str(value).strip().lower()
        mapping = {
            "6": cls.SIX,
            "6e": cls.SIX,
            "6eme": cls.SIX,
            "6ème": cls.SIX,
            "6ieme": cls.SIX,
            "6ième": cls.SIX,
            "sixieme": cls.SIX,
            "sixième": cls.SIX,
            "7": cls.SEVEN,
            "7e": cls.SEVEN,
            "7eme": cls.SEVEN,
            "7ème": cls.SEVEN,
            "7ieme": cls.SEVEN,
            "7ième": cls.SEVEN,
            "septieme": cls.SEVEN,
            "septième": cls.SEVEN,
            "8": cls.EIGHT,
            "8e": cls.EIGHT,
            "8eme": cls.EIGHT,
            "8ème": cls.EIGHT,
            "8ieme": cls.EIGHT,
            "8ième": cls.EIGHT,
            "huitieme": cls.EIGHT,
            "huitième": cls.EIGHT,
            "9": cls.NINE,
            "9e": cls.NINE,
            "9eme": cls.NINE,
            "9ème": cls.NINE,
            "9ieme": cls.NINE,
            "9ième": cls.NINE,
            "neuvieme": cls.NINE,
            "neuvième": cls.NINE,
            "def": cls.NINE,
            "10": cls.TEN,
            "10e": cls.TEN,
            "10eme": cls.TEN,
            "10ème": cls.TEN,
            "10ieme": cls.TEN,
            "10ième": cls.TEN,
            "seconde": cls.TEN,
            "11": cls.ELEVEN,
            "11e": cls.ELEVEN,
            "11eme": cls.ELEVEN,
            "11ème": cls.ELEVEN,
            "11ieme": cls.ELEVEN,
            "11ième": cls.ELEVEN,
            "premiere": cls.ELEVEN,
            "première": cls.ELEVEN,
            "12": cls.TWELVE,
            "12e": cls.TWELVE,
            "12eme": cls.TWELVE,
            "12ème": cls.TWELVE,
            "12ieme": cls.TWELVE,
            "12ième": cls.TWELVE,
            "terminale": cls.TWELVE,
            "tle": cls.TWELVE,
            "bac": cls.TWELVE,
            "tse": cls.TWELVE,
            "tsexp": cls.TWELVE,
            "tss": cls.TWELVE,
            "tseco": cls.TWELVE,
            "tll": cls.TWELVE,
        }
        if v in mapping:
            return mapping[v]

        for item in cls:
            if item.value == v:
                return item
        return None


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
    ECM = "ecm"
    AGRICULTURE = "agriculture"
    DESSIN = "dessin"
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
            "math": cls.MATHEMATIQUES,
            "mahts": cls.MATHEMATIQUES,
            "mathematique": cls.MATHEMATIQUES,
            "mathematiques": cls.MATHEMATIQUES,
            "mathematics": cls.MATHEMATIQUES,
            "physique": cls.PHYSIQUE,
            "chimie": cls.CHIMIE,
            "physique-chimie": cls.PHYSIQUE,
            "phy-chi": cls.PHYSIQUE,
            "sciences-physiques": cls.PHYSIQUE,
            "sciences physiques": cls.PHYSIQUE,
            "physics-chemistry": cls.PHYSIQUE,
            "pc": cls.PHYSIQUE,
            "biologie": cls.BIOLOGIE,
            "svt": cls.SVT,
            "bio": cls.BIOLOGIE,
            "sciences-naturelles": cls.BIOLOGIE,
            "sciences naturelles": cls.BIOLOGIE,
            "sc-nat": cls.BIOLOGIE,
            "francais": cls.FRANCAIS,
            "français": cls.FRANCAIS,
            "dictee": cls.FRANCAIS,
            "dictée": cls.FRANCAIS,
            "redaction": cls.FRANCAIS,
            "rédaction": cls.FRANCAIS,
            "grammaire": cls.FRANCAIS,
            "dict-quest": cls.FRANCAIS,
            "philosophie": cls.PHILOSOPHIE,
            "philo": cls.PHILOSOPHIE,
            "histoire": cls.HISTOIRE,
            "geographie": cls.GEOGRAPHIE,
            "géographie": cls.GEOGRAPHIE,
            "histoire-geo": cls.HISTOIRE,
            "histoire-géo": cls.HISTOIRE,
            "hist-geo": cls.HISTOIRE,
            "history-geography": cls.HISTOIRE,
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
            "english": cls.ANGLAIS,
            "dictation": cls.ANGLAIS,
            "ecm": cls.ECM,
            "education civique": cls.ECM,
            "éducation civique": cls.ECM,
            "civique": cls.ECM,
            "morale": cls.ECM,
            "agriculture": cls.AGRICULTURE,
            "agri": cls.AGRICULTURE,
            "dessin": cls.DESSIN,
            "arts": cls.DESSIN,
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