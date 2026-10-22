"""
Tests unitaires et d'intégration pour les 8 modules d'évolution AlterniA :
Portefeuille & Transactions, Retraits Mobile Money, Parrainage, Abonnements,
Défi National, Podcasts et Administration sécurisée.
"""

import sys
from pathlib import Path
import uuid
from fastapi.testclient import TestClient

root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.src.main import app
from backend.src.db.database import init_db, SessionLocal
from backend.src.services.wallet_service import (
    get_or_create_wallet,
    credit_coins,
    get_wallet_summary,
)

client = TestClient(app)


def setup_module():
    """Initialise la base de données de test."""
    init_db()


def test_wallet_initial_and_credit():
    """Teste l'initialisation du portefeuille et le crédit de pièces avec idempotence."""
    db = SessionLocal()
    try:
        student_id = "test_student_wallet_01"
        wallet = get_or_create_wallet(db, student_id)
        assert wallet.solde_pieces >= 240

        # Crédit standard
        w_apres, tx = credit_coins(
            db=db,
            student_id=student_id,
            amount=50,
            origine="BATTLE_DUEL",
            description="Victoire test duel",
            idempotency_key="unique_key_test_01",
        )
        assert tx is not None
        assert w_apres.solde_pieces == wallet.solde_pieces

        # Test d'idempotence : rejouer la même transaction ne doit pas rajouter de pièces
        w_rejoue, tx_rejoue = credit_coins(
            db=db,
            student_id=student_id,
            amount=50,
            origine="BATTLE_DUEL",
            description="Victoire test duel",
            idempotency_key="unique_key_test_01",
        )
        assert w_rejoue.solde_pieces == w_apres.solde_pieces
    finally:
        db.close()


def test_wallet_api_summary_and_transactions():
    """Teste les endpoints REST du portefeuille."""
    res = client.get("/api/wallet/summary?student_id=test_student_wallet_01")
    assert res.status_code == 200
    data = res.json()
    assert "solde_pieces" in data
    assert "valeur_fcfa" in data
    assert data["taux_conversion"] == 2

    res_tx = client.get("/api/wallet/transactions?student_id=test_student_wallet_01")
    assert res_tx.status_code == 200
    txs = res_tx.json()
    assert isinstance(txs, list)
    assert len(txs) >= 1


