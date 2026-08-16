import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[2]
AI_ENGINE_SRC = ROOT_DIR / "ai-engine" / "src"
BACKEND_DIR = ROOT_DIR / "backend" / "src"

for p in [str(AI_ENGINE_SRC), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from main import app, normalize_student_class


def test_normalize_student_class():
    assert normalize_student_class("10eme") == "10eme"
    assert normalize_student_class("10e") == "10eme"
    assert normalize_student_class("11eme") == "11eme"
    assert normalize_student_class("tse") == "12eme"
    assert normalize_student_class("tsexp") == "12eme"
    assert normalize_student_class("tss") == "12eme"
    assert normalize_student_class("terminale") == "12eme"


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["application"] == "AlternIA"


def test_curriculum_endpoint():
    client = TestClient(app)
    response = client.get("/api/curriculum")
    assert response.status_code == 200
    data = response.json()
    assert data["country"] == "Mali"
    assert len(data["classes"]) == 3


def test_device_info_endpoint():
    client = TestClient(app)
    response = client.get("/api/device/info")
    assert response.status_code == 200
    data = response.json()
    assert data["device_name"] == "AlternIA Box (Mali)"
    assert data["llm_local"] is True


def test_get_learner_profile_endpoint():
    client = TestClient(app)
    response = client.get("/api/learner/student-test-01")
    assert response.status_code == 200
    data = response.json()
    assert data["student_id"] == "student-test-01"
    assert data["total_interactions"] == 0
    assert "mastered_topics" in data
    assert "topics_to_review" in data


def test_record_learner_interaction_endpoint():
    client = TestClient(app)
    payload = {
        "student_class": "10eme",
        "intent": "exercise",
        "subject": "mathematiques",
        "topic": "équations",
        "difficulty": "facile",
        "success": True,
    }
    response = client.post("/api/learner/student-test-01/interaction", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "recorded"

    # Now verify updated profile
    profile_response = client.get("/api/learner/student-test-01")
    assert profile_response.status_code == 200
    profile_data = profile_response.json()
    assert profile_data["total_interactions"] == 1

