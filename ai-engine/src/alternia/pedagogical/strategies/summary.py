from alternia.pedagogical.models import PedagogicalRequest


class SummaryStrategy:
    """
    Stratégie de résumé.
    """

    name = "summary"

    def generate(
        self,
        request: PedagogicalRequest,
    ) -> str:

        return (
            "Résume le contenu pédagogique pertinent "
            "pour répondre à la question.\n\n"
            "Conserve uniquement les informations essentielles.\n"
            "Respecte les notions et la terminologie du contexte.\n"
            "Structure le résumé de manière claire et concise."
        )
