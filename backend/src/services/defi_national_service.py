"""
Service du Défi National Scolaire du Mali (Module B).
Fournit les épreuves hebdomadaires par niveau scolaire,
contrôle le temps et calcule les résultats strictement côté serveur,
attribue les pièces automatiquement dans le portefeuille unique,
et établit le classement national en temps réel.
"""

from datetime import datetime, timedelta
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
    {
        "titre": "Défi National Seconde — Tronc Commun du Lycée",
        "description": "Grand tournoi national de révision pour les élèves de 10ème du Mali.",
        "classe": "10eme",
        "matiere": "Mathématiques & SVT",
        "duree_minutes": 15,
        "questions": [
            {
                "id": "q10_1",
                "question": "Combien font (2x + 3)(2x - 3) selon les identités remarquables ?",
                "options": ["4x² - 9", "4x² + 9", "4x² - 12x + 9", "2x² - 6"],
                "correct_index": 0,
                "explanation": "(a + b)(a - b) = a² - b² = (2x)² - 3² = 4x² - 9.",
            },
            {
                "id": "q10_2",
                "question": "Quelle est la formule chimique du chlorure de sodium (sel de table) ?",
                "options": ["NaCl", "KCl", "NaOH", "HCl"],
                "correct_index": 0,
                "explanation": "Le chlorure de sodium est composé d'ions Na+ et Cl- soit NaCl.",
            },
            {
                "id": "q10_3",
                "question": "Quelle est la date de la proclamation de l'indépendance de la République du Mali par le Président Modibo Keïta ?",
                "options": ["22 septembre 1960", "20 janvier 1961", "15 août 1960", "25 mai 1963"],
                "correct_index": 0,
                "explanation": "Le Mali a accédé à sa souveraineté nationale le 22 septembre 1960.",
            },
        ],
    },
]

# Rivaux lycéens du Mali simulés (style SoloLearn pour matchmaking instantané sans attente)
RIVAUX_MALI_FICTIFS = [
    {
        "nom": "Fatoumata Diarra",
        "etablissement": "Lycée Ba Aminata Diallo (LBAD)",
        "ville": "Bamako",
        "classe": "12eme",
        "serie": "TSExp",
        "avatar": "female_1",
    },
    {
        "nom": "Amadou Konaté",
        "etablissement": "Lycée Askia Mohamed",
        "ville": "Bamako",
        "classe": "12eme",
        "serie": "TSE",
        "avatar": "male_1",
    },
    {
        "nom": "Ousmane Coulibaly",
        "etablissement": "Lycée Hamadoun Dicko",
        "ville": "Sévaré (Mopti)",
        "classe": "12eme",
        "serie": "TSE",
        "avatar": "male_2",
    },
    {
        "nom": "Aïssata Traoré",
        "etablissement": "Lycée Public de Sikasso",
        "ville": "Sikasso",
        "classe": "11eme",
        "serie": "11eme Sciences",
        "avatar": "female_2",
    },
    {
        "nom": "Boubacar Sanogo",
        "etablissement": "Lycée Progrès de Ségou",
        "ville": "Ségou",
        "classe": "11eme",
        "serie": "11eme Sciences",
        "avatar": "male_3",
    },
    {
        "nom": "Mariam Touré",
        "etablissement": "Lycée Mahamane Alassane Haïdara",
        "ville": "Tombouctou",
        "classe": "10eme",
        "serie": "10eme Commune",
        "avatar": "female_3",
    },
    {
        "nom": "Ibrahim Cissé",
        "etablissement": "Lycée Dougoukolo Konaré",
        "ville": "Kayes",
        "classe": "12eme",
        "serie": "TSE",
        "avatar": "male_4",
    },
    {
        "nom": "Kadiatou Fofana",
        "etablissement": "Lycée Notre-Dame du Niger",
        "ville": "Bamako",
        "classe": "12eme",
        "serie": "TSExp",
        "avatar": "female_4",
    },
    {
        "nom": "Salif Keïta",
        "etablissement": "Lycée Technique de Bamako",
        "ville": "Bamako",
        "classe": "11eme",
        "serie": "11eme Technique",
        "avatar": "male_5",
    },
]


