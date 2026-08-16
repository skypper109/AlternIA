from dataclasses import dataclass, field
from typing import Optional

from alternia.learner.models import (
    LearningInteraction,
    LearningStatistics,
    TopicProgress,
)


@dataclass
class LearningProfile:
    """
    Profil d'apprentissage durable d'un élève.

    Contrairement au StudentProfile pédagogique,
    ce profil évolue au fil des interactions.
    """

    student_id: str

    student_class: str

    preferred_language: str = "fr"

    strengths: list[str] = field(
        default_factory=list
    )

    weaknesses: list[str] = field(
        default_factory=list
    )

    mastered_topics: list[str] = field(
        default_factory=list
    )

    topics_to_review: list[str] = field(
        default_factory=list
    )

    topic_progress: dict[str, TopicProgress] = field(
        default_factory=dict
    )

    recent_interactions: list[
        LearningInteraction
    ] = field(default_factory=list)

    statistics: LearningStatistics = field(
        default_factory=LearningStatistics
    )

    current_topic: Optional[str] = None

    current_subject: Optional[str] = None

    @property
    def history(self) -> list[LearningInteraction]:
        """Alias pour recent_interactions."""
        return self.recent_interactions

    def get_topic_progress(
        self,
        topic: str,
    ) -> TopicProgress:

        if topic not in self.topic_progress:
            self.topic_progress[topic] = (
                TopicProgress(
                    topic=topic
                )
            )

        return self.topic_progress[topic]

    def register_interaction(
        self,
        interaction: LearningInteraction,
    ) -> None:

        self.recent_interactions.append(
            interaction
        )

        self.statistics.register_interaction(
            intent=interaction.intent,
            success=interaction.success,
        )

        if interaction.topic:

            self.current_topic = (
                interaction.topic
            )

            if interaction.subject:
                self.current_subject = (
                    interaction.subject
                )

            if interaction.success is not None:

                progress = (
                    self.get_topic_progress(
                        interaction.topic
                    )
                )

                progress.register_attempt(
                    interaction.success
                )

                self._update_topic_status(
                    interaction.topic,
                    progress,
                )

    def _update_topic_status(
        self,
        topic: str,
        progress: TopicProgress,
    ) -> None:

        if (
            progress.attempts >= 2
            and progress.mastery_score >= 0.8
        ):

            if topic not in self.mastered_topics:
                self.mastered_topics.append(
                    topic
                )

            if topic in self.topics_to_review:
                self.topics_to_review.remove(
                    topic
                )

        elif (
            progress.attempts >= 1
            and progress.mastery_score < 0.6
        ):

            if topic not in self.topics_to_review:
                self.topics_to_review.append(
                    topic
                )

            if topic in self.mastered_topics:
                self.mastered_topics.remove(
                    topic
                )