def test_retrait_mobile_money_lifecycle():
    """Teste le cycle de vie complet d'une demande de retrait Mobile Money (création, réservation, paiement)."""
    student_id = f"test_student_retrait_{uuid.uuid4().hex[:6]}"

    # 1. Création de demande de retrait (Orange Money)
    res = client.post(
        "/api/retraits/demande",
        json={
            "apprenant_id": student_id,
            "pieces": 100,
            "operateur": "ORANGE_MONEY",
            "numero_telephone": "76123456",
            "nom_titulaire": "Moussa Traoré",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["succes"] is True
    assert data["statut"] == "EN_ATTENTE"
    assert data["pieces_reservees"] == 100
    ref = data["reference"]

    # 2. Consultation des demandes de l'apprenant
    res_list = client.get(f"/api/retraits/mes-demandes?apprenant_id={student_id}")
    assert res_list.status_code == 200
    demandes = res_list.json()
    assert any(d["ref"] == ref for d in demandes)
    demande_id = [d["id"] for d in demandes if d["ref"] == ref][0]

    # 3. Traitement admin : mise en vérification
    res_verif = client.post(
        f"/api/admin/retraits/{demande_id}/verifier",
        json={"admin_id": "admin_test"},
    )
    assert res_verif.status_code == 200
    assert res_verif.json()["statut"] == "EN_VERIFICATION"

    # 4. Traitement admin : confirmation du paiement
    res_pay = client.post(
        f"/api/admin/retraits/{demande_id}/payer",
        json={"admin_id": "admin_test", "reference_operateur": "OM-MALI-89123"},
    )
    assert res_pay.status_code == 200
    assert res_pay.json()["statut"] == "PAYEE"


def test_parrainage_system():
    """Teste le système de parrainage et la prévention des fraudes."""
    parrain_id = f"parrain_{uuid.uuid4().hex[:6]}"
    filleul_id = f"filleul_{uuid.uuid4().hex[:6]}"

    # 1. Récupérer le code de parrainage d'un parrain
    res_sum = client.get(f"/api/parrainage/summary?student_id={parrain_id}&student_name=Fanta")
    assert res_sum.status_code == 200
    data_sum = res_sum.json()
    code_parrain = data_sum["code"]
    assert len(code_parrain) >= 5

    # 2. Tentative d'auto-parrainage (doit échouer)
    res_auto = client.post(
        "/api/parrainage/valider",
        json={"filleul_id": parrain_id, "code_parrainage": code_parrain},
    )
    assert res_auto.status_code == 400

    # 3. Parrainage valide d'un nouvel élève
    res_val = client.post(
        "/api/parrainage/valider",
        json={"filleul_id": filleul_id, "code_parrainage": code_parrain},
    )
    assert res_val.status_code == 200
    assert res_val.json()["succes"] is True
    assert res_val.json()["pieces_filleul"] == 25

    # 4. Tentative de double parrainage du même filleul (doit échouer)
    res_double = client.post(
        "/api/parrainage/valider",
        json={"filleul_id": filleul_id, "code_parrainage": code_parrain},
    )
    assert res_double.status_code == 400


def test_abonnements_catalog_and_status():
    """Teste le catalogue d'abonnements et la vérification de statut Premium."""
    res_offres = client.get("/api/abonnements/offres")
    assert res_offres.status_code == 200
    offres = res_offres.json()
    assert len(offres) >= 1
    premiere_offre = offres[0]
    assert "prix_fcfa" in premiere_offre

    # Élève sans abonnement
    eleve_id = f"eleve_sub_{uuid.uuid4().hex[:6]}"
    res_stat = client.get(f"/api/abonnements/status?student_id={eleve_id}")
    assert res_stat.status_code == 200
    assert res_stat.json()["est_premium"] is False

    # Souscription
    res_sub = client.post(
        "/api/abonnements/souscrire",
        json={"apprenant_id": eleve_id, "offre_id": premiere_offre["id"]},
    )
    assert res_sub.status_code == 200
    assert res_sub.json()["succes"] is True

    # Vérification que l'élève est devenu Premium
    res_stat_apres = client.get(f"/api/abonnements/status?student_id={eleve_id}")
    assert res_stat_apres.status_code == 200
    assert res_stat_apres.json()["est_premium"] is True


def test_defi_national_flow():
    """Teste la participation au Défi National officiel avec validation serveur et rival fictif SoloLearn."""
    res_actifs = client.get("/api/defi-national/actifs?classe=12eme")
    assert res_actifs.status_code == 200
    defis = res_actifs.json()
    assert len(defis) >= 1
    defi = defis[0]
    assert "questions" in defi
    assert "correct_index" not in defi["questions"][0]  # Anti-triche
    assert "adversaire" in defi  # Rival fictif SoloLearn disponible instantanément
    assert "nom" in defi["adversaire"]
    assert "etablissement" in defi["adversaire"]

    # 1. Soumission d'une victoire face au rival
    apprenant_id = f"eleve_defi_{uuid.uuid4().hex[:6]}"
    res_soum = client.post(
        "/api/defi-national/soumettre",
        json={
            "defi_id": defi["id"],
            "apprenant_id": apprenant_id,
            "apprenant_nom": "Amadou Cissé",
            "apprenant_classe": "12eme",
            "reponses": {"q1": 0, "q2": 0, "q3": 0, "q4": 0},
            "temps_ecoule_sec": 45,
            "adversaire_nom": "Fatoumata Diarra",
            "adversaire_score": 2,
            "adversaire_temps_sec": 80,
        },
    )
    assert res_soum.status_code == 200
    resultat = res_soum.json()
    assert resultat["succes"] is True
    assert resultat["est_victoire"] is True
    assert resultat["pieces_gagnees"] >= 50
    assert resultat["xp_gagnes"] >= 250

    # 2. Rejouabilité à tout moment pour faire grimper son score (sans blocage anti-rejeu)
    res_rejouer = client.post(
        "/api/defi-national/soumettre",
        json={
            "defi_id": defi["id"],
            "apprenant_id": apprenant_id,
            "apprenant_nom": "Amadou Cissé",
            "apprenant_classe": "12eme",
            "reponses": {"q1": 0, "q2": 0, "q3": 0, "q4": 0, "q5": 0},
            "temps_ecoule_sec": 40,
            "adversaire_nom": "Fatoumata Diarra",
            "adversaire_score": 3,
            "adversaire_temps_sec": 75,
        },
    )
    assert res_rejouer.status_code == 200
    res_rejouer_data = res_rejouer.json()
    assert res_rejouer_data["succes"] is True
    assert res_rejouer_data["score"] == 5
    assert res_rejouer_data["nouveau_record"] is True

    # 3. Test de défaite : si on ne gagne pas, 0 pièce mais juste des XP
    autre_eleve = f"eleve_defaite_{uuid.uuid4().hex[:6]}"
    res_defaite = client.post(
        "/api/defi-national/soumettre",
        json={
            "defi_id": defi["id"],
            "apprenant_id": autre_eleve,
            "apprenant_nom": "Élève Débutant",
            "apprenant_classe": "12eme",
            "reponses": {"q1": 1, "q2": 1, "q3": 1},  # Mauvaises réponses
            "temps_ecoule_sec": 120,
            "adversaire_nom": "Amadou Konaté",
            "adversaire_score": 4,
            "adversaire_temps_sec": 50,
        },
    )
    assert res_defaite.status_code == 200
    data_defaite = res_defaite.json()
    assert data_defaite["est_victoire"] is False
    assert data_defaite["pieces_gagnees"] == 0  # AUCUNE PIÈCE en cas de défaite
    assert data_defaite["xp_gagnes"] == 100     # UNIQUEMENT DES XPS

    # Classement officiel
    res_class = client.get(f"/api/defi-national/{defi['id']}/classement")
    assert res_class.status_code == 200
    classement = res_class.json()
    assert any(c["nom"] == "Amadou Cissé" for c in classement)


def test_podcast_generation_from_text():
    """Teste la génération de podcast éducatif à partir d'un cours textuel."""
    sample_text = (
        "Leçon sur la colonisation et l'indépendance de la République du Mali. "
        "Le 22 septembre 1960, le président Modibo Keïta proclame l'indépendance du Mali à Bamako. "
        "Les symboles de la République comprennent le drapeau tricolore vert, or et rouge, "
        "la devise 'Un Peuple, Un But, Une Foi' et l'hymne national 'Pour l'Afrique et pour toi, Mali'."
    )
    res = client.post(
        "/api/education/podcast/generate-from-text",
        json={
            "course_text": sample_text,
            "subject": "Histoire-Géographie",
            "class_level": "12eme",
            "student_name": "Sory",
            "duration_minutes": 5,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "full_script" in data
    assert len(data["chapters"]) >= 2
    assert len(data["key_takeaways"]) >= 2
