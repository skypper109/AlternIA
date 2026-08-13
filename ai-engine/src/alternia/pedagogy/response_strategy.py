from enum import Enum


class ResponseStrategy(str, Enum):
    """
    Stratégie pédagogique utilisée par AlternIA
    pour construire la réponse destinée à l'élève.
    """

    DIRECT = "direct"

    STEP_BY_STEP = "step_by_step"

    EXAMPLE = "example"

    EXERCISE = "exercise"

    CORRECTION = "correction"

    REVISION = "revision"
