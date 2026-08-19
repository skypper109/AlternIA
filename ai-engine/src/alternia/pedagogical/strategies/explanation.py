from alternia.pedagogical.models import PedagogicalRequest


class ExplanationStrategy:
    """
    Stratégie pédagogique utilisée lorsqu'un élève
    demande une explication ou cherche à comprendre
    une notion.

    La stratégie produit l'instruction pédagogique
    ainsi que le contexte disponible afin de conserver
    la compatibilité avec l'ancien moteur pendant
    la migration vers le PromptBuilder.
    """

    name = "explanation"

    def generate(
        self,
        request: PedagogicalRequest,
    ) -> str:
        context = request.context.strip()

        instruction = (
            "EXPLICATION PÉDAGOGIQUE DIRECTE\n\n"
            "- Réponds directement et avec clarté à la question posée par l'élève.\n"
            "- Fonde ton explication sur les définitions et formules officielles du cours.\n"
            "- Reste synthétique (2 à 4 phrases denses, claires et bienveillantes)."
        )

        if context:
            return (
                instruction
                + "\n\nContexte pédagogique :\n"
                + context
            )

        return (
            instruction
            + "\n\nContexte pédagogique :\n"
            + "Aucun contexte pédagogique suffisant n'est disponible pour cette question spécifique."
        )