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
            "- Si c'est une question générale de découverte, donne une explication claire et structurée.\n"
            "- S'il s'agit d'une suite, précision ou application ('en quoi c'est utilisé en...', 'pourquoi...', 'donne un exemple'), réponds DIRECTEMENT sur cet aspect sans répéter les définitions déjà données dans les échanges précédents.\n"
            "- Synthèse en 3 à 5 phrases pertinentes + formules si approprié."
        )

        if context:
            return (
                instruction
                + "\n\nContexte pédagogique :\n"
                + context
                + "\n\n(Utilise ces extraits uniquement s'ils répondent précisément à la question de l'élève)."
            )

        return (
            instruction
            + "\n\nContexte pédagogique :\n"
            + "Aucun contexte pédagogique suffisant n'est disponible pour cette question spécifique."
        )