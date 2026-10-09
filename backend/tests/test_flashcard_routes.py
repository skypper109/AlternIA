"""
Tests automatisés pour l'API Flashcards Leitner IA.
Vérifie la génération dynamique de cartes de révision.
"""

from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from backend.src.main import app

client = TestClient(app)


def test_flashcards_generate_curated_fallback():
    """Vérifie que l'endpoint retourne les cartes du programme même sans LLM."""
    response = client.post(
        "/api/education/flashcards/generate",
        json={
            "subject": "Mathématiques",
            "class_level": "12eme",
            "count": 5,
        },
    )
    assert response.status_code == 200
    cards = response.json()
    assert isinstance(cards, list)
    assert len(cards) >= 3
    for card in cards:
        assert "front" in card
        assert "back" in card
        assert "concept" in card
        assert card["subject"] == "Mathématiques"
        assert card["box"] == 1


def test_flashcards_generate_with_orchestrator_process_message():
    """Vérifie l'intégration avec process_message de l'orchestrateur."""
    mock_ai_json = (
        '[\n'
        '  {"front": "Question 1", "back": "Reponse 1", "concept": "Concept 1"},\n'
        '  {"front": "Question 2", "back": "Reponse 2", "concept": "Concept 2"},\n'
        '  {"front": "Question 3", "back": "Reponse 3", "concept": "Concept 3"}\n'
        ']'
    )

    with patch("backend.src.routes.flashcard_routes.get_orchestrator") as mock_get_orch:
        mock_orch = AsyncMock()
        mock_orch.process_message.return_value = {"content": mock_ai_json}
        mock_get_orch.return_value = mock_orch

        response = client.post(
            "/api/education/flashcards/generate",
            json={
                "subject": "Physique-Chimie",
                "class_level": "11eme",
                "count": 3,
            },
        )
        assert response.status_code == 200
        cards = response.json()
        assert len(cards) == 3
        assert cards[0]["front"] == "Question 1"
        assert cards[0]["back"] == "Reponse 1"
        assert cards[0]["concept"] == "Concept 1"
        assert cards[0]["subject"] == "Physique-Chimie"
        mock_orch.process_message.assert_awaited_once()


def test_flashcards_def_curriculum():
    """Vérifie que les élèves de DEF (9ème année) reçoivent des notions spécifiques de DEF (Pythagore, Thalès, P=mg)."""
    from backend.src.routes.flashcard_routes import _get_curated_cards
    cards = _get_curated_cards(subject="Mathématiques", class_level="def", count=3, now_iso="2026-10-09T00:00:00")
    assert len(cards) == 3
    assert cards[0]["classLevel"] == "def"
    assert "Pythagore" in cards[0]["front"] or "Pythagore" in cards[0]["concept"]


def test_flashcards_philosophie_curriculum():
    """Vérifie que la Philosophie génère bien des notions philosophiques et non des dérivées mathématiques."""
    from backend.src.routes.flashcard_routes import _get_curated_cards
    cards = _get_curated_cards(subject="Philosophie", class_level="12eme", count=3, now_iso="2026-10-09T00:00:00")
    assert len(cards) == 3
    assert any("Freud" in (c["front"] + c["back"]) or "Sartre" in (c["front"] + c["back"]) or "Rousseau" in (c["front"] + c["back"]) for c in cards)

