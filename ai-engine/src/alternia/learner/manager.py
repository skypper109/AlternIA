from alternia.learner.models import (
    LearningInteraction,
)
from alternia.learner.profile import (
    LearningProfile,
)
from alternia.pedagogical.models import (
    StudentProfile as PedagogicalStudentProfile,
)


class LearnerManager:
    """
    Gestionnaire des profils d'apprentissage.

    Cette couche représente la mémoire pédagogique
    durable de l'élève.

    Elle reste indépendante du moteur pédagogique.
    """

    def __init__(self):

        self._profiles: dict[
            str,
            LearningProfile,
        ] = {}

    # =========================================================
    # PROFIL
    # =========================================================

    def create_profile(
        self,
        student_id: str,
        student_class: str,
        preferred_language: str = "fr",
    ) -> LearningProfile:

        if student_id in self._profiles:
            return self._profiles[
                student_id
            ]

        profile = LearningProfile(
            student_id=student_id,
            student_class=student_class,
            preferred_language=preferred_language,
        )

        self._profiles[
            student_id
        ] = profile

        return profile

    def get_profile(
        self,
        student_id: str,
    ) -> LearningProfile:

        try:
            return self._profiles[
                student_id
            ]

        except KeyError:
            raise KeyError(
                f"Profil élève introuvable : "
                f"{student_id}"
            )

    def get_optional_profile(
        self,
        student_id: str,
    ) -> LearningProfile | None:
        """
        Retourne le profil s'il existe.

        Aucun profil n'est créé automatiquement.
        """
        return self._profiles.get(student_id)

    def get_or_create(
        self,
        student_id: str,
        student_class: str = "10eme",
        preferred_language: str = "fr",
    ) -> LearningProfile:
        """
        Retourne le profil apprenant existant ou le crée s'il n'existe pas.
        """
        profile = self.get_optional_profile(student_id)
        if profile is not None:
            return profile
        return self.create_profile(
            student_id=student_id,
            student_class=student_class,
            preferred_language=preferred_language,
        )


    def to_optional_pedagogical_profile(
        self,
        student_id: str,
    ) -> PedagogicalStudentProfile | None:
        """
        Convertit le profil apprenant vers le profil
        pédagogique uniquement s'il existe.
        """

        profile = self.get_optional_profile(
            student_id
        )

        if profile is None:
            return None

        return self.to_pedagogical_profile(
            student_id
        )

    def get_or_create_profile(
        self,
        student_id: str,
        student_class: str,
        preferred_language: str = "fr",
    ) -> LearningProfile:

        if student_id in self._profiles:
            return self._profiles[
                student_id
            ]

        return self.create_profile(
            student_id=student_id,
            student_class=student_class,
            preferred_language=preferred_language,
        )

    def has_profile(
        self,
        student_id: str,
    ) -> bool:

        return student_id in self._profiles

    # =========================================================
    # ADAPTATION VERS LE MOTEUR PÉDAGOGIQUE
    # =========================================================

    def to_pedagogical_profile(
        self,
        student_id: str,
        student_class: str = "10eme",
        preferred_language: str = "fr",
    ) -> PedagogicalStudentProfile:

        profile = self.get_or_create_profile(
            student_id=student_id,
            student_class=student_class,
            preferred_language=preferred_language,
        )

        return PedagogicalStudentProfile(
            student_id=profile.student_id,
            student_class=profile.student_class,
            preferred_language=profile.preferred_language,
            strengths=list(profile.strengths),
            weaknesses=list(profile.weaknesses),
            mastered_topics=list(
                profile.mastered_topics
            ),
            topics_to_review=list(
                profile.topics_to_review
            ),
            questions_asked=(
                profile.statistics.total_questions
            ),
        )
    # =========================================================
    # APPRENTISSAGE
    # =========================================================

    def register_interaction(
        self,
        student_id: str,
        interaction: LearningInteraction,
    ) -> LearningProfile:

        profile = self.get_profile(
            student_id
        )

        profile.register_interaction(
            interaction
        )

        return profile


    # =========================================================
    # ÉVALUATION
    # =========================================================

    def register_result(
        self,
        student_id: str,
        interaction: LearningInteraction,
        success: bool,
    ) -> LearningProfile:
        """
        Enregistre le résultat d'une interaction
        d'apprentissage.

        Cette méthode est utilisée lorsqu'AlternIA
        connaît réellement le résultat de l'élève.
        """

        interaction.success = success

        profile = self.get_profile(
            student_id
        )

        profile.register_interaction(
            interaction
        )

        return profile

    # =========================================================
    # CONTEXTE DU PROFIL
    # =========================================================

    def build_profile_context(
        self,
        student_id: str,
    ) -> str:

        profile = self.get_profile(
            student_id
        )

        lines = [
            "PROFIL D'APPRENTISSAGE",
            f"Classe : {profile.student_class}",
            (
                "Langue : "
                + profile.preferred_language
            ),
        ]

        if profile.current_subject:
            lines.append(
                "Matière actuelle : "
                + profile.current_subject
            )

        if profile.current_topic:
            lines.append(
                "Notion actuelle : "
                + profile.current_topic
            )

        if profile.mastered_topics:
            lines.append(
                "Notions maîtrisées : "
                + ", ".join(
                    profile.mastered_topics
                )
            )

        if profile.topics_to_review:
            lines.append(
                "Notions à revoir : "
                + ", ".join(
                    profile.topics_to_review
                )
            )

        if profile.strengths:
            lines.append(
                "Points forts : "
                + ", ".join(
                    profile.strengths
                )
            )

        if profile.weaknesses:
            lines.append(
                "Points faibles : "
                + ", ".join(
                    profile.weaknesses
                )
            )

        lines.extend(
            [
                "",
                "STATISTIQUES",
                (
                    "Questions : "
                    + str(
                        profile.statistics.total_questions
                    )
                ),
                (
                    "Exercices : "
                    + str(
                        profile.statistics.total_exercises
                    )
                ),
                (
                    "Corrections : "
                    + str(
                        profile.statistics.total_corrections
                    )
                ),
            ]
        )

        return "\n".join(lines)