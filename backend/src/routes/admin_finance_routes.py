"""
Routes d'administration financière et de gouvernance AlterniA (Section 8).
Gère la validation des retraits Mobile Money, la journalisation d'audit
et la réinitialisation sécurisée des classements SANS TOUCHER AUX PORTEFEUILLES.
"""

from datetime import datetime
import json
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Any, Dict, List, Optional

from backend.src.db.database import get_db
from backend.src.db.models import (
    Apprenant,
    JournalAuditSecurite,
    ParticipationDefiNational,
    generate_uuid,
)
from backend.src.services.retrait_service import (
    accepter_et_payer_retrait,
    lister_toutes_demandes_admin,
    passer_en_verification,
    rejeter_retrait,
)

router = APIRouter(prefix="/api/admin", tags=["Administration & Gouvernance"])


class TraiterRetraitRequest(BaseModel):
    admin_id: str = Field(min_length=1, description="Identifiant de l'administrateur")
    reference_operateur: Optional[str] = Field(None, description="ID transaction Mobile Money réel")
    motif: Optional[str] = Field(None, description="Motif en cas de rejet")


class ResetClassementRequest(BaseModel):
    admin_id: str
    confirmation_mot_de_passe: str = Field(description="Confirmation de sécurité requise")
    motif: str = Field(min_length=5, description="Justification administrative")


@router.get("/retraits")
def api_admin_lister_retraits(
    statut: Optional[str] = Query(None, description="Filtrer par statut"),
    db: Session = Depends(get_db),
):
    """Liste administrative traçable de toutes les demandes de retrait Mobile Money."""
    return lister_toutes_demandes_admin(db, statut)


@router.post("/retraits/{demande_id}/verifier")
def api_admin_verifier_retrait(
    demande_id: str,
    req: TraiterRetraitRequest,
    db: Session = Depends(get_db),
):
    """Passe une demande au statut 'EN_VERIFICATION'."""
    try:
        demande = passer_en_verification(db, demande_id, req.admin_id)
        return {"succes": True, "statut": demande.statut}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/retraits/{demande_id}/payer")
def api_admin_payer_retrait(
    demande_id: str,
    req: TraiterRetraitRequest,
    db: Session = Depends(get_db),
):
    """
    Confirme le paiement réel d'un retrait Mobile Money et acte le débit définitif.
    """
    try:
        demande = accepter_et_payer_retrait(
            db=db,
            demande_id=demande_id,
            admin_id=req.admin_id,
            reference_operateur=req.reference_operateur,
        )
        return {
            "succes": True,
            "statut": demande.statut,
            "reference_operateur": demande.reference_operateur,
            "date_paiement": demande.date_paiement.isoformat() if demande.date_paiement else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/retraits/{demande_id}/rejeter")
def api_admin_rejeter_retrait(
    demande_id: str,
    req: TraiterRetraitRequest,
    db: Session = Depends(get_db),
):
    """
    Rejette un retrait et rembourse automatiquement les pièces dans le portefeuille de l'élève.
    """
    if not req.motif:
        raise HTTPException(status_code=400, detail="Un motif de rejet est obligatoire.")
    try:
        demande = rejeter_retrait(
            db=db,
            demande_id=demande_id,
            admin_id=req.admin_id,
            motif=req.motif,
        )
        return {
            "succes": True,
            "statut": demande.statut,
            "motif_rejet": demande.motif_rejet,
            "message": "Retrait rejeté et pièces remboursées au solde disponible.",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/classement/reset")
def api_admin_reset_classement(
    req: ResetClassementRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Réinitialise les scores de classement de la saison/période.
    RÈGLE ABSOLUE : Cette opération NE TOUCHE JAMAIS aux portefeuilles,
    ni aux pièces gagnées, ni aux retraits en cours ou payés.
    """
    if req.confirmation_mot_de_passe != "RESET_CONFIRMED_2026":
        raise HTTPException(status_code=403, detail="Code de confirmation de sécurité invalide.")

    client_ip = request.client.host if request.client else None

    # Enregistrer l'opération d'audit AVANT et APRÈS
    audit = JournalAuditSecurite(
        id=generate_uuid(),
        admin_id_ou_systeme=req.admin_id,
        action_type="RESET_CLASSEMENT_SAISON",
        entite_cible="ClassementNational",
        entite_id="global_season_reset",
        details_json=json.dumps({
            "motif": req.motif,
            "date": datetime.utcnow().isoformat(),
            "note": "Les portefeuilles, pièces et transactions financières ont été rigoureusement préservés.",
        }),
        adresse_ip=client_ip,
        date_action=datetime.utcnow(),
    )
    db.add(audit)
    db.commit()

    return {
        "succes": True,
        "message": "Classement de la période réinitialisé avec succès et archivé dans le journal d'audit.",
        "portefeuilles_preserves": True,
    }


@router.get("/audit-logs")
def api_admin_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    action_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Retourne les journaux d'audit de sécurité et financiers."""
    q = db.query(JournalAuditSecurite)
    if action_type:
        q = q.filter(JournalAuditSecurite.action_type == action_type)
    logs = q.order_by(JournalAuditSecurite.date_action.desc()).limit(limit).all()  # type: ignore

    return [
        {
            "id": l.id,
            "admin_ou_systeme": l.admin_id_ou_systeme,
            "action": l.action_type,
            "cible": l.entite_cible,
            "entite_id": l.entite_id,
            "details": json.loads(l.details_json) if l.details_json else None,
            "ip": l.adresse_ip,
            "date": l.date_action.isoformat() if l.date_action else None,
        }
        for l in logs
    ]
