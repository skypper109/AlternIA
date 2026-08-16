from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class LearningInteraction:
    """
    Représente une interaction pédagogique
    entre l'élève et AlternIA.
    """

    question: str

    intent: str

    subject: Optional[str] = None

    topic: Optional[str] = None

    difficulty: Optional[str] = None

    success: Optional[bool] = None

    timestamp: datetime = field(
        default_factory=_utcnow
    )


@dataclass
class TopicProgress:
    """
    Progression de l'élève sur une notion.
    """

    topic: str

    attempts: int = 0

    successes: int = 0

    failures: int = 0

    mastery_score: float = 0.0

    last_seen: Optional[datetime] = None

    def register_attempt(
        self,
        success: bool,
    ) -> None:

        self.attempts += 1

        if success:
            self.successes += 1
        else:
            self.failures += 1

        if self.attempts > 0:
            self.mastery_score = (
                self.successes
                / self.attempts
            )

        self.last_seen = _utcnow()



@dataclass
class LearningStatistics:
    """
    Statistiques globales d'apprentissage.
    """

    total_questions: int = 0

    total_exercises: int = 0

    total_corrections: int = 0

    successful_interactions: int = 0

    failed_interactions: int = 0

    def register_interaction(
        self,
        intent: str,
        success: Optional[bool],
    ) -> None:

        self.total_questions += 1

        if intent == "exercise":
            self.total_exercises += 1

        if intent == "correction":
            self.total_corrections += 1

        if success is True:
            self.successful_interactions += 1

        elif success is False:
            self.failed_interactions += 1