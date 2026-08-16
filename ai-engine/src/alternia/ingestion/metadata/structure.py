from dataclasses import dataclass
from typing import Optional


@dataclass
class PedagogicalMetadata:
    """
    Métadonnées pédagogiques associées à un contenu.
    """

    student_class: Optional[str] = None
    series: Optional[str] = None
    subject: Optional[str] = None
    chapter: Optional[str] = None
    lesson: Optional[str] = None
    section: Optional[str] = None
    objective: Optional[str] = None

    def copy(self) -> "PedagogicalMetadata":
        """
        Crée une copie indépendante des métadonnées.
        """

        return PedagogicalMetadata(
            student_class=self.student_class,
            series=self.series,
            subject=self.subject,
            chapter=self.chapter,
            lesson=self.lesson,
            section=self.section,
            objective=self.objective,
        )