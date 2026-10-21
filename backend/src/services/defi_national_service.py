"""
Service du Défi National Scolaire du Mali (Module B).
Fournit les épreuves hebdomadaires par niveau scolaire,
contrôle le temps et calcule les résultats strictement côté serveur,
attribue les pièces automatiquement dans le portefeuille unique,
et établit le classement national en temps réel.
"""

from datetime import UTC, datetime, timedelta
import json
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.src.db.models import (
    DefiNational,
    ParticipationDefiNational,
    generate_uuid,
)
from backend.src.services.wallet_service import credit_coins

logger = logging.getLogger("AlternIA.DefiNationalService")

# Épreuves officielles préconfigurées pour le programme malien
DEFIS_NATIONAUX_DEFAUT = [
    {
        "titre": "Grand Défi National Baccalauréat — Session Spéciale",
        "description": "L'épreuve nationale de référence pour tous les lycéens du Mali en Terminale.",
        "classe": "12eme",
        "matiere": "Mathématiques & Sciences",
        "duree_minutes": 15,
        "questions": [
            {
                "id": "q1",
                "question": "Soit la fonction f(x) = ln(x) sur ]0, +∞[. Quelle est l'équation de la tangente au point d'abscisse x = 1 ?",
                "options": ["y = x - 1", "y = x", "y = 1/x", "y = x + 1"],
                "correct_index": 0,
                "explanation": "f'(1) = 1 et f(1) = 0. Donc y = f'(1)(x - 1) + f(1) = x - 1.",
            },
            {
                "id": "q2",
                "question": "En physique, quelle est l'expression de l'énergie cinétique d'un solide de masse m et de vitesse v ?",
                "options": ["Ec = 1/2 · m · v²", "Ec = m · g · h", "Ec = m · v", "Ec = 1/2 · m² · v"],
                "correct_index": 0,
                "explanation": "L'énergie cinétique de translation est Ec = 1/2 m v².",
            },
            {
                "id": "q3",
                "question": "Quelle est la capitale historique de l'Empire du Mali fondée au XIIIe siècle sous Soundiata Keïta ?",
                "options": ["Niani", "Gao", "Koumbi Saleh", "Djenné"],
                "correct_index": 0,
                "explanation": "Niani fut la prestigieuse capitale impériale de Soundiata Keïta.",
            },
            {
                "id": "q4",
                "question": "Quelle est la solution de l'équation différentielle y' - 3y = 0 avec y(0) = 2 ?",
                "options": ["y(x) = 2 · e^(3x)", "y(x) = 3 · e^(2x)", "y(x) = e^(3x) + 1", "y(x) = 2 · ln(3x)"],
                "correct_index": 0,
                "explanation": "Les solutions sont de la forme y(x) = C · e^(3x). Avec y(0)=2, C=2.",
            },
            {
                "id": "q5",
                "question": "Dans le programme de chimie, quelle est la formule générale d'un acide carboxylique ?",
                "options": ["R-COOH", "R-CHO", "R-CO-R'", "R-OH"],
                "correct_index": 0,
                "explanation": "Le groupement carboxyle s'écrit -COOH.",
            },
        ],
    },
    {
        "titre": "Défi National Première — Fondamentaux du Lycée",
        "description": "Épreuve de consolidation pour les élèves de 11ème du Mali.",
        "classe": "11eme",
        "matiere": "Sciences Générales",
        "duree_minutes": 15,
        "questions": [
            {
                "id": "q11_1",
                "question": "Quel est le discriminant Δ du polynôme P(x) = 2x² - 4x + 2 ?",
                "options": ["0", "4", "16", "-8"],
                "correct_index": 0,
                "explanation": "Δ = b² - 4ac = (-4)² - 4(2)(2) = 16 - 16 = 0.",
            },
            {
                "id": "q11_2",
                "question": "Quel est le plus long fleuve qui traverse la République du Mali sur plus de 1 700 km ?",
                "options": ["Le Fleuve Niger", "Le Fleuve Sénégal", "Le Bani", "La Volta"],
                "correct_index": 0,
                "explanation": "Le fleuve Niger (Djoliba) est l'artère nourricière du Mali.",
            },
            {
                "id": "q11_3",
                "question": "Quel organite cellulaire est le siège principal de la respiration cellulaire et de la production d'ATP ?",
                "options": ["La mitochondrie", "Le chloroplaste", "Le ribosome", "L'appareil de Golgi"],
                "correct_index": 0,
                "explanation": "Les mitochondries sont les centrales énergétiques de la cellule.",
            },
        ],
    },
]


