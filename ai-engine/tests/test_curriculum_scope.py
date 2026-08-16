import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
AI_ENGINE_SRC = ROOT_DIR / "ai-engine" / "src"
BACKEND_DIR = ROOT_DIR / "backend" / "src"

for p in [str(AI_ENGINE_SRC), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import pytest
from alternia.pedagogical.curriculum_scope import CurriculumScopeChecker
from alternia.pedagogical.prompt_builder import PedagogicalPromptBuilder
from alternia.pedagogical.models import (
    PedagogicalRequest,
    QuestionAnalysis,
    StudentProfile,
)


def test_scope_checker_detects_12eme_topic_for_10eme():
    checker = CurriculumScopeChecker()
    res = checker.check_scope(
        question="Explique-moi les nombres complexes et la forme trigonométrique.",
        student_class="10eme",
        subject="mathematiques",
    )
    assert res.is_higher_level is True
    assert res.target_class == "12eme"
    assert res.topic_name is not None
    assert "Complexes" in res.topic_name
    assert len(res.prerequisites) > 0
    assert len(res.suggested_questions) > 0
    assert res.pedagogical_guidance is not None
    assert "10eme" in res.pedagogical_guidance
    assert "12eme" in res.pedagogical_guidance


def test_scope_checker_detects_integrals_for_10eme():
    checker = CurriculumScopeChecker()
    res = checker.check_scope(
        question="Comment calculer une intégrale par parties ?",
        student_class="10eme",
        subject="mathematiques",
    )
    assert res.is_higher_level is True
    assert res.target_class == "12eme"
    assert res.topic_name is not None
    assert "Intégral" in res.topic_name


def test_scope_checker_detects_11eme_topic_for_10eme():
    checker = CurriculumScopeChecker()
    res = checker.check_scope(
        question="C'est quoi un barycentre de points pondérés ?",
        student_class="10eme",
        subject="mathematiques",
    )
    assert res.is_higher_level is True
    assert res.target_class == "11eme"


def test_scope_checker_allows_same_class_topic():
    checker = CurriculumScopeChecker()
    # Topic in 12eme asked by a 12eme student should NOT be marked as higher level
    res = checker.check_scope(
        question="Comment calculer le module d'un nombre complexe ?",
        student_class="12eme",
        subject="mathematiques",
    )
    assert res.is_higher_level is False

    # Normal 10eme topic asked by 10eme student
    res_10 = checker.check_scope(
        question="Comment résoudre 2x + 5 = 15 ?",
        student_class="10eme",
        subject="mathematiques",
    )
    assert res_10.is_higher_level is False


def test_prompt_builder_injects_scope_guidance():
    builder = PedagogicalPromptBuilder()
    req = PedagogicalRequest(
        question="Explique-moi les nombres complexes",
        profile=StudentProfile(student_class="10eme"),
        analysis=QuestionAnalysis(
            original_question="Explique-moi les nombres complexes",
            intent="explanation",
            student_class="10eme",
            subject="mathematiques",
        ),
        context="",
    )
    prompt = builder.build(req, strategy_instruction="Explication progressive")
    assert "CADRAGE CURRICULAIRE" in prompt
    assert "10eme" in prompt
    assert "12eme" in prompt
    assert "Nombres Complexes" in prompt


def test_scope_checker_detects_congruence_for_10eme():
    checker = CurriculumScopeChecker()
    res = checker.check_scope(
        question="C'est quoi la congruence en arithmétique ?",
        student_class="10eme",
        subject="mathematiques",
    )
    assert res.is_higher_level is True
    assert res.target_class == "12eme"
    assert res.topic_name is not None
    assert "Congruence" in res.topic_name or "Arithmétique" in res.topic_name
    assert len(res.prerequisites) > 0


def test_scope_checker_detects_stereochimie_for_10eme():
    checker = CurriculumScopeChecker()
    res = checker.check_scope(
        question="Qu'est-ce que la stéréochimie et la chiralité des molécules ?",
        student_class="10eme",
        subject="chimie",
    )
    assert res.is_higher_level is True
    assert res.target_class == "12eme"
    assert res.topic_name is not None
    assert "Stéréochimie" in res.topic_name

