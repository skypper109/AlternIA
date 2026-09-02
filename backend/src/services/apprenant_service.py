"""
Service de gestion des profils apprenants et historique de leurs sessions.
"""

from typing import Any, Dict, List
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.src.db.models import Apprenant, SessionApprentissage


def list_apprenants(db: Session) -> List[Dict[str, Any]]:
    """Retourne la liste de tous les apprenants avec progression réelle."""
    apprenants = db.query(Apprenant).all()
    return [
        {
            "id": a.id,
            "nom": a.nom,
            "prenom": a.prenom,
            "nomComplet": f"{a.prenom} {a.nom}",
            "matricule": a.matricule,
            "classe": a.classe,
            "serie": a.serie,
            "niveauMaitrise": a.niveau_maitrise,
            "tempsTotalSec": a.temps_total_sec,
            "questionsPosees": a.questions_posees,
            "dernierAcces": a.dernier_acces.isoformat() if a.dernier_acces else None,
            "boitierId": a.boitier_id,
            "etablissementId": a.etablissement_id,
        }
        for a in apprenants
    ]


def get_apprenant_detail(db: Session, apprenant_id: str) -> Dict[str, Any]:
    """Retourne les informations détaillées d'un apprenant."""
    a = db.query(Apprenant).filter(Apprenant.id == apprenant_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Apprenant introuvable")
    return {
        "id": a.id,
        "nom": a.nom,
        "prenom": a.prenom,
        "nomComplet": f"{a.prenom} {a.nom}",
        "matricule": a.matricule,
        "classe": a.classe,
        "serie": a.serie,
        "niveauMaitrise": a.niveau_maitrise,
        "tempsTotalSec": a.temps_total_sec,
        "questionsPosees": a.questions_posees,
        "dernierAcces": a.dernier_acces.isoformat() if a.dernier_acces else None,
        "boitierId": a.boitier_id,
        "etablissementId": a.etablissement_id,
    }


def list_apprenant_sessions(db: Session, apprenant_id: str) -> List[Dict[str, Any]]:
    """Retourne l'historique des sessions d'apprentissage d'un élève."""
    sessions = (
        db.query(SessionApprentissage)
        .filter(SessionApprentissage.apprenant_id == apprenant_id)
        .order_by(SessionApprentissage.date_debut.desc())
        .all()
    )
    return [
        {
            "id": s.id,
            "matiere": s.matiere,
            "chapitre": s.chapitre,
            "notion": s.notion,
            "dateDebut": s.date_debut.isoformat() if s.date_debut else None,
            "dateFin": s.date_fin.isoformat() if s.date_fin else None,
            "dureeSec": s.duree_sec,
            "questionsCount": s.questions_count,
            "reussiteTaux": s.reussite_taux,
        }
        for s in sessions
    ]


def create_apprenant(db: Session, req: Any) -> Dict[str, Any]:
    """Enregistre un nouvel apprenant dans l'établissement."""
    from datetime import datetime
    import uuid
    apprenant_id = f"eleve_{uuid.uuid4().hex[:8]}"
    matricule = req.matricule or f"ML-2026-{uuid.uuid4().hex[:4].upper()}"
    nouveau = Apprenant(
        id=apprenant_id,
        matricule=matricule,
        nom=req.nom,
        prenom=req.prenom,
        classe=req.classe,
        serie=req.serie or "generale",
        niveau_maitrise=75,
        temps_total_sec=0,
        questions_posees=0,
        etablissement_id=req.etablissement_id or "etab-lbad-bamako",
        boitier_id=req.boitier_id or "box_001",
        dernier_acces=datetime.utcnow(),
    )
    db.add(nouveau)
    db.commit()
    db.refresh(nouveau)
    return {
        "id": nouveau.id,
        "nom": nouveau.nom,
        "prenom": nouveau.prenom,
        "nomComplet": f"{nouveau.prenom} {nouveau.nom}",
        "matricule": nouveau.matricule,
        "classe": nouveau.classe,
        "serie": nouveau.serie,
        "niveauMaitrise": nouveau.niveau_maitrise,
        "tempsTotalSec": nouveau.temps_total_sec,
        "questionsPosees": nouveau.questions_posees,
        "dernierAcces": nouveau.dernier_acces.isoformat() if nouveau.dernier_acces else None,
        "boitierId": nouveau.boitier_id,
        "etablissementId": nouveau.etablissement_id,
    }


def delete_apprenant(db: Session, apprenant_id: str) -> Dict[str, Any]:
    """Supprime le dossier d'un apprenant."""
    a = db.query(Apprenant).filter(Apprenant.id == apprenant_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Apprenant introuvable")
    db.delete(a)
    db.commit()
    return {"succes": True, "message": f"Apprenant {apprenant_id} supprimé avec succès"}
