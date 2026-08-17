"""
Tests automatisés des APIs du portail Alta et de l'intégration base de données alta_db.
"""

from fastapi.testclient import TestClient
from backend.src.main import app
from backend.src.db.database import init_db

client = TestClient(app)


def setup_module():
    """Initialise la base de données de test."""
    init_db()


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["application"] == "AlternIA"


def test_auth_connexion_directeur():
    response = client.post(
        "/api/auth/connexion",
        json={"email": "directeur@altern.ia", "mot_de_passe": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["succes"] is True
    assert "token" in data
    assert data["utilisateur"]["email"] == "directeur@altern.ia"
    assert data["utilisateur"]["role"] == "admin_ecole"


def test_auth_connexion_parent():
    response = client.post(
        "/api/auth/connexion",
        json={"email": "parent@altern.ia", "mot_de_passe": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["succes"] is True
    assert data["utilisateur"]["role"] == "parent"


def test_liste_boitiers():
    response = client.get("/api/boitiers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    premier_boitier = data[0]
    assert "numeroSerie" in premier_boitier
    assert "statut" in premier_boitier
    assert "batterie" in premier_boitier


def test_sync_boitier():
    response = client.post("/api/boitiers/box-alta-01/sync", json={"force": True})
    assert response.status_code == 200
    data = response.json()
    assert data["succes"] is True
    assert data["statut"] == "synchronise"


def test_liste_apprenants():
    response = client.get("/api/apprenants")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any("Diallo" in a["nom"] for a in data)


def test_insights():
    response = client.get("/api/insights")
    assert response.status_code == 200
    data = response.json()
    assert "notionsCritiques" in data
    assert "kpis" in data
    assert len(data["notionsCritiques"]) >= 1


def test_statistiques():
    response = client.get("/api/statistiques")
    assert response.status_code == 200
    data = response.json()
    assert "totalHeuresApprentissage" in data
    assert "repartitionMatieres" in data


def test_avatars_vivienne():
    response = client.get("/api/avatars")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    noms = [av["nom"] for av in data]
    assert any("Vivienne" in nom for nom in noms)


def test_alertes_and_resolve():
    response = client.get("/api/alertes")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        alerte_id = data[0]["id"]
        res_response = client.put(f"/api/alertes/{alerte_id}/resoudre")
        assert res_response.status_code == 200
        assert res_response.json()["resolu"] is True


def test_spa_index_serving():
    # Test d'accès aux routes Angular clientes
    response = client.get("/etablissement/tableau-de-bord")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
