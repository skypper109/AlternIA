"""
Tests d'intégration automatisés pour l'API CultureLens & Patrimoine du Mali.
Vérifie la présence et le bon fonctionnement de tous les endpoints :
- Santé et statistiques
- Monuments (avec priorité Bamako)
- Identification CultureLens
- Guide culturel RAG
- Packs hors ligne
- Figures, contes et proverbes
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.src.main import app

client = TestClient(app)


def test_culture_health():
    response = client.get("/api/v1/culture/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["totalMonuments"] >= 19
    assert data["bamakoMonuments"] >= 12


def test_get_monuments_bamako():
    response = client.get("/api/v1/culture/monuments?ville=Bamako")
    assert response.status_code == 200
    monuments = response.json()
    assert len(monuments) >= 12
    ids = [m["id"] for m in monuments]
    assert "monument_independance_bamako" in ids
    assert "monument_tour_afrique_bamako" in ids
    assert "monument_paix_bamako" in ids
    assert "monument_musee_national_bamako" in ids


def test_get_monument_detail():
    response = client.get("/api/v1/culture/monuments/monument_independance_bamako")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "monument_independance_bamako"
    assert data["ville"] == "Bamako"
    assert "obelisque" in data["keywords"]
    assert len(data["detectionFeatures"]) > 0


def test_culture_identify():
    # Identification avec mot-clé ou indice
    payload = {
        "keywords": ["independance", "obelisque", "bamako"],
        "latitude": 12.6392,
        "longitude": -8.0029,
    }
    response = client.post("/api/v1/culture/identify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["target"]["id"] == "monument_independance_bamako"
    assert data["confidence"] > 0.85
    assert len(data["recognizedFeatures"]) > 0


def test_culture_ask_rag():
    payload = {
        "question": "Qui a construit la Tour de l'Afrique et pourquoi ce monument est-il important à Bamako ?",
        "monument_id": "monument_tour_afrique_bamako",
    }
    response = client.post("/api/v1/culture/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reponse" in data or "answer" in data
    assert len(data["sources"]) > 0
    assert data["ragVerified"] is True


def test_culture_packs():
    response = client.get("/api/v1/culture/packs")
    assert response.status_code == 200
    packs = response.json()
    assert len(packs) >= 4
    pack_ids = [p["id"] for p in packs]
    assert "pack_bamako_capitale" in pack_ids

    # Téléchargement du pack Bamako
    resp_dl = client.get("/api/v1/culture/packs/pack_bamako_capitale/download")
    assert resp_dl.status_code == 200
    bundle = resp_dl.json()
    assert bundle["packId"] == "pack_bamako_capitale"
    assert len(bundle["monuments"]) >= 12


def test_culture_figures_and_proverbs():
    resp_fig = client.get("/api/v1/culture/figures")
    assert resp_fig.status_code == 200
    assert len(resp_fig.json()) >= 5

    resp_prov = client.get("/api/v1/culture/proverbs")
    assert resp_prov.status_code == 200
    assert len(resp_prov.json()) >= 5
