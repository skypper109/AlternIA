import re


class DocumentCleaner:
    """
    Nettoie le texte extrait des documents scolaires.
    """

    def clean(self, text: str) -> str:

        if not text.strip():
            return ""

        # Normalisation des retours à la ligne
        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")

        # Suppression des espaces multiples
        text = re.sub(
            r"[ \t]+",
            " ",
            text,
        )

        # Suppression des lignes vides répétées
        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        # Nettoyage des espaces autour des lignes
        lines = [
            line.strip()
            for line in text.splitlines()
        ]

        text = "\n".join(lines)

        return text.strip()
