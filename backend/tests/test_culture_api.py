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


def test_create_and_moderate_proverbe_contribution():
    payload = {
        "type_contenu": "proverbe",
        "texte": "Dɔɔnin dɔɔnin, kɔnɔnin b'a ɲaa da.",
        "texte_original": "Dɔɔnin dɔɔnin, kɔnɔnin b'a ɲaa da.",
        "signification": "Petit à petit, l'oiseau fait son nid. La patience et la persévérance mènent au succès.",
        "morale": "La patience est la mère de la réussite.",
        "origine": "Tradition Mandingue",
        "region_id": "koulikoro",
        "region_nom": "Koulikoro",
        "source_temoin": "Mon grand-père à Kangaba",
        "auteur_nom": "Amadou Diarra",
        "auteur_role": "Apprenant",
    }
    # 1. Soumission
    resp = client.post("/api/v1/culture/contributions", json=payload)
    assert resp.status_code in (200, 201)
    created = resp.json()
    assert created["statut"] == "EN_ATTENTE"
    assert created["typeContenu"] == "proverbe"
    contrib_id = created["id"]

    # 2. Modération : Approbation
    mod_resp = client.post(
        f"/api/v1/culture/contributions/{contrib_id}/decision",
        json={"decision": "APPROUVE", "motif": "Proverbe authentique certifié", "admin_id": "admin_sage_1"},
    )
    assert mod_resp.status_code == 200
    approved = mod_resp.json()
    assert approved["statut"] == "APPROUVE"
    assert approved["motifModeration"] == "Proverbe authentique certifié"


def test_contributions_all_pillars():
    pillars = [
        {
            "type_contenu": "devinette",
            "texte": "Je voyage partout dans le village sans laisser de trace de pas. Qui suis-je ?",
            "signification": "Énigme sur l'élément naturel omniprésent",
            "morale": "Le vent",
            "origine": "Tradition Peule",
            "region_id": "mopti",
            "region_nom": "Mopti",
        },
        {
            "type_contenu": "conte",
            "titre": "Le Lièvre et le Lion",
            "texte": "Il était une fois dans la savane du Manden un lièvre si rusé qu'il défia le roi lion...",
            "signification": "Conte initiatique sur l'intelligence qui triomphe de la force brute",
            "morale": "La ruse vaut mieux que la force",
            "origine": "Tradition Orale Mandingue",
            "region_id": "segou",
            "region_nom": "Ségou",
        },
        {
            "type_contenu": "monument",
            "titre": "Sanctuaire de Kamablon",
            "texte": "Case sacrée circulaire à Kangaba réfectionnée tous les 7 ans lors d'un rituel solennel.",
            "signification": "Cœur mystique et spirituel du Manden historique",
            "origine": "Histoire du Mali",
            "region_id": "koulikoro",
            "region_nom": "Koulikoro",
            "donnees_supplementaires": {"ville": "Kangaba", "epoque": "XIIIe siècle"},
        },
        {
            "type_contenu": "personnage",
            "titre": "Fakoly Doumbia",
            "texte": "Général d'armée redoutable, grand maître des forgerons et allié clé de Soundiata Keïta.",
            "signification": "Symbole de la bravoure et de la maîtrise du fer au Manden",
            "morale": "Chef suprême des forgerons",
            "origine": "Épopée Mandingue",
            "region_id": "koulikoro",
            "region_nom": "Koulikoro",
            "donnees_supplementaires": {"periode": "XIIIe siècle"},
        },
        {
            "type_contenu": "lieu",
            "titre": "Bafoulabé la Légendaire",
            "texte": "Cité confluent du Bafing et du Bakoye devenant le fleuve Sénégal, terre de la légende de Mali Sadio.",
            "signification": "Carrefour fluvial et légende sacrée de l'amitié entre une jeune fille et un hippopotame",
            "origine": "Royaume du Khasso",
            "region_id": "kayes",
            "region_nom": "Kayes",
            "donnees_supplementaires": {"fondation": "Carrefour séculaire"},
        },
        {
            "type_contenu": "patronyme",
            "titre": "Coulibaly",
            "texte": "Fondateurs du Royaume bambara de Ségou avec Biton Coulibaly.",
            "signification": "Nom clanique noble de Ségou signifiant 'sans pirogue' selon la légende de la traversée.",
            "texte_original": "Ségou Diarra, Ségou Coulibaly",
            "origine": "Bambara de Ségou",
            "region_id": "segou",
            "region_nom": "Ségou",
            "donnees_supplementaires": {"totem": "Silure", "senankouya": "Diarra / Traoré"},
        },
    ]

    for p in pillars:
        resp = client.post("/api/v1/culture/contributions", json=p)
        assert resp.status_code in (200, 201), f"Erreur soumission pilier {p['type_contenu']}: {resp.text}"
        data = resp.json()
        assert data["typeContenu"] == p["type_contenu"]
        assert data["statut"] == "EN_ATTENTE"
        c_id = data["id"]

        # Modération et promotion automatique
        mod = client.post(
            f"/api/v1/culture/contributions/{c_id}/decision",
            json={"decision": "APPROUVE", "motif": "Validé par le jury d'experts"},
        )
        assert mod.status_code == 200, f"Erreur modération pilier {p['type_contenu']}: {mod.text}"
        assert mod.json()["statut"] == "APPROUVE"


def teardown_module():
    """Supprime les contributions temporaires créées par la suite de tests ainsi que les promotions test."""
    from backend.src.db.database import SessionLocal
    from backend.src.db.models import (
        CultureContribution, CultureMonument, CulturePersonnage,
        CultureLieu, CultureConte, CultureProverbe
    )

    db = SessionLocal()
    try:
        db.query(CultureContribution).filter(
            (CultureContribution.auteur_id == None)
            | (CultureContribution.auteur_nom.in_(["Amadou Diarra", "Contributeur AlternIA"]))
        ).delete(synchronize_session=False)

        # Nettoyage rigoureux des entités promues lors des tests
        for model in (CultureMonument, CulturePersonnage, CultureLieu, CultureConte, CultureProverbe):
            db.query(model).filter(model.id.like("contrib_%")).delete(synchronize_session=False)

        db.commit()
    finally:
        db.close()


