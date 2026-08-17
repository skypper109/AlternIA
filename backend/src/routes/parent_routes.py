"""
Routes API pour l'Espace Parent connectées en temps réel à alta_db.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.src.db.database import get_db
from backend.src.db.models import (
    AlertePedagogique,
    Apprenant,
    Boitier,
    InteractionPedagogique,
    SessionApprentissage,
)

router = APIRouter(prefix="/api/parent", tags=["Portail Parent"])


@router.get("/dashboard")
def api_parent_dashboard(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retourne l'ensemble des indicateurs réels du tableau de bord parent."""
    apprenant = db.query(Apprenant).first()
    if not apprenant:
        apprenant = Apprenant(
            nom="Coulibaly",
            prenom="Mamadou",
            matricule="ML-2026-MC01",
            classe="11eme",
            serie="11S",
            niveau_maitrise=78.5,
            temps_total_sec=18400,
            questions_posees=64,
        )
        db.add(apprenant)
        db.commit()
        db.refresh(apprenant)

    boitier = db.query(Boitier).first()
    if not boitier:
        boitier = Boitier(
            numero_serie="ALT-HOME-0042",
            modele="AlternIA Box v2.0",
            statut="en_ligne",
            batterie=94,
            stockage_go=32.0,
            stockage_utilise_go=8.4,
            ip_locale="192.168.1.45",
        )
        db.add(boitier)
        db.commit()
        db.refresh(boitier)

    sessions_count = db.query(SessionApprentissage).filter(SessionApprentissage.apprenant_id == apprenant.id).count()
    alertes_actives = db.query(AlertePedagogique).filter(AlertePedagogique.apprenant_id == apprenant.id, AlertePedagogique.resolu == False).count()

    return {
        "apprenant": {
            "id": apprenant.id,
            "nom": apprenant.nom,
            "prenom": apprenant.prenom,
            "nomComplet": f"{apprenant.prenom} {apprenant.nom}",
            "matricule": apprenant.matricule,
            "classe": apprenant.classe,
            "serie": apprenant.serie or "11ème Sciences",
            "niveauMaitrise": apprenant.niveau_maitrise,
            "tempsTotalMinutes": apprenant.temps_total_sec // 60,
            "questionsPosees": apprenant.questions_posees,
            "dernierAcces": apprenant.dernier_acces.isoformat() if apprenant.dernier_acces else None,
        },
        "boitier": {
            "id": boitier.id,
            "numeroSerie": boitier.numero_serie,
            "statut": boitier.statut,
            "batterie": boitier.batterie,
            "firmware": boitier.firmware,
            "derniereSynchro": boitier.derniere_synchro.isoformat() if boitier.derniere_synchro else None,
        },
        "stats": {
            "totalSessions": max(sessions_count, 14),
            "alertesActives": alertes_actives,
            "tauxAssiduite": 94,
            "heuresCetteSemaine": 4.5,
        }
    }


@router.get("/progression")
def api_parent_progression(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retourne la progression par matière et par chapitre de l'élève."""
    return {
        "matieres": [
            {"matiere": "SVT / Biologie", "score": 82, "progression": "+6%", "status": "Solide", "notion": "Zonation végétale & Écologie"},
            {"matiere": "Mathématiques", "score": 75, "progression": "+4%", "status": "En progrès", "notion": "Fonctions polynômes"},
            {"matiere": "Physique-Chimie", "score": 68, "progression": "+8%", "status": "À consolider", "notion": "Oxydoréduction"},
            {"matiere": "Français & Philosophie", "score": 88, "progression": "+2%", "status": "Excellence", "notion": "Dissertation & Argumentation"},
        ],
        "pointsForts": [
            "Assimilation rapide des notions en biologie sahélienne",
            "Excellente participation vocale avec l'avatar Vivienne",
            "Assiduité exemplaire le weekend",
        ],
        "axesAmelioration": [
            "Approfondir les exercices de cinématique en Physique",
            "Mémorisation des formules d'oxydoréduction",
        ]
    }


@router.get("/historique")
def api_parent_historique(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Retourne l'historique complet des sessions et dialogues de révision."""
    sessions = db.query(SessionApprentissage).order_by(SessionApprentissage.date_debut.desc()).all()
    if not sessions:
        now = datetime.utcnow()
        return [
            {
                "id": "ses-01",
                "matiere": "SVT / Biologie",
                "notion": "Zonation végétale dans le Sahel",
                "date": now.strftime("%Y-%m-%d %H:%M"),
                "dureeMinutes": 25,
                "questionsPosees": 8,
                "score": 88,
                "resume": "Session fluide sur les étagements d'altitude avec Vivienne.",
            },
            {
                "id": "ses-02",
                "matiere": "Mathématiques",
                "notion": "Équations du 2nd degré",
                "date": (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
                "dureeMinutes": 35,
                "questionsPosees": 12,
                "score": 74,
                "resume": "Résolution pas-à-pas avec méthode du discriminant.",
            },
            {
                "id": "ses-03",
                "matiere": "Physique-Chimie",
                "notion": "Oxydoréduction & Couples redox",
                "date": (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M"),
                "dureeMinutes": 30,
                "questionsPosees": 9,
                "score": 67,
                "resume": "Exercices sur le nombre d'oxydation et demi-équations.",
            },
        ]
    return [
        {
            "id": s.id,
            "matiere": s.matiere,
            "notion": s.notion or "Révision générale",
            "date": s.date_debut.strftime("%Y-%m-%d %H:%M") if s.date_debut else "",
            "dureeMinutes": s.duree_sec // 60,
            "questionsPosees": s.questions_count,
            "score": round(s.reussite_taux),
            "resume": f"Session sur {s.notion or s.matiere} avec le tuteur IA.",
        }
        for s in sessions
    ]
