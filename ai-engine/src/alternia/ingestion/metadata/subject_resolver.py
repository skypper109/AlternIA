import re
import unicodedata

from alternia.core.models import Subject


class SubjectResolver:
    """
    Résout la matière scolaire à partir des informations
    disponibles dans un document.

    La résolution est insensible :
    - aux majuscules/minuscules ;
    - aux accents ;
    - aux espaces multiples.

    Le résultat est toujours une valeur du modèle Subject
    d'AlternIA.
    """

    SUBJECT_ALIASES: dict[Subject, list[str]] = {
        Subject.MATHEMATIQUES: [
            "mathématiques",
            "mathematique",
            "mathématiques générales",
            "sciences mathématiques",
            "sciences mathematiques",
            "mathematics",
            "mahts",
            "math",
            "maths",
        ],

        Subject.PHYSIQUE: [
            "physique",
            "sciences physiques",
            "sciences-physiques",
            "physique-chimie",
            "physique chimie",
            "physics chemistry",
            "physics-chemistry",
            "phy-chi",
            "phy chi",
        ],

        Subject.CHIMIE: [
            "chimie",
        ],

        Subject.BIOLOGIE: [
            "biologie",
            "sciences naturelles",
            "sciences-naturelles",
            "sc-nat",
            "bio",
        ],

        Subject.FRANCAIS: [
            "français",
            "francais",
            "langue française",
            "langue francaise",
            "dictée",
            "dictee",
            "dict-quest",
            "dict quest",
            "rédaction",
            "redaction",
            "grammaire",
        ],

        Subject.ANGLAIS: [
            "anglais",
            "english",
            "dictation",
        ],

        Subject.HISTOIRE: [
            "histoire",
            "histoire-géographie",
            "histoire-geographie",
            "histoire-geo",
            "hist-geo",
            "history-geography",
        ],

        Subject.GEOGRAPHIE: [
            "géographie",
            "geographie",
        ],

        Subject.ECM: [
            "éducation civique et morale",
            "education civique et morale",
            "éducation civique",
            "education civique",
            "ecm",
            "civique",
            "morale",
        ],

        Subject.AGRICULTURE: [
            "agriculture",
            "agronomie",
            "agri",
        ],

        Subject.DESSIN: [
            "arts plastiques",
            "dessin",
        ],

        Subject.SCIENCES: [
            "sciences",
            "sciences de la vie et de la terre",
            "svt",
        ],
    }

    def resolve(
        self,
        text: str,
        filename: str | None = None,
    ) -> Subject | None:
        """
        Détecte la matière du document.

        Priorité :
        1. nom du fichier ;
        2. contenu du document.

        Retourne :
            Subject ou None
        """

        sources: list[str] = []

        if filename:
            sources.append(filename)

        if text:
            sources.append(text)

        if not sources:
            return None

        combined_text = "\n".join(sources)

        normalized = self._normalize(
            combined_text
        )

        # Les alias les plus spécifiques sont recherchés
        # en premier afin d'éviter les collisions.
        candidates: list[
            tuple[Subject, str]
        ] = []

        for subject, aliases in self.SUBJECT_ALIASES.items():
            for alias in aliases:
                candidates.append(
                    (
                        subject,
                        self._normalize(alias),
                    )
                )

        candidates.sort(
            key=lambda item: len(item[1]),
            reverse=True,
        )

        for subject, normalized_alias in candidates:

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
        """
        Normalise un texte avant comparaison.
        """

        text = text.lower()

        text = unicodedata.normalize(
            "NFD",
            text,
        )

        text = "".join(
            char
            for char in text
            if unicodedata.category(char) != "Mn"
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()