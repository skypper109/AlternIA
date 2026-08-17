"""
Service de gestion des alertes pédagogiques en temps réel.
"""

from typing import Any, Dict, List
from sqlalchemy.orm import Session

from backend.src.db.models import AlertePedagogique


def list_alertes(db: Session) -> List[Dict[str, Any]]:
    """Retourne toutes les alertes pédagogiques ordonnées par date décroissante."""
    alertes = db.query(AlertePedagogique).order_by(AlertePedagogique.date_creation.desc()).all()
    return [
        {
            "id": alt.id,
            "apprenantId": alt.apprenant_id,
            "titre": alt.titre,
            "description": alt.description,
            "type": alt.type_alerte,
            "gravite": alt.gravite,
            "matiere": alt.matiere,
            "resolu": alt.resolu,
            "dateCreation": alt.date_creation.isoformat() if alt.date_creation else None,
        }
        for alt in alertes
    ]


def resolve_alerte(db: Session, alerte_id: str) -> Dict[str, Any]:
    """Marque une alerte pédagogique comme résolue."""
    alt = db.query(AlertePedagogique).filter(AlertePedagogique.id == alerte_id).first()
    if alt:
        alt.resolu = True
        db.commit()
    return {"succes": True, "id": alerte_id, "resolu": True}
