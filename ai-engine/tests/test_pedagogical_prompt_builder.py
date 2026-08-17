from alternia.pedagogical.models import (
    PedagogicalRequest,
    QuestionAnalysis,
    StudentProfile,
)
from alternia.pedagogical.prompt_builder import (
    PedagogicalPromptBuilder,
)


def test_prompt_builder_includes_conversation_context():

    request = PedagogicalRequest(
        question="Et comment on la résout ?",

        profile=StudentProfile(
            student_class="10eme",
        ),

        analysis=QuestionAnalysis(
            original_question="Et comment on la résout ?",
            intent="explanation",
            student_class="10eme",
            subject="mathematiques",
        ),

        context=(
            "Une équation est une égalité "
            "contenant une inconnue."
        ),

        conversation_context=(
            "CONTEXTE CONVERSATIONNEL ALTERNIA\n"
            "ÉLÈVE : Qu'est-ce qu'une équation ?\n"
            "ALTERNIA : Une équation contient une inconnue."
        ),
    )

    builder = PedagogicalPromptBuilder()

    prompt = builder.build(
        request=request,
        strategy_instruction=(
            "Explique progressivement la méthode."
        ),
    )

    assert (
        "CONTEXTE CONVERSATIONNEL ALTERNIA"
        in prompt
    )

    assert (
        "Qu'est-ce qu'une équation ?"
        in prompt
    )

    assert (
        "Et comment on la résout ?"
        in prompt
    )

    assert (
        "Une équation est une égalité"
        in prompt
    )


def test_prompt_builder_question_guidance_closed():
    builder = PedagogicalPromptBuilder()
    guidance = builder.detect_question_guidance("Est-ce que les métaux sont conducteurs ?")
    assert guidance is not None
    assert "QUESTION FERMÉE" in guidance
    assert "'Oui', 'Non'" in guidance


def test_prompt_builder_question_guidance_comparison():
    builder = PedagogicalPromptBuilder()
    guidance = builder.detect_question_guidance("Quelle est la différence entre vitesse et accélération ?")
    assert guidance is not None
    assert "COMPARAISON" in guidance


def test_prompt_builder_question_guidance_reexplanation():
    builder = PedagogicalPromptBuilder()
    guidance = builder.detect_question_guidance("Réexplique moi en détail")
    assert guidance is not None
    assert "RÉEXPLICATION" in guidance
    assert "INTERDICTION STRICTE de répéter" in guidance