def init_defis_nationaux_si_besoin(db: Session):
    """Initialise un défi national actif si la table est vide."""
    now = datetime.now(UTC)
    existant = db.query(DefiNational).filter(DefiNational.statut == "EN_COURS").first()
    if not existant:
        for d in DEFIS_NATIONAUX_DEFAUT:
            defi = DefiNational(
                id=generate_uuid(),
                titre=d["titre"],
                description=d["description"],
                classe=d["classe"],
                matiere=d["matiere"],
                statut="EN_COURS",
                date_debut=now - timedelta(hours=2),
                date_fin=now + timedelta(days=7),  # Valable 1 semaine
                duree_minutes=d["duree_minutes"],
                recompense_pieces_premier=500,
                recompense_pieces_top10=250,
                recompense_pieces_participation=50,
                questions_json=json.dumps(d["questions"]),
                date_creation=now,
            )
            db.add(defi)
        db.commit()


def get_defis_actifs(db: Session, classe: Optional[str] = None, periode: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retourne les défis nationaux ouverts avec questions épurées des réponses correctes."""
    init_defis_nationaux_si_besoin(db)
    now = datetime.now(UTC)
    query = db.query(DefiNational).filter(
        DefiNational.statut == "EN_COURS",
        DefiNational.date_fin > now,
    )
    if classe:
        norm_class = "12eme" if any(c in classe.lower() for c in ["12", "tse", "tsexp", "tll", "tss"]) else "11eme"
        query = query.filter(DefiNational.classe == norm_class)

    defis = query.all()
    result = []
    for d in defis:
        questions_raw = json.loads(d.questions_json) if d.questions_json else []

        # Si trimestre 1 demandé, exclure les questions de fin d'année
        if periode == "trimestre_1":
            end_terms = ["différentielle", "primitives", "intégral", "acide carboxylique", "complexe", "chatelier"]
            filtered = [
                q for q in questions_raw
                if not any(term in q.get("question", "").lower() for term in end_terms)
            ]
            if filtered:
                questions_raw = filtered

        # Supprimer correct_index pour éviter la triche côté client !
        questions_client = [
            {
                "id": q.get("id"),
                "question": q.get("question"),
                "options": q.get("options", []),
            }
            for q in questions_raw
        ]

        result.append({
            "id": d.id,
            "titre": d.titre,
            "description": d.description,
            "classe": d.classe,
            "matiere": d.matiere,
            "duree_minutes": d.duree_minutes,
            "date_fin": d.date_fin.isoformat() if d.date_fin else None,
            "questions_count": len(questions_client),
            "recompense_premier": d.recompense_pieces_premier,
            "recompense_top10": d.recompense_pieces_top10,
            "recompense_participation": d.recompense_pieces_participation,
            "questions": questions_client,
        })
    return result


def soumettre_reponses_defi(
    db: Session,
    defi_id: str,
    apprenant_id: str,
    apprenant_nom: str,
    apprenant_classe: str,
    reponses: Dict[str, int],  # { "q1": 0, "q2": 1 }
    temps_ecoule_sec: int,
) -> Dict[str, Any]:
    """
    Validation serveur des réponses d'un Défi National :
    Calcule le score réel, empêche les soumissions multiples pour un même défi,
    crédite les pièces dans le portefeuille et retourne les corrections détaillées.
    """
    defi = db.query(DefiNational).filter(DefiNational.id == defi_id).first()
    if not defi:
        raise ValueError("Défi national introuvable.")

    # Vérifier l'anti-rejeu : un élève ne peut soumettre qu'une seule fois par défi
    deja_participe = (
        db.query(ParticipationDefiNational)
        .filter(
            ParticipationDefiNational.defi_id == defi_id,
            ParticipationDefiNational.apprenant_id == apprenant_id,
        )
        .first()
    )
    if deja_participe:
        raise ValueError("Vous avez déjà soumis vos réponses pour cette session de Défi National.")

    questions_officielles = json.loads(defi.questions_json) if defi.questions_json else []
    score = 0
    total_questions = len(questions_officielles)
    corrections = []

    for q in questions_officielles:
        qid = q.get("id")
        choix_eleve = reponses.get(qid)
        bonne_reponse = q.get("correct_index")
        est_correct = (choix_eleve == bonne_reponse)

        if est_correct:
            score += 1

        corrections.append({
            "id": qid,
            "question": q.get("question"),
            "choix_eleve": choix_eleve,
            "bonne_reponse": bonne_reponse,
            "est_correct": est_correct,
            "explication": q.get("explanation"),
        })

    pourcentage = int((score / total_questions * 100)) if total_questions > 0 else 0

    # Barème de pièces calculé strictement par le serveur
    if pourcentage >= 80:
        pieces_gagnees = defi.recompense_pieces_top10
        xp_gagnes = 400
    elif pourcentage >= 50:
        pieces_gagnees = defi.recompense_pieces_participation * 2
        xp_gagnes = 250
    else:
        pieces_gagnees = defi.recompense_pieces_participation
        xp_gagnes = 100

    # 1. Enregistrer la participation
    participation = ParticipationDefiNational(
        id=generate_uuid(),
        defi_id=defi_id,
        apprenant_id=apprenant_id,
        apprenant_nom=apprenant_nom,
        apprenant_classe=apprenant_classe,
        score=score,
        temps_secondes=temps_ecoule_sec,
        pieces_remportees=pieces_gagnees,
        xp_remportes=xp_gagnes,
        reponses_soumises_json=json.dumps(reponses),
        soumis_a=datetime.now(UTC),
    )
    db.add(participation)

    # 2. Créditer le portefeuille de façon atomique
    credit_coins(
        db=db,
        student_id=apprenant_id,
        amount=pieces_gagnees,
        origine="DEFI_NATIONAL",
        description=f"Récompense Défi National : score {score}/{total_questions} ({pourcentage}%)",
        idempotency_key=f"defi_nat_{participation.id}",
    )

    db.commit()
    db.refresh(participation)

    return {
        "succes": True,
        "score": score,
        "total_questions": total_questions,
        "pourcentage": pourcentage,
        "pieces_gagnees": pieces_gagnees,
        "xp_gagnes": xp_gagnes,
        "temps_secondes": temps_ecoule_sec,
        "corrections": corrections,
    }


def get_classement_defi(db: Session, defi_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Retourne le classement officiel d'une session de Défi National."""
    participations = (
        db.query(ParticipationDefiNational)
        .filter(ParticipationDefiNational.defi_id == defi_id)
        .order_by(
            ParticipationDefiNational.score.desc(),  # type: ignore
            ParticipationDefiNational.temps_secondes,
        )
        .limit(limit)
        .all()
    )

    return [
        {
            "rang": idx + 1,
            "nom": p.apprenant_nom,
            "classe": p.apprenant_classe,
            "score": p.score,
            "temps_secondes": p.temps_secondes,
            "pieces_remportees": p.pieces_remportees,
            "xp_remportes": p.xp_remportes,
            "date": p.soumis_a.isoformat() if p.soumis_a else None,
        }
        for idx, p in enumerate(participations)
    ]
