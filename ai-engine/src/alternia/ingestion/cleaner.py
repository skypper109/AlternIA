import re


class TextCleaner:
    """
    Nettoie le texte extrait des documents scolaires.

    Important :
    le nettoyage ne doit pas réécrire le contenu.
    Il supprime uniquement les artefacts techniques
    provenant de l'extraction PDF.
    """

    @staticmethod
    def clean(text: str) -> str:

        if not text:
            return ""

        # Normalisation des espaces
        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")

        # Supprime les espaces en fin de ligne
        text = re.sub(
            r"[ \t]+\n",
            "\n",
            text,
        )

        # Plusieurs espaces → un seul
        text = re.sub(
            r"[ \t]+",
            " ",
            text,
        )

        # Maximum deux retours à la ligne
        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        # Nettoyage début/fin
        text = text.strip()

        return text