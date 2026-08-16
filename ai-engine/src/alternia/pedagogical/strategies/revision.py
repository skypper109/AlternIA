from alternia.pedagogical.models import PedagogicalRequest


class RevisionStrategy:
    """
    Stratégie de révision.
    """

    name = "revision"

    def generate(
        self,
        request: PedagogicalRequest,
    ) -> str:

        return (
            "Construis une synthèse de révision adaptée "
            "à la classe de l'élève.\n\n"
            "Présente uniquement les notions essentielles "
            "présentes dans le contexte pédagogique.\n"
            "Organise-les de manière claire.\n"
            "Fais ressortir les définitions, règles, formules "
            "ou méthodes importantes.\n"
            "Termine par une courte liste des éléments "
            "à retenir."
        )