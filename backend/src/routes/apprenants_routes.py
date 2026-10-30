"""
Routes API pour la consultation des apprenants et de leurs sessions d'apprentissage.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.src.db.database import get_db
from backend.src.models.apprenant import ApprenantCreateRequest
from backend.src.services.apprenant_service import (
    create_apprenant,
    delete_apprenant,
    get_apprenant_detail,
    list_apprenant_sessions,
    list_apprenants,
)

router = APIRouter(prefix="/api/apprenants", tags=["Apprenants"])


@router.get("")
def api_liste_apprenants(db: Session = Depends(get_db)):
    """Liste de tous les apprenants enregistrés avec leur taux de maîtrise."""
    return list_apprenants(db)


@router.get("/leaderboard")
def api_classement_national(db: Session = Depends(get_db)):
    """Classement national des élèves du Mali (Terminale TSExp, TSE, etc.)."""
    from backend.src.services.apprenant_service import get_national_leaderboard
    return get_national_leaderboard(db)


@router.post("")
def api_creer_apprenant(req: ApprenantCreateRequest, db: Session = Depends(get_db)):
    """Enregistre un nouvel apprenant."""
    return create_apprenant(db, req)


@router.get("/{apprenant_id}")
def api_detail_apprenant(apprenant_id: str, db: Session = Depends(get_db)):
    """Fiche détaillée d'un apprenant."""
    return get_apprenant_detail(db, apprenant_id)


@router.delete("/{apprenant_id}")
def api_supprimer_apprenant(apprenant_id: str, db: Session = Depends(get_db)):
    """Supprime un apprenant."""
    return delete_apprenant(db, apprenant_id)


@router.get("/{apprenant_id}/sessions")
def api_sessions_apprenant(apprenant_id: str, db: Session = Depends(get_db)):
    """Historique des sessions d'apprentissage d'un élève."""
    return list_apprenant_sessions(db, apprenant_id)


