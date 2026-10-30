"""
Test d'intégration End-to-End complet pour la validation des flux clés AlterniA :
1. Enregistrement d'un nouvel apprenant (stats initiales : Streak 1j, 0 XP, 0 Pièces).
2. Dépôt d'une contribution culturelle citoyenne (statut EN_ATTENTE).
3. Modération Super Admin (APPROUVE) -> Promotion en collection officielle, crédit +25 pièces au portefeuille, attribution +50 XP.
4. Consultation interactive avec le Guide Culturel / Grand-mère Mah.
"""

import sys
import uuid
from pathlib import Path
from fastapi.testclient import TestClient

root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.src.main import app
from backend.src.db.database import SessionLocal, init_db
from backend.src.db.models import CultureProverbe
from backend.src.services.wallet_service import get_wallet_summary

def test_full_integration_flow():
    init_db()
    client = TestClient(app)

    # 1. Enregistrement d'un nouvel élève avec nom unique
    unique_suffix = uuid.uuid4().hex[:6]
    student_name = f"Nio_User_{unique_suffix}"
    res_reg = client.post("/api/apprenants", json={
        "nom": student_name,
        "prenom": "Élève",
        "classe": "6eme",
        "etablissement_id": "etab-lbad-bamako"
    })
    assert res_reg.status_code == 200, f"Erreur inscription: {res_reg.text}"
    apprenant_id = res_reg.json()["id"]

    # Vérification des stats initiales : Streak 1j, 0 XP, 0 Pièces
    res_stats = client.get(f"/api/apprenants/gamification/stats?student_id={apprenant_id}&eleve_nom={student_name}")
    assert res_stats.status_code == 200
    stats_data = res_stats.json()
    assert stats_data["xp"] == 0, f"XP initial devrait être 0, obtenu: {stats_data['xp']}"
    assert stats_data["coins"] == 0, f"Pièces initiales devraient être 0, obtenu: {stats_data['coins']}"
    assert stats_data["streak"] == 1, f"Streak initial devrait être 1, obtenu: {stats_data['streak']}"

    # 2. Dépôt de contribution culturelle par l'élève
    proverbe_unique = f"Dolo ma nyi {unique_suffix}"
    res_contrib = client.post("/api/v1/culture/contributions", json={
        "type_contenu": "proverbe",
        "texte": proverbe_unique,
        "texte_original": proverbe_unique,
        "signification": "Le travail persévérant apporte respect et dignité.",
        "morale": "L'effort porte toujours ses fruits.",
        "origine": "Tradition Mandingue",
        "region_id": "sikasso",
        "region_nom": "Sikasso",
        "auteur_id": apprenant_id,
        "auteur_nom": student_name,
        "auteur_role": "Apprenant",
        "xp_attribues": 50,
        "pieces_attribuees": 25,
    })
    assert res_contrib.status_code == 201, f"Erreur contribution: {res_contrib.text}"
    contrib_data = res_contrib.json()
    contrib_id = contrib_data["id"]
    assert contrib_data["statut"] == "EN_ATTENTE"

    # 3. Modération Super Admin : Approbation
    res_mod = client.post(f"/api/v1/culture/contributions/{contrib_id}/moderate", json={
        "decision": "APPROUVE",
        "motif": "Proverbe authentique conforme au patrimoine national."
    })
    assert res_mod.status_code == 200
    assert res_mod.json()["statut"] == "APPROUVE"

    # Vérification en base de données du Portefeuille
    db = SessionLocal()
    try:
        w_summary = get_wallet_summary(db, apprenant_id)
        assert w_summary["solde_pieces"] == 25, f"Solde portefeuille devrait être 25, obtenu: {w_summary['solde_pieces']}"
        assert w_summary["solde_culture"] == 25, f"Solde culture devrait être 25, obtenu: {w_summary['solde_culture']}"
        assert w_summary["solde_education"] == 0, f"Solde éducation devrait rester 0, obtenu: {w_summary['solde_education']}"

        # Vérification de la promotion dans la table officielle CultureProverbe
        prov = db.query(CultureProverbe).filter(CultureProverbe.texte.ilike(f"%{proverbe_unique}%")).first()
        assert prov is not None, "Le proverbe devrait être promu dans CultureProverbe"
    finally:
        db.close()

    # Vérification de la séparation stricte après modération :
    # - Éducation reste à 0 XP et 0 Pièces
    # - Culture passe à 50 XP et 25 Pièces
    res_stats_after = client.get(f"/api/apprenants/gamification/stats?student_id={apprenant_id}&eleve_nom={student_name}")
    assert res_stats_after.status_code == 200
    stats_after = res_stats_after.json()
    assert stats_after["coins"] == 0, f"Coins Éducation devrait rester 0, obtenu: {stats_after['coins']}"
    assert stats_after["xp"] == 0, f"XP Éducation devrait rester 0, obtenu: {stats_after['xp']}"
    assert stats_after["education"]["coins"] == 0
    assert stats_after["education"]["xp"] == 0
    assert stats_after["culture"]["coins"] == 25, f"Coins Culture après approbation devrait être 25, obtenu: {stats_after['culture']['coins']}"
    assert stats_after["culture"]["xp"] == 50, f"XP Culture après approbation devrait être 50, obtenu: {stats_after['culture']['xp']}"

    # 4. Dialogue avec Grand-mère Mah / Guide Culturel IA
    res_ask = client.post("/api/v1/culture/ask", json={
        "question": "Qui était Soundiata Keïta et quelle est la charte de Kouroukan Fouga ?"
    })
    assert res_ask.status_code == 200
    assert "reponse" in res_ask.json()
    assert len(res_ask.json()["reponse"]) > 30

if __name__ == "__main__":
    test_full_integration_flow()
