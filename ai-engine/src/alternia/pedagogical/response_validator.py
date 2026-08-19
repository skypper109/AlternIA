import re


class PedagogicalResponseValidator:
    """
    Valide et assainit la réponse générée par le LLM.
    Nettoie les artefacts de formatage (***), balises internes et fuites de métadonnées.
    """

    @classmethod
    def sanitize(cls, text: str) -> str:
        """Nettoie les artefacts de formatage Markdown et les balises parasites."""
        if not text:
            return ""

        t = text.strip()

        # Nettoyage des balises de réflexion ou internes
        t = re.sub(r"<think>[\s\S]*?</think>", "", t, flags=re.IGNORECASE)
        t = re.sub(r"</?think>", "", t, flags=re.IGNORECASE)

        # Nettoyage et traduction des en-têtes en anglais fréquents dans les balises ***...*** ou **...**
        en_fr_headers = [
            (r"\*{2,3}\s*step\s*1\s*(?::|-)?\s*(?:formula|explication|method|méthode)?\s*(?::|-)?\s*\*{2,3}", "1ère étape : "),
            (r"\*{2,3}\s*step\s*2\s*(?::|-)?\s*(?:formula|explication|method|méthode)?\s*(?::|-)?\s*\*{2,3}", "2ème étape : "),
            (r"\*{2,3}\s*step\s*3\s*(?::|-)?\s*(?:formula|explication|method|méthode)?\s*(?::|-)?\s*\*{2,3}", "3ème étape : "),
            (r"\*{2,3}\s*step\s*(\d+)\s*(?::|-)?\s*\*{2,3}", r"Étape \1 : "),
            (r"\*{2,3}\s*formula\s*(?::|-)?\s*\*{2,3}", "Formule : "),
            (r"\*{2,3}\s*definition\s*(?::|-)?\s*\*{2,3}", "Définition : "),
            (r"\*{2,3}\s*summary\s*(?::|-)?\s*\*{2,3}", "En résumé : "),
            (r"\*{2,3}\s*explanation\s*(?::|-)?\s*\*{2,3}", "Explication : "),
            (r"\*{2,3}\s*key points?\s*(?::|-)?\s*\*{2,3}", "Points clés : "),
            (r"\*{2,3}\s*example\s*(?::|-)?\s*\*{2,3}", "Exemple : "),
            (r"\*{2,3}\s*note\s*(?::|-)?\s*\*{2,3}", "Remarque : "),
            (r"\*{2,3}\s*hint\s*(?::|-)?\s*\*{2,3}", "Indice : "),
        ]
        for pattern, repl in en_fr_headers:
            t = re.sub(pattern, repl, t, flags=re.IGNORECASE)

        # Nettoyage des triples astérisques restants : ***texte*** -> **texte**
        t = re.sub(r"\*{3,}([^*]+)\*{3,}", r"**\1**", t)
        t = t.replace("***", "")

        # Nettoyage des espaces résiduels
        t = re.sub(r"[ \t]+", " ", t)
        t = re.sub(r"\n{3,}", "\n\n", t)

        return t.strip()

    def validate(
        self,
        answer: str,
        *,
        question: str,
        context: str = "",
    ) -> str:

        if answer is None:
            raise ValueError(
                "Le LLM a retourné une réponse vide."
            )

        answer = self.sanitize(answer)

        if not answer:
            raise ValueError(
                "Le LLM a retourné une réponse vide."
            )

        # Protection contre certaines réponses manifestement internes
        forbidden_markers = (
            "REQUÊTE PÉDAGOGIQUE ALTERNIA",
            "STRATÉGIE PÉDAGOGIQUE",
            "INSTRUCTION FINALE",
        )

        for marker in forbidden_markers:
            if marker in answer:
                raise ValueError(
                    "La réponse contient des informations "
                    "internes au système pédagogique."
                )

        return answer