@router.get("/gamification/stats")
def api_gamification_stats(
    eleve_nom: Optional[str] = Query(None),
    classe: Optional[str] = Query(None),
    student_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Retourne les statistiques réelles de gamification (Streak, XP, Séances) et le taux de progression par matière."""
    from backend.src.db.models import Apprenant, SessionApprentissage, SeanceRevisionModel
    from backend.src.services.wallet_service import get_wallet_summary

    apprenant: Optional[Apprenant] = None

    if student_id:
        apprenant = db.query(Apprenant).filter(
            (Apprenant.id == student_id)
            | (Apprenant.nom.ilike(f"%{student_id}%"))
            | (Apprenant.matricule == student_id)
        ).first()

    clean_name = (eleve_nom or "").strip()
    if not apprenant and clean_name and clean_name.lower() not in ("diallo", "eleve", "élève alternia", "nouveau"):
        apprenant = db.query(Apprenant).filter(
            (Apprenant.nom.ilike(f"%{clean_name}%")) | (Apprenant.prenom.ilike(f"%{clean_name}%"))
        ).first()

    # Si c'est un élève qui vient de s'inscrire ou non trouvé dans la base
    if not apprenant:
        target_id = student_id or clean_name or "nouvel_eleve"
        streak_days = 1  # 1er jour d'activité

        # XP issus des contributions culturelles validées
        culture_xp = 0
        try:
            from backend.src.db.models import CultureContribution
            contribs = db.query(CultureContribution).filter(
                (CultureContribution.auteur_id == target_id) | (CultureContribution.auteur_nom == target_id),
                CultureContribution.statut == "APPROUVE",
            ).all()
            culture_xp = sum(c.xp_attribues or 50 for c in contribs)
        except Exception:
            culture_xp = 0

        education_xp = 0
        total_seances = 0
        wallet_info = get_wallet_summary(db, target_id)
        education_coins = wallet_info["solde_education"]
        culture_coins = wallet_info["solde_culture"]
        subjects_progress = {
            "Sociologie Générale": 0,
            "Droit & Institutions": 0,
            "Science Politique": 0,
            "Histoire-Géographie": 0,
            "Économie": 0,
            "Philosophie": 0,
            "Mathématiques": 0,
            "Physique-Chimie": 0,
            "Biologie": 0,
            "Français": 0,
            "Anglais": 0,
        }
        return {
            "status": "success",
            "streak": streak_days,
            "streak_label": f"{streak_days}j",
            "xp": education_xp,
            "xp_label": f"{education_xp:,}".replace(",", " "),
            "coins": education_coins,
            "coins_label": f"{education_coins:,}".replace(",", " "),
            "valeur_fcfa": wallet_info["valeur_education_fcfa"],
            "valeur_fcfa_label": wallet_info["valeur_education_fcfa_label"],
            "seances": total_seances,
            "seances_label": f"{total_seances}",
            "education": {
                "xp": education_xp,
                "xp_label": f"{education_xp:,}".replace(",", " "),
                "coins": education_coins,
                "coins_label": f"{education_coins:,}".replace(",", " "),
                "valeur_fcfa": wallet_info["valeur_education_fcfa"],
                "streak": streak_days,
                "seances": total_seances,
            },
            "culture": {
                "xp": culture_xp,
                "xp_label": f"{culture_xp:,}".replace(",", " "),
                "coins": culture_coins,
                "coins_label": f"{culture_coins:,}".replace(",", " "),
                "valeur_fcfa": wallet_info["valeur_culture_fcfa"],
            },
            "subjects_progress": subjects_progress,
        }

    resolved_student_id = apprenant.id
    sessions = db.query(SessionApprentissage).filter(SessionApprentissage.apprenant_id == apprenant.id).all()
    try:
        revisions = db.query(SeanceRevisionModel).filter(SeanceRevisionModel.apprenant_id == apprenant.id).all()
    except Exception:
        revisions = []
    total_seances = len(sessions) + len(revisions)
    questions_count = apprenant.questions_posees or 0

    # XP issus des contributions culturelles validées par le Super Admin
    culture_xp = 0
    try:
        from backend.src.db.models import CultureContribution
        author_keys = {apprenant.id, apprenant.nom, apprenant.prenom, clean_name}
        if student_id:
            author_keys.add(student_id)
        author_keys = {k for k in author_keys if k}
        contribs = db.query(CultureContribution).filter(
            (CultureContribution.auteur_id.in_(author_keys)) | (CultureContribution.auteur_nom.in_(author_keys)),
            CultureContribution.statut == "APPROUVE",
        ).all()
        culture_xp = sum(c.xp_attribues or 50 for c in contribs)
    except Exception:
        culture_xp = 0

    # Séparation stricte entre l'XP Éducation et l'XP Culture
    if total_seances == 0 and questions_count == 0:
        education_xp = 0
        streak_days = 1
    else:
        education_xp = (questions_count * 20) + (total_seances * 40)
        streak_days = max(1, min(total_seances + 1, 30))

    wallet_info = get_wallet_summary(db, resolved_student_id)
    # Si le portefeuille sous apprenant.id est vide mais qu'un solde existe sous apprenant.nom ou student_id
    if wallet_info["solde_pieces"] == 0:
        candidates = [c for c in [apprenant.nom, student_id, clean_name] if c and c != resolved_student_id]
        for cand in candidates:
            alt_wallet = get_wallet_summary(db, cand)
            if alt_wallet["solde_pieces"] > 0:
                wallet_info = alt_wallet
                break

    education_coins = wallet_info["solde_education"]
    culture_coins = wallet_info["solde_culture"]

    subjects_progress = {
        "Sociologie Générale": 0,
        "Droit & Institutions": 0,
        "Science Politique": 0,
        "Histoire-Géographie": 0,
        "Économie": 0,
        "Philosophie": 0,
        "Mathématiques": 0,
        "Physique-Chimie": 0,
        "Biologie": 0,
        "Français": 0,
        "Anglais": 0,
    }
    for s in sessions:
        if s.matiere:
            norm_sub = s.matiere.strip()
            subjects_progress[norm_sub] = min(100, subjects_progress.get(norm_sub, 0) + 15)

    return {
        "status": "success",
        "streak": streak_days,
        "streak_label": f"{streak_days}j",
        "xp": education_xp,
        "xp_label": f"{education_xp:,}".replace(",", " "),
        "coins": education_coins,
        "coins_label": f"{education_coins:,}".replace(",", " "),
        "valeur_fcfa": wallet_info["valeur_education_fcfa"],
        "valeur_fcfa_label": wallet_info["valeur_education_fcfa_label"],
        "seances": total_seances,
        "seances_label": f"{total_seances}",
        "education": {
            "xp": education_xp,
            "xp_label": f"{education_xp:,}".replace(",", " "),
            "coins": education_coins,
            "coins_label": f"{education_coins:,}".replace(",", " "),
            "valeur_fcfa": wallet_info["valeur_education_fcfa"],
            "streak": streak_days,
            "seances": total_seances,
        },
        "culture": {
            "xp": culture_xp,
            "xp_label": f"{culture_xp:,}".replace(",", " "),
            "coins": culture_coins,
            "coins_label": f"{culture_coins:,}".replace(",", " "),
            "valeur_fcfa": wallet_info["valeur_culture_fcfa"],
        },
        "subjects_progress": subjects_progress,
    }
