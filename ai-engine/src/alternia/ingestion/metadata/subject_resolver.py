import re
import unicodedata


class SubjectResolver:
    """
    Résout la matière scolaire à partir des informations
    disponibles dans un document.

    La résolution est insensible :
    - aux majuscules/minuscules
    - aux accents
    - aux espaces multiples
    """

    SUBJECT_ALIASES = {
        "mathematiques": [
            "mathématiques",
            "mathematique",
            "mathématiques générales",
            "sciences mathématiques",
        ],
        "physique": [
            "physique",
            "sciences physiques",
            "physique-chimie",
        ],
        "chimie": [
            "chimie",
        ],
        "francais": [
            "français",
            "francais",
            "langue française",
        ],
        "anglais": [
            "anglais",
            "english",
        ],
        "histoire": [
            "histoire",
        ],
        "geographie": [
            "géographie",
            "geographie",
        ],
        "philosophie": [
            "philosophie",
        ],
        "svt": [
            "svt",
            "sciences de la vie et de la terre",
        ],
    }

    def resolve(
        self,
        text: str,
        filename: str | None = None,
    ) -> str | None:

        sources = []

        if filename:
            sources.append(filename)

        sources.append(text)

        combined_text = "\n".join(sources)

        normalized = self._normalize(
            combined_text
        )

        for subject, aliases in self.SUBJECT_ALIASES.items():

            for alias in aliases:

                normalized_alias = self._normalize(
                    alias
                )

                pattern = (
                    r"(?<!\w)"
                    + re.escape(normalized_alias)
                    + r"(?!\w)"
                )

                if re.search(
                    pattern,
                    normalized,
                ):
                    return subject

        return None

    @staticmethod
    def _normalize(
        text: str,
    ) -> str:

        # Minuscules
        text = text.lower()

        # Suppression des accents
        text = unicodedata.normalize(
            "NFD",
            text,
        )

        text = "".join(
            char
            for char in text
            if unicodedata.category(char) != "Mn"
        )

        # Normalisation des espaces
        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()