def get_adversaire_fictif_pour_defi(
    defi_id: str,
    classe: Optional[str] = None,
    total_questions: int = 5,
    seed_str: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Génère un rival lycéen malien certifié (style SoloLearn).
    Permet à l'élève d'affronter instantanément un camarade sans attendre d'autres personnes en ligne.
    """
    import random
    
    # Filtrer par classe si possible
    candidates = RIVAUX_MALI_FICTIFS
    if classe:
        norm_class = "12eme" if any(c in classe.lower() for c in ["12", "tse", "tsexp", "tll", "tss"]) else ("11eme" if "11" in classe else "10eme")
        filtered = [r for r in RIVAUX_MALI_FICTIFS if r.get("classe") == norm_class]
        if filtered:
            candidates = filtered

    # Sélection déterministe ou semi-aléatoire selon la seed
    if seed_str:
        idx = abs(hash(seed_str + defi_id)) % len(candidates)
        rival = candidates[idx]
    else:
        idx = abs(hash(defi_id)) % len(candidates)
        rival = candidates[idx]

    # Score simulé réaliste entre 50% et 75% des questions
    base_correct = max(1, min(total_questions, int(total_questions * 0.6)))
    # Temps simulé réaliste (environ 18-25 secondes par question)
    temps_simule = max(30, total_questions * 20)

    return {
        "nom": rival["nom"],
        "etablissement": rival["etablissement"],
        "ville": rival["ville"],
        "classe": rival.get("classe", "12eme"),
        "serie": rival.get("serie", "Sciences"),
        "avatar": rival.get("avatar", "student_mali"),
        "score_simule": base_correct,
        "temps_simule_sec": temps_simule,
        "est_fictif": True,
        "badge": "Lycéen Certifié du Mali",
    }


def init_defis_nationaux_si_besoin(db: Session):
    """
    Initialise ou réactive les défis nationaux afin qu'à TOUT MOMENT,
    un élève puisse trouver une session ouverte 24h/24 sans attendre d'autres élèves en ligne.
    """
    now = datetime.utcnow()
    # 1. Vérifier si des défis sont expirés et les prolonger pour maintenir la disponibilité 24/7
    defis_expires = db.query(DefiNational).filter(DefiNational.date_fin <= now).all()
    for d in defis_expires:
        d.statut = "EN_COURS"
        d.date_fin = now + timedelta(days=7)
    if defis_expires:
        db.commit()

    # 2. Vérifier les épreuves de base
    classes_existantes = {d.classe for d in db.query(DefiNational).filter(DefiNational.statut == "EN_COURS").all()}
    for d in DEFIS_NATIONAUX_DEFAUT:
        if d["classe"] not in classes_existantes:
            defi = DefiNational(
                id=generate_uuid(),
                titre=d["titre"],
                description=d["description"],
                classe=d["classe"],
                matiere=d["matiere"],
                statut="EN_COURS",
                date_debut=now - timedelta(hours=2),
                date_fin=now + timedelta(days=7),  # Valable 1 semaine renouvelable
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
    """
    Retourne les défis nationaux ouverts avec questions épurées des réponses correctes.
    Chaque défi est instantanément appairé avec un rival lycéen malien certifié (style SoloLearn)
    afin qu'un élève puisse concourir à tout moment sans attendre d'autres camarades en ligne.
    """
    init_defis_nationaux_si_besoin(db)
    now = datetime.utcnow()
    query = db.query(DefiNational).filter(
        DefiNational.statut == "EN_COURS",
        DefiNational.date_fin > now,
    )
    if classe:
        norm_class = "12eme" if any(c in classe.lower() for c in ["12", "tse", "tsexp", "tll", "tss"]) else ("11eme" if "11" in classe else "10eme")
        query = query.filter(DefiNational.classe == norm_class)

    defis = query.all()
    # Si aucun défi dans la classe demandée, charger tous les défis en cours
    if not defis and classe:
        defis = db.query(DefiNational).filter(
            DefiNational.statut == "EN_COURS",
            DefiNational.date_fin > now,
        ).all()

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

        # Générer un rival fictif malien spécifique au défi
        adversaire = get_adversaire_fictif_pour_defi(
            defi_id=d.id,
            classe=d.classe,
            total_questions=len(questions_client),
        )

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
            "adversaire": adversaire,
            "mode_duel": "sololearn_instant_match",
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
    adversaire_nom: Optional[str] = None,
    adversaire_score: Optional[int] = None,
    adversaire_temps_sec: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Validation serveur des réponses d'un Défi National :
    1. Calcule le score réel strictement côté serveur.
    2. Permet à tout moment à l'élève de concourir et faire grimper ses scores (rejouabilité SoloLearn).
    3. Confronte l'élève à son rival malien (fictif ou réel) sans blocage.
    4. RÈGLE OFFICIELLE : Si l'élève gagne le défi face au rival, il remporte des pièces et des XP.
       Si l'élève NE GAGNE PAS, il N'OBTIENT AUCUNE PIÈCE (0 pièce), mais uniquement des points XP.
    5. Met à jour le meilleur score et le classement national officiel.
    """
    defi = db.query(DefiNational).filter(DefiNational.id == defi_id).first()
    if not defi:
        raise ValueError("Défi national introuvable.")

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

    # Établissement du rival malien (style SoloLearn)
    rival_ref = get_adversaire_fictif_pour_defi(
        defi_id=defi_id,
        classe=apprenant_classe,
        total_questions=total_questions,
        seed_str=apprenant_id,
    )
    nom_rival = adversaire_nom or rival_ref["nom"]
    score_rival = adversaire_score if adversaire_score is not None else rival_ref["score_simule"]
    temps_rival = adversaire_temps_sec if adversaire_temps_sec is not None else rival_ref["temps_simule_sec"]

    # Condition de Victoire face au rival (SoloLearn)
    # 1. Score supérieur au rival -> Victoire nette
    # 2. Score égal -> Déterminé par le temps le plus rapide ou score >= 60%
    if score > score_rival:
        est_victoire = True
    elif score == score_rival:
        est_victoire = (temps_ecoule_sec <= temps_rival) or (pourcentage >= 60)
    else:
        est_victoire = False

    # ─────────────────────────────────────────────────────────────────────────
    # RÈGLE DEMANDÉE :
    # Si on gagne -> attribution de pièces + points XP
    # Si on ne gagne pas -> AUCUNE PIÈCE (0 pièce), JUSTE DES XP !
    # ─────────────────────────────────────────────────────────────────────────
    if est_victoire:
        if pourcentage >= 80:
            pieces_gagnees = defi.recompense_pieces_top10  # 250 pièces
            xp_gagnes = 400
        elif pourcentage >= 50:
            pieces_gagnees = defi.recompense_pieces_participation * 2  # 100 pièces
            xp_gagnes = 250
        else:
            pieces_gagnees = defi.recompense_pieces_participation  # 50 pièces
            xp_gagnes = 150
        message = (
            f"Victoire éclatante contre {nom_rival} ({score} vs {score_rival}) ! "
            f"Tu gagnes {pieces_gagnees} Pièces AlterniA et {xp_gagnes} XP."
        )
    else:
        # DÉFAITE / NON GAGNÉ : ZÉRO PIÈCE, UNIQUEMENT DES XPS
        pieces_gagnees = 0
        xp_gagnes = 100
        message = (
            f"{nom_rival} a remporté ce défi ({score_rival} vs {score}). "
            f"Tu gagnes {xp_gagnes} XP d'entraînement, mais aucune pièce. "
            "Rejoue immédiatement pour battre son score et décrocher les pièces !"
        )

    # 1. Gestion de la rejouabilité et progression du score (Grimper ses scores à tout moment)
    deja_participe = (
        db.query(ParticipationDefiNational)
        .filter(
            ParticipationDefiNational.defi_id == defi_id,
            ParticipationDefiNational.apprenant_id == apprenant_id,
        )
        .first()
    )

    nouveau_record = False
    if deja_participe:
        # L'élève rejoue pour faire grimper ses scores au classement !
        est_meilleur_score = (score > deja_participe.score)
        est_meilleur_temps = (score == deja_participe.score and temps_ecoule_sec < deja_participe.temps_secondes)

        if est_meilleur_score or est_meilleur_temps:
            nouveau_record = True
            deja_participe.score = score
            deja_participe.temps_secondes = temps_ecoule_sec
            deja_participe.reponses_soumises_json = json.dumps(reponses)
            deja_participe.soumis_a = datetime.utcnow()

        # Cumul de l'expérience et des pièces
        deja_participe.xp_remportes += xp_gagnes
        deja_participe.pieces_remportees += pieces_gagnees
        deja_participe.apprenant_nom = apprenant_nom
        deja_participe.apprenant_classe = apprenant_classe
        participation = deja_participe
    else:
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
            soumis_a=datetime.utcnow(),
        )
        db.add(participation)
        nouveau_record = True

    # 2. Créditer les pièces dans le portefeuille UNIQUEMENT si l'élève a gagné (pieces_gagnees > 0)
    if pieces_gagnees > 0:
        tentative_ts = int(datetime.utcnow().timestamp())
        credit_coins(
            db=db,
            student_id=apprenant_id,
            amount=pieces_gagnees,
            origine="DEFI_NATIONAL",
            description=f"Victoire Défi National contre {nom_rival} : score {score}/{total_questions}",
            idempotency_key=f"defi_nat_{participation.id}_{tentative_ts}",
        )

    db.commit()
    db.refresh(participation)

    return {
        "succes": True,
        "est_victoire": est_victoire,
        "nouveau_record": nouveau_record,
        "score": score,
        "total_questions": total_questions,
        "pourcentage": pourcentage,
        "pieces_gagnees": pieces_gagnees,
        "xp_gagnes": xp_gagnes,
        "temps_secondes": temps_ecoule_sec,
        "adversaire": {
            "nom": nom_rival,
            "etablissement": rival_ref.get("etablissement"),
            "ville": rival_ref.get("ville"),
            "score": score_rival,
            "temps_secondes": temps_rival,
            "est_fictif": True,
        },
        "message": message,
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
