from alternia.pedagogical.models import (
    StudentProfile,
    QuestionAnalysis,
    PedagogicalRequest,
    PedagogicalResponse,
)


def test_student_profile():

    profile = StudentProfile(
        student_id="student-001",
        student_class="10eme",
        preferred_language="fr",
    )

    assert profile.student_class == "10eme"
    assert profile.preferred_language == "fr"


def test_question_analysis():

    analysis = QuestionAnalysis(
        original_question="Comment résoudre 2x + 5 = 15 ?",
        intent="explanation",
        student_class="10eme",
        subject="mathematiques",
        chapter="algebre",
        lesson="equations",
    )

    assert analysis.intent == "explanation"
    assert analysis.subject == "mathematiques"
    assert analysis.student_class == "10eme"


def test_pedagogical_request():

    profile = StudentProfile(
        student_class="10eme",
    )

    analysis = QuestionAnalysis(
        original_question="Comment résoudre une équation ?",
        intent="explanation",
        student_class="10eme",
        subject="mathematiques",
    )

    request = PedagogicalRequest(
        question="Comment résoudre une équation ?",
        profile=profile,
        analysis=analysis,
        context="Une équation est une égalité contenant une inconnue.",
    )

    assert request.profile.student_class == "10eme"
    assert request.analysis.subject == "mathematiques"
    assert "équation" in request.context


def test_pedagogical_response():

    response = PedagogicalResponse(
        answer="Une équation permet de trouver la valeur de l'inconnue.",
        student_class="10eme",
        subject="mathematiques",
        intent="explanation",
    )

    assert response.student_class == "10eme"
    assert response.subject == "mathematiques"
    assert response.answer != ""
