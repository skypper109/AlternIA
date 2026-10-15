"""
Service de gestion des retraits Mobile Money (Module G).
Supporte Orange Money Mali, Moov Money Mali et Wave Mali.
Garantit la réservation atomique des pièces, le suivi de cycle de vie traçable,
la gestion des rejets/échecs avec remboursement, et le journal d'audit administratif.
"""

from datetime import datetime
import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.src.db.models import DemandeRetrait, JournalAuditSecurite, generate_uuid
from backend.src.services.wallet_service import (
    SEUIL_MINIMAL_RETRAIT_PIECES,
    PLAFOND_MAXIMAL_RETRAIT_PIECES,
    TAUX_CONVERSION_PIECE_FCFA,
    confirm_withdrawal_debit,
    refund_reserved_coins,
    reserve_coins_for_withdrawal,
)

logger = logging.getLogger("AlternIA.RetraitService")

OPERATEURS_AUTORISES = {
    "ORANGE_MONEY": "Orange Money Mali (Orange)",
    "MOOV_MONEY": "Moov Money Mali (Malitel)",
    "WAVE": "Wave Mali",
}

STATUTS_RETRAIT = [
    "EN_ATTENTE",
    "EN_VERIFICATION",
    "ACCEPTEE",
    "REJETEE",
    "EN_COURS_DE_PAIEMENT",
    "PAYEE",
    "ECHEC",
]


def _valider_numero_telephone_mali(numero: str) -> str:
    """Valide et normalise le numéro Mobile Money malien."""
    propre = re.sub(r"[^0-9+]", "", numero.strip())
    if propre.startswith("+223"):
        propre = propre[4:]
    elif propre.startswith("00223"):
        propre = propre[5:]

    if not re.match(r"^[5-9][0-9]{7}$", propre):
        raise ValueError(
            "Le numéro de téléphone Mobile Money malien doit comporter 8 chiffres valides (ex: 76 12 34 56 ou 66 12 34 56)."
        )
    return f"+223 {propre[:2]} {propre[2:4]} {propre[4:6]} {propre[6:]}"


def creer_demande_retrait(
    db: Session,
    apprenant_id: str,
    pieces: int,
    operateur: str,
    numero_telephone: str,
    nom_titulaire: str,
    ip_client: Optional[str] = None,
) -> DemandeRetrait:
    """Crée une demande de retrait et réserve immédiatement les pièces de façon atomique."""
    op_clean = operateur.upper().strip()
    if op_clean not in OPERATEURS_AUTORISES:
        raise ValueError(f"Opérateur invalide. Choisissez parmi : {', '.join(OPERATEURS_AUTORISES.keys())}")

    if pieces < SEUIL_MINIMAL_RETRAIT_PIECES:
        raise ValueError(f"Le seuil minimal est de {SEUIL_MINIMAL_RETRAIT_PIECES} pièces ({SEUIL_MINIMAL_RETRAIT_PIECES * TAUX_CONVERSION_PIECE_FCFA} FCFA).")

    if pieces > PLAFOND_MAXIMAL_RETRAIT_PIECES:
        raise ValueError(f"Le plafond maximal par demande est de {PLAFOND_MAXIMAL_RETRAIT_PIECES} pièces ({PLAFOND_MAXIMAL_RETRAIT_PIECES * TAUX_CONVERSION_PIECE_FCFA} FCFA).")

    nom_propre = nom_titulaire.strip()
    if len(nom_propre) < 3:
        raise ValueError("Veuillez indiquer le nom complet du titulaire du compte Mobile Money.")

    numero_formate = _valider_numero_telephone_mali(numero_telephone)
    montant_fcfa = pieces * TAUX_CONVERSION_PIECE_FCFA
    code_ref = f"ALT-RET-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    # 1. Réserver atomiquement les pièces
    reserve_coins_for_withdrawal(
        db=db,
        student_id=apprenant_id,
        amount=pieces,
        description=f"Réservation pour retrait {montant_fcfa} FCFA ({op_clean})",
        idempotency_key=f"retrait_res_{code_ref}",
    )

    # 2. Enregistrer la demande de retrait
    demande = DemandeRetrait(
        id=generate_uuid(),
        apprenant_id=apprenant_id,
        numero_transaction_ref=code_ref,
        pieces_debitees=pieces,
        montant_fcfa=montant_fcfa,
        operateur=op_clean,
        numero_telephone=numero_formate,
        nom_titulaire=nom_propre,
        statut="EN_ATTENTE",
        date_demande=datetime.utcnow(),
        ip_demandeur=ip_client,
    )
    db.add(demande)

    # 3. Journaliser l'audit
    audit = JournalAuditSecurite(
        id=generate_uuid(),
        admin_id_ou_systeme=apprenant_id,
        action_type="CREATION_DEMANDE_RETRAIT",
        entite_cible="DemandeRetrait",
        entite_id=demande.id,
        details_json=json.dumps({
            "code_ref": code_ref,
            "pieces": pieces,
            "montant_fcfa": montant_fcfa,
            "operateur": op_clean,
        }),
        adresse_ip=ip_client,
        date_action=datetime.utcnow(),
    )
    db.add(audit)
    db.commit()
    db.refresh(demande)
    return demande


def passer_en_verification(db: Session, demande_id: str, admin_id: str) -> DemandeRetrait:
    """Marque une demande de retrait comme étant en cours de vérification administrative."""
    demande = db.query(DemandeRetrait).filter(DemandeRetrait.id == demande_id).first()
    if not demande:
        raise ValueError("Demande de retrait introuvable.")

    if demande.statut != "EN_ATTENTE":
        raise ValueError(f"Impossible de vérifier une demande au statut {demande.statut}.")

    demande.statut = "EN_VERIFICATION"
    demande.traite_par_admin_id = admin_id
    demande.date_traitement = datetime.utcnow()

    db.add(JournalAuditSecurite(
        id=generate_uuid(),
        admin_id_ou_systeme=admin_id,
        action_type="VERIFICATION_RETRAIT",
        entite_cible="DemandeRetrait",
        entite_id=demande.id,
        date_action=datetime.utcnow(),
    ))
    db.commit()
    db.refresh(demande)
    return demande


def accepter_et_payer_retrait(
    db: Session,
    demande_id: str,
    admin_id: str,
    reference_operateur: Optional[str] = None,
) -> DemandeRetrait:
    """Valide et confirme le paiement réel du retrait vers le compte Mobile Money."""
    demande = db.query(DemandeRetrait).filter(DemandeRetrait.id == demande_id).first()
    if not demande:
        raise ValueError("Demande de retrait introuvable.")

    if demande.statut not in ["EN_ATTENTE", "EN_VERIFICATION", "ACCEPTEE", "EN_COURS_DE_PAIEMENT"]:
        raise ValueError(f"Transition non autorisée depuis le statut {demande.statut}.")

    # Confirmer le débit définitif dans le portefeuille
    confirm_withdrawal_debit(
        db=db,
        student_id=demande.apprenant_id,
        amount=demande.pieces_debitees,
        description=f"Paiement Mobile Money effectué ({demande.montant_fcfa} FCFA sur {demande.numero_telephone})",
    )

    demande.statut = "PAYEE"
    demande.reference_operateur = reference_operateur or f"EXT-{uuid.uuid4().hex[:8].upper()}"
    demande.traite_par_admin_id = admin_id
    demande.date_traitement = demande.date_traitement or datetime.utcnow()
    demande.date_paiement = datetime.utcnow()

    db.add(JournalAuditSecurite(
        id=generate_uuid(),
        admin_id_ou_systeme=admin_id,
        action_type="PAIEMENT_RETRAIT_CONFIRME",
        entite_cible="DemandeRetrait",
        entite_id=demande.id,
        details_json=json.dumps({
            "montant_fcfa": demande.montant_fcfa,
            "reference_operateur": demande.reference_operateur,
        }),
        date_action=datetime.utcnow(),
    ))
    db.commit()
    db.refresh(demande)
    return demande


def rejeter_retrait(
    db: Session,
    demande_id: str,
    admin_id: str,
    motif: str,
) -> DemandeRetrait:
    """Rejette une demande de retrait et rembourse intégralement les pièces réservées."""
    demande = db.query(DemandeRetrait).filter(DemandeRetrait.id == demande_id).first()
    if not demande:
        raise ValueError("Demande de retrait introuvable.")

    if demande.statut in ["PAYEE", "REJETEE"]:
        raise ValueError(f"Impossible de rejeter une demande déjà finalisée au statut {demande.statut}.")

    # Remboursement atomique
    refund_reserved_coins(
        db=db,
        student_id=demande.apprenant_id,
        amount=demande.pieces_debitees,
        description=f"Remboursement suite au rejet du retrait ({motif})",
    )

    demande.statut = "REJETEE"
    demande.motif_rejet = motif
    demande.traite_par_admin_id = admin_id
    demande.date_traitement = datetime.utcnow()

    db.add(JournalAuditSecurite(
        id=generate_uuid(),
        admin_id_ou_systeme=admin_id,
        action_type="REJET_RETRAIT",
        entite_cible="DemandeRetrait",
        entite_id=demande.id,
        details_json=json.dumps({"motif": motif, "pieces_remboursees": demande.pieces_debitees}),
        date_action=datetime.utcnow(),
    ))
    db.commit()
    db.refresh(demande)
    return demande


def lister_demandes_apprenant(db: Session, apprenant_id: str) -> List[Dict[str, Any]]:
    """Liste l'historique de retraits d'un apprenant."""
    demandes = (
        db.query(DemandeRetrait)
        .filter(DemandeRetrait.apprenant_id == apprenant_id)
        .order_by(desc(DemandeRetrait.date_demande))
        .all()
    )
    return [_serialiser_demande(d) for d in demandes]


def lister_toutes_demandes_admin(db: Session, statut_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Vue administrative traçable de tous les retraits."""
    query = db.query(DemandeRetrait)
    if statut_filter:
        query = query.filter(DemandeRetrait.statut == statut_filter.upper())
    demandes = query.order_by(desc(DemandeRetrait.date_demande)).all()
    return [_serialiser_demande(d) for d in demandes]


def _serialiser_demande(d: DemandeRetrait) -> Dict[str, Any]:
    return {
        "id": d.id,
        "ref": d.numero_transaction_ref,
        "apprenant_id": d.apprenant_id,
        "pieces": d.pieces_debitees,
        "montant_fcfa": d.montant_fcfa,
        "montant_fcfa_label": f"{d.montant_fcfa:,} FCFA".replace(",", " "),
        "operateur": d.operateur,
        "operateur_label": OPERATEURS_AUTORISES.get(d.operateur, d.operateur),
        "numero_telephone": d.numero_telephone,
        "nom_titulaire": d.nom_titulaire,
        "statut": d.statut,
        "motif_rejet": d.motif_rejet,
        "reference_operateur": d.reference_operateur,
        "date_demande": d.date_demande.isoformat() if d.date_demande else None,
        "date_traitement": d.date_traitement.isoformat() if d.date_traitement else None,
        "date_paiement": d.date_paiement.isoformat() if d.date_paiement else None,
    }
