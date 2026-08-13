from typing import Any

from alternia.context.models import (
    ContextSource,
    PedagogicalContext,
)


class ContextBuilder:
    """
    Transforme les résultats du SemanticRetriever
    en contexte pédagogique exploitable par le moteur IA.
    """

    def __init__(
        self,
        max_sources: int = 5,
        min_score: float = 0.0,
    ):
        self.max_sources = max_sources
        self.min_score = min_score

    def build(
        self,
        query: str,
        results: list[Any],
        student_class: str,
        subject: str | None = None,
    ) -> PedagogicalContext:

        sources = []

        for result in results:

            payload = self._extract_payload(result)

            if not payload:
                continue

            # -----------------------------------------
            # Vérification classe
            # -----------------------------------------

            result_class = payload.get(
                "student_class"
            )

            if result_class != student_class:
                continue

            # -----------------------------------------
            # Vérification matière
            # -----------------------------------------

            result_subject = payload.get(
                "subject"
            )

            if (
                subject is not None
                and result_subject != subject
            ):
                continue

            # -----------------------------------------
            # Score
            # -----------------------------------------

            score = float(
                getattr(result, "score", 0.0)
            )

            if score < self.min_score:
                continue

            # -----------------------------------------
            # Contenu
            # -----------------------------------------

            content = payload.get(
                "content",
                "",
            )

            if not content.strip():
                continue

            # -----------------------------------------
            # Création source
            # -----------------------------------------

            source = ContextSource(
                chunk_id=str(
                    payload.get(
                        "chunk_id",
                        "",
                    )
                ),
                content=content.strip(),
                score=score,
                student_class=result_class,
                subject=result_subject,
                chapter=payload.get(
                    "chapter"
                ),
                lesson=payload.get(
                    "lesson"
                ),
                source_document=payload.get(
                    "source_document"
                ),
                metadata=payload,
            )

            sources.append(source)

        # ---------------------------------------------
        # Tri par pertinence
        # ---------------------------------------------

        sources.sort(
            key=lambda source: source.score,
            reverse=True,
        )

        # ---------------------------------------------
        # Suppression des doublons
        # ---------------------------------------------

        sources = self._remove_duplicates(
            sources
        )

        # ---------------------------------------------
        # Top-K
        # ---------------------------------------------

        sources = sources[
            : self.max_sources
        ]

        # ---------------------------------------------
        # Construction du texte
        # ---------------------------------------------

        context_text = self._build_text(
            sources
        )

        return PedagogicalContext(
            query=query,
            student_class=student_class,
            subject=subject,
            sources=sources,
            context_text=context_text,
            max_sources=self.max_sources,
        )

    @staticmethod
    def _extract_payload(
        result: Any,
    ) -> dict[str, Any] | None:

        payload = getattr(
            result,
            "payload",
            None,
        )

        if payload is None:
            return None

        if not isinstance(
            payload,
            dict,
        ):
            return None

        return payload

    @staticmethod
    def _remove_duplicates(
        sources: list[ContextSource],
    ) -> list[ContextSource]:

        seen = set()

        unique_sources = []

        for source in sources:

            key = source.chunk_id

            if key in seen:
                continue

            seen.add(key)

            unique_sources.append(
                source
            )

        return unique_sources

    @staticmethod
    def _build_text(
        sources: list[ContextSource],
    ) -> str:

        if not sources:
            return ""

        sections = []

        for index, source in enumerate(
            sources,
            start=1,
        ):

            header = (
                f"SOURCE {index}\n"
                f"Classe : {source.student_class}\n"
                f"Matière : {source.subject}\n"
            )

            if source.chapter:
                header += (
                    f"Chapitre : "
                    f"{source.chapter}\n"
                )

            if source.lesson:
                header += (
                    f"Leçon : "
                    f"{source.lesson}\n"
                )

            sections.append(
                header
                + "\n"
                + source.content
            )

        return (
            "CONTEXTE PÉDAGOGIQUE ALTERNIA\n\n"
            + "\n\n".join(sections)
            + "\n\nFIN DU CONTEXTE"
        )