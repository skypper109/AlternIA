import re


class TextCleaner:
    """
    Nettoie le texte extrait des documents scolaires
    sans supprimer leur structure pédagogique.
    """

    def clean(self, text: str) -> str:

        if not text:
            return ""

        text = self._normalize_line_endings(text)

        text = self._remove_page_numbers(text)

        text = self._remove_excessive_spaces(text)

        text = self._normalize_blank_lines(text)

        return text.strip()

    def _normalize_line_endings(
        self,
        text: str,
    ) -> str:

        return text.replace(
            "\r\n",
            "\n",
        ).replace(
            "\r",
            "\n",
        )

    def _remove_page_numbers(
        self,
        text: str,
    ) -> str:

        lines = text.split("\n")

        cleaned_lines = []

        for line in lines:

            stripped = line.strip()

            # Ignore les lignes contenant uniquement
            # un numéro de page.
            if re.fullmatch(
                r"\d+",
                stripped,
            ):
                continue

            cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    def _remove_excessive_spaces(
        self,
        text: str,
    ) -> str:

        lines = text.split("\n")

        cleaned_lines = []

        for line in lines:

            # Remplace plusieurs espaces consécutifs
            # par un seul espace.
            line = re.sub(
                r"[ \t]+",
                " ",
                line,
            )

            cleaned_lines.append(
                line.rstrip()
            )

        return "\n".join(cleaned_lines)

    def _normalize_blank_lines(
        self,
        text: str,
    ) -> str:

        return re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )