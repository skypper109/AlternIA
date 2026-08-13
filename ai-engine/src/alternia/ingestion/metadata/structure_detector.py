import re

from .structure import PedagogicalMetadata


class StructureDetector:
    """
    Détecte la structure pédagogique d'un texte scolaire.

    Première version :
    - classe
    - matière
    - chapitre
    - leçon
    - section
    """

    CLASS_PATTERNS = [
        (
            re.compile(
                r"\b(?:classe\s+de\s+)?10(?:e|ème|eme)\b",
                re.IGNORECASE,
            ),
            "10eme",
        ),
        (
            re.compile(
                r"\b(?:classe\s+de\s+)?11(?:e|ème|eme)\b",
                re.IGNORECASE,
            ),
            "11eme",
        ),
        (
            re.compile(
                r"\b(?:classe\s+de\s+)?12(?:e|ème|eme)\b",
                re.IGNORECASE,
            ),
            "12eme",
        ),
    ]

    def detect_class(
        self,
        text: str,
    ) -> str | None:

        for pattern, student_class in self.CLASS_PATTERNS:

            if pattern.search(text):
                return student_class

        return None

    def detect_chapter(
        self,
        line: str,
    ) -> str | None:

        pattern = re.compile(
            r"^\s*"
            r"(?:CHAPITRE|CHAPTER)"
            r"\s*"
            r"(?:[IVXLCDM\d]+)?"
            r"\s*"
            r"[:\-–.]?"
            r"\s*(.+?)"
            r"\s*$",
            re.IGNORECASE,
        )

        match = pattern.match(line)

        if not match:
            return None

        return self._normalize_title(
            match.group(1)
        )

    def detect_lesson(
        self,
        line: str,
    ) -> str | None:

        pattern = re.compile(
            r"^\s*"
            r"(?:LEÇON|LECON|LESSON)"
            r"\s*"
            r"(?:[IVXLCDM\d]+)?"
            r"\s*"
            r"[:\-–.]?"
            r"\s*(.+?)"
            r"\s*$",
            re.IGNORECASE,
        )

        match = pattern.match(line)

        if not match:
            return None

        return self._normalize_title(
            match.group(1)
        )

    def detect_section(
        self,
        line: str,
    ) -> str | None:

        pattern = re.compile(
            r"^\s*"
            r"(?:(?:\d+\.)+\s*)?"
            r"(.+?)"
            r"\s*$",
            re.IGNORECASE,
        )

        match = pattern.match(line)

        if not match:
            return None

        title = match.group(1).strip()

        if not title:
            return None

        return self._normalize_title(title)

    def detect(
        self,
        text: str,
    ) -> PedagogicalMetadata:

        metadata = PedagogicalMetadata()

        metadata.student_class = self.detect_class(text)

        lines = text.splitlines()

        for line in lines:

            line = line.strip()

            if not line:
                continue

            chapter = self.detect_chapter(line)

            if chapter:
                metadata.chapter = chapter
                continue

            lesson = self.detect_lesson(line)

            if lesson:
                metadata.lesson = lesson
                continue

        return metadata

    @staticmethod
    def _normalize_title(
        title: str,
    ) -> str:

        title = title.strip()

        title = re.sub(
            r"\s+",
            " ",
            title,
        )

        return title.lower()