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
        apprenant = db.query(Apprenant).filter(Apprenant.id == student_id).first()

    clean_name = (eleve_nom or "").strip()
    if not apprenant and clean_name and clean_name.lower() not in ("diallo", "eleve", "élève alternia", "nouveau"):
        apprenant = db.query(Apprenant).filter(
            (Apprenant.nom.ilike(f"%{clean_name}%")) | (Apprenant.prenom.ilike(f"%{clean_name}%"))
        ).first()

    # Si c'est un élève qui vient de s'inscrire ou non trouvé dans la base de démo
    if not apprenant and clean_name:
        # Nouvel apprenant inscrit : initialise avec des statistiques vierges et réalistes
        streak_days = 1  # 1er jour d'activité
        total_xp = 0
        total_seances = 0
        wallet_info = get_wallet_summary(db, clean_name)
        coins_count = wallet_info["solde_pieces"]
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
            "xp": total_xp,
            "xp_label": f"{total_xp}",
            "coins": coins_count,
            "coins_label": f"{coins_count}",
            "valeur_fcfa": wallet_info["valeur_fcfa"],
            "valeur_fcfa_label": wallet_info["valeur_fcfa_label"],
            "seances": total_seances,
            "seances_label": f"{total_seances}",
            "subjects_progress": subjects_progress,
        }

    # Si c'est un élève existant ou mode démo général
    if not apprenant and classe:
        apprenant = db.query(Apprenant).filter(Apprenant.classe == classe).first()
    if not apprenant:
        apprenant = db.query(Apprenant).first()

    if apprenant:
        student_id = apprenant.id
        sessions = db.query(SessionApprentissage).filter(SessionApprentissage.apprenant_id == apprenant.id).all()
        revisions = db.query(SeanceRevisionModel).filter(SeanceRevisionModel.apprenant_id == apprenant.id).all()
        total_seances = len(sessions) + len(revisions)
        questions_count = apprenant.questions_posees or 0

        # Si c'est un compte nouvellement créé avec 0 session réelle
        if total_seances == 0 and questions_count == 0:
            total_xp = 0
            streak_days = 1
        else:
            total_xp = (questions_count * 20) + (total_seances * 40)
            streak_days = max(1, min(total_seances + 1, 30))
    else:
        student_id = "eleve_defaut"
        sessions = []
        total_seances = 0
        total_xp = 0
        streak_days = 1

    wallet_info = get_wallet_summary(db, student_id)
    coins_count = wallet_info["solde_pieces"]

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
        "xp": total_xp,
        "xp_label": f"{total_xp:,}".replace(",", " "),
        "coins": coins_count,
        "coins_label": f"{coins_count:,}".replace(",", " "),
        "valeur_fcfa": wallet_info["valeur_fcfa"],
        "valeur_fcfa_label": wallet_info["valeur_fcfa_label"],
        "seances": total_seances,
        "seances_label": f"{total_seances}",
        "subjects_progress": subjects_progress,
    }
