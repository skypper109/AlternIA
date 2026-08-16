from alternia.learner.profile import LearningProfile


class LearningAdaptationService:
    """
    Détermine les adaptations pédagogiques à appliquer
    en fonction du profil d'apprentissage de l'élève.
    """

    def build_adaptation_context(
        self,
        profile: LearningProfile,
        *,
        topic: str | None = None,
    ) -> str:
        """
        Construit le contexte pédagogique dynamique
        utilisé par le PromptBuilder.
        """

        lines: list[str] = [
            "ADAPTATION PÉDAGOGIQUE",
            "======================",
        ]

        if profile.strengths:
            lines.extend(
                [
                    "",
                    "POINTS FORTS",
                    ", ".join(profile.strengths),
                ]
            )

        if profile.weaknesses:
            lines.extend(
                [
                    "",
                    "POINTS FAIBLES",
                    ", ".join(profile.weaknesses),
                ]
            )

        if profile.mastered_topics:
            lines.extend(
                [
                    "",
                    "NOTIONS MAÎTRISÉES",
                    ", ".join(
                        profile.mastered_topics
                    ),
                ]
            )

        if profile.topics_to_review:
            lines.extend(
                [
                    "",
                    "NOTIONS À REVOIR",
                    ", ".join(
                        profile.topics_to_review
                    ),
                ]
            )

        if topic:
            progress = profile.topic_progress.get(
                topic
            )

            if progress is not None:
                lines.extend(
                    [
                        "",
                        "PROGRESSION SUR LA NOTION",
                        f"Notion : {topic}",
                        (
                            f"Tentatives : "
                            f"{progress.attempts}"
                        ),
                        (
                            f"Réussites : "
                            f"{progress.successes}"
                        ),
                        (
                            f"Échecs : "
                            f"{progress.failures}"
                        ),
                        (
                            f"Maîtrise : "
                            f"{progress.mastery_score:.2f}"
                        ),
                    ]
                )

        lines.extend(
            [
                "",
                "CONSIGNES D'ADAPTATION",
                self._build_instruction(
                    profile=profile,
                    topic=topic,
                ),
            ]
        )

        return "\n".join(lines)

    @staticmethod
    def _build_instruction(
        profile: LearningProfile,
        topic: str | None,
    ) -> str:

        instructions: list[str] = []

        if topic and topic in profile.topics_to_review:
            instructions.append(
                "Reprendre les bases de la notion "
                "avant d'introduire des concepts avancés."
            )

            instructions.append(
                "Donner des explications progressives "
                "et des exemples simples."
            )

        if (
            topic
            and topic in profile.mastered_topics
        ):
            instructions.append(
                "L'élève maîtrise déjà cette notion."
            )

            instructions.append(
                "Éviter de répéter inutilement "
                "les définitions élémentaires."
            )

            instructions.append(
                "Proposer si pertinent un niveau "
                "de difficulté légèrement supérieur."
            )

        if profile.weaknesses:
            instructions.append(
                "Accorder une attention particulière "
                "aux difficultés connues de l'élève."
            )

        if not instructions:
            instructions.append(
                "Adapter progressivement la réponse "
                "au niveau de l'élève."
            )

        return "\n".join(
            f"- {instruction}"
            for instruction in instructions
        )