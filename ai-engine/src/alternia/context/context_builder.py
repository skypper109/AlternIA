import time
from typing import Any

from alternia.context.models import (
    ContextSource,
    PedagogicalContext,
)


class ContextBuilder:
    """
    Transforme les résultats du retrieval en contexte
    pédagogique exploitable par AlternIA.

    Pipeline :

        retrieval
            ↓
        validation metadata
            ↓
        score filtering
            ↓
        nettoyage
            ↓
        déduplication
            ↓
        Top-K
            ↓
        contexte pédagogique
    """

    def __init__(
        self,
        max_sources: int = 2,
        min_score: float = 0.15,
        max_content_length: int = 350,
    ):
        self.max_sources = max_sources
        self.min_score = min_score
        self.max_content_length = max_content_length

    # =========================================================
    # BUILD
    # =========================================================

    def build(
        self,
        query: str,
        results: list[Any],
        student_class: str,
        subject: str | None = None,
    ) -> PedagogicalContext:

        t0_ctx = time.perf_counter()
        sources: list[ContextSource] = []

        for result in results:

            payload = self._extract_payload(
                result
            )

            if not payload:
                continue

            result_class = str(payload.get("student_class", "")).strip().lower()
            s_cls = str(student_class).strip().lower()

            allowed_classes = {
                "10eme": ["10eme", "10"],
                "11eme": ["10eme", "11eme", "10", "11"],
                "12eme": ["10eme", "11eme", "12eme", "10", "11", "12", "terminale", "tse", "tsexp", "tseco", "tss", "tll"],
            }.get(s_cls, [s_cls])

            if result_class and result_class not in allowed_classes:
                continue

            result_subject = str(payload.get("subject", "")).strip().lower()

            # Compatibilité étendue des matières (les manuels de 10ème sont souvent catégorisés 'sciences')
            if subject is not None:
                subj_norm = str(subject).strip().lower()
                subject_compatibility = {
                    "mathematiques": {"mathematiques", "maths", "sciences", "autre", ""},
                    "maths": {"mathematiques", "maths", "sciences", "autre", ""},
                    "physique": {"physique", "chimie", "physique-chimie", "sciences", "autre", ""},
                    "chimie": {"chimie", "physique", "physique-chimie", "sciences", "autre", ""},
                    "physique-chimie": {"physique", "chimie", "physique-chimie", "sciences", "autre", ""},
                    "biologie": {"biologie", "svt", "sciences", "autre", ""},
                    "svt": {"biologie", "svt", "sciences", "autre", ""},
                    "sciences": {"sciences", "mathematiques", "physique", "chimie", "biologie", "svt", "autre", ""},
                    "francais": {"francais", "lettres", "litterature", "linguistique", "autre", ""},
                    "philosophie": {"philosophie", "lettres", "autre", ""},
                    "histoire": {"histoire", "geographie", "histoire-geo", "autre", ""},
                    "geographie": {"geographie", "histoire", "histoire-geo", "geologie", "autre", ""},
                    "economie": {"economie", "seco", "comptabilite", "autre", ""},
                    "comptabilite": {"comptabilite", "economie", "seco", "autre", ""},
                    "linguistique": {"linguistique", "francais", "lettres", "autre", ""},
                    "sociologie": {"sociologie", "philosophie", "histoire", "autre", ""},
                    "anglais": {"anglais", "langues", "autre", ""},
                }

                allowed_subj = subject_compatibility.get(subj_norm, {subj_norm, "sciences", "autre", ""})
                if result_subject and result_subject not in allowed_subj:
                    continue

            score = float(
                getattr(
                    result,
                    "score",
                    0.0,
                )
            )

            if score < self.min_score:
                continue

            content = self._clean_content(
                payload.get(
                    "content",
                    "",
                )
            )

            if not content:
                continue

            if (
                self.max_content_length > 0
                and len(content)
                > self.max_content_length
            ):
                content = (
                    content[
                        : self.max_content_length
                    ].rstrip()
                    + "..."
                )

            source = ContextSource(
                chunk_id=str(
                    payload.get(
                        "chunk_id",
                        "",
                    )
                ),
                content=content,
                score=score,
                student_class=student_class,
                subject=result_subject or subject,
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

            sources.append(
                source
            )

        # =====================================================
        # TRI
        # =====================================================

        sources.sort(
            key=lambda source: source.score,
            reverse=True,
        )

        # =====================================================
        # DÉDUPLICATION
        # =====================================================

        sources = self._remove_duplicates(
            sources
        )

        # =====================================================
        # TOP-K
        # =====================================================

        sources = sources[
            : self.max_sources
        ]

        # =====================================================
        # TEXTE
        # =====================================================

        context_text = self._build_text(
            sources
        )

        dt_ctx = time.perf_counter() - t0_ctx
        print(f"\033[36m⏱️  [context_builder.py]\033[0m Contexte pédagogique assemblé ({len(sources)} sources, {len(context_text)} chars) en \033[1;33m{dt_ctx:.4f}s\033[0m")

        return PedagogicalContext(
            query=query,
            student_class=student_class,
            subject=subject,
            sources=sources,
            context_text=context_text,
            max_sources=self.max_sources,
        )

    # =========================================================
    # PAYLOAD
    # =========================================================

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

    # =========================================================
    # NETTOYAGE
    # =========================================================

    @staticmethod
    def _clean_content(
        content: Any,
    ) -> str:

        if not isinstance(
            content,
            str,
        ):
            return ""

        lines = []

        for line in content.splitlines():

            cleaned = " ".join(
                line.split()
            )

            if cleaned:
                lines.append(
                    cleaned
                )

        return "\n".join(
            lines
        ).strip()

    # =========================================================
    # DÉDUPLICATION
    # =========================================================

    @staticmethod
    def _remove_duplicates(
        sources: list[ContextSource],
    ) -> list[ContextSource]:

        seen_chunk_ids: set[str] = set()
        seen_content: set[str] = set()

        unique_sources = []

        for source in sources:

            if source.chunk_id in seen_chunk_ids:
                continue

            normalized_content = (
                " ".join(
                    source.content.lower().split()
                )
            )

            if normalized_content in seen_content:
                continue

            seen_chunk_ids.add(
                source.chunk_id
            )

            seen_content.add(
                normalized_content
            )

            unique_sources.append(
                source
            )

        return unique_sources

    # =========================================================
    # CONTEXTE TEXTE
    # =========================================================

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
            header = f"[Extrait {index}"
            if source.subject:
                header += f" - {str(source.subject).capitalize()}"
            if source.chapter and str(source.chapter).lower() not in {"non défini", "none", ""}:
                header += f" | {source.chapter}"
            header += "]"
            sections.append(f"{header} : {source.content}")

        return "\n".join(sections)