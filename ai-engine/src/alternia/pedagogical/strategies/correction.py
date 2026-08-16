from alternia.pedagogical.models import PedagogicalRequest


class CorrectionStrategy:
    """
    Stratégie de correction pédagogique.
    """

    name = "correction"

    def generate(
        self,
        request: PedagogicalRequest,
    ) -> str:

        return (
            "Analyse la réponse ou la démarche de l'élève.\n\n"
            "Identifie précisément les erreurs éventuelles.\n"
            "Explique pourquoi chaque erreur est incorrecte.\n"
            "Montre ensuite la méthode correcte étape par étape.\n"
            "Si la réponse de l'élève est correcte, explique "
            "brièvement pourquoi elle est correcte."
        )