"""
Service central de gestion du Portefeuille et des Transactions de Pièces AlterniA (Module F).
Garantit la traçabilité complète, la cohérence du solde, la protection contre l'idempotence
et la séparation stricte entre pièces disponibles, réservées et argent convertible.
"""

from datetime import datetime
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.src.db.models import Portefeuille, TransactionPiece, generate_uuid

logger = logging.getLogger("AlternIA.WalletService")

# Taux de conversion officiel : 1 pièce = 2 FCFA (configurable)
TAUX_CONVERSION_PIECE_FCFA = 2
SEUIL_MINIMAL_RETRAIT_PIECES = 100  # Minimum 100 pièces (200 FCFA)
PLAFOND_MAXIMAL_RETRAIT_PIECES = 25000  # Plafond par demande : 50 000 FCFA


def get_or_create_wallet(db: Session, student_id: str) -> Portefeuille:
    """Récupère ou initialise le portefeuille d'un apprenant."""
    wallet = db.query(Portefeuille).filter(Portefeuille.apprenant_id == student_id).first()
    if not wallet:
        wallet = Portefeuille(
            id=generate_uuid(),
            apprenant_id=student_id,
            solde_pieces=240,  # Solde d'accueil initial
            pieces_reservees=0,
            pieces_retirees_total=0,
            argent_total_gagne_fcfa=480,
            date_creation=datetime.utcnow(),
            date_mise_a_jour=datetime.utcnow(),
        )
        db.add(wallet)
        db.commit()
        db.refresh(wallet)

        # Enregistrer la transaction initiale de bienvenue
        init_tx = TransactionPiece(
            id=generate_uuid(),
            portefeuille_id=wallet.id,
            apprenant_id=student_id,
            montant=240,
            type_operation="CREDIT",
            origine="BONUS_FIDELITE",
            idempotency_key=f"welcome_bonus_{student_id}",
            description="Bonus initial de bienvenue AlterniA",
            solde_apres=240,
            metadonnees_json=json.dumps({"reason": "welcome_account_creation"}),
            date_creation=datetime.utcnow(),
        )
        db.add(init_tx)
        db.commit()
    return wallet


def credit_coins(
    db: Session,
    student_id: str,
    amount: int,
    origine: str,
    description: str,
    idempotency_key: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Tuple[Portefeuille, Optional[TransactionPiece]]:
    """
    Crédite le portefeuille d'un élève de manière atomique et traçable.
    Si une idempotency_key existe déjà, l'opération est ignorée sans doublon.
    """
    if amount <= 0:
        raise ValueError("Le montant à créditer doit être strictement positif.")

    # 1. Vérification d'idempotence
    if idempotency_key:
        existing_tx = db.query(TransactionPiece).filter(
            TransactionPiece.idempotency_key == idempotency_key
        ).first()
        if existing_tx:
            logger.info(f"Transaction idempotente déjà traitée : {idempotency_key}")
            wallet = get_or_create_wallet(db, student_id)
            return wallet, existing_tx

    wallet = get_or_create_wallet(db, student_id)
    wallet.solde_pieces += amount
    wallet.argent_total_gagne_fcfa += (amount * TAUX_CONVERSION_PIECE_FCFA)
    wallet.date_mise_a_jour = datetime.utcnow()

    tx = TransactionPiece(
        id=generate_uuid(),
        portefeuille_id=wallet.id,
        apprenant_id=student_id,
        montant=amount,
        type_operation="CREDIT",
        origine=origine,
        idempotency_key=idempotency_key,
        description=description,
        solde_apres=wallet.solde_pieces,
        metadonnees_json=json.dumps(metadata or {}),
        date_creation=datetime.utcnow(),
    )
    db.add(tx)
    db.commit()
    db.refresh(wallet)
    db.refresh(tx)
    return wallet, tx


def reserve_coins_for_withdrawal(
    db: Session,
    student_id: str,
    amount: int,
    description: str,
    idempotency_key: Optional[str] = None,
) -> Tuple[Portefeuille, TransactionPiece]:
    """
    Réserve des pièces pour une demande de retrait Mobile Money en cours de vérification.
    Déduit immédiatement du solde disponible et ajoute au solde réservé.
    """
    if amount <= 0:
        raise ValueError("Le montant à réserver doit être strictement positif.")

    wallet = get_or_create_wallet(db, student_id)
    if wallet.solde_pieces < amount:
        raise ValueError(
            f"Solde insuffisant : {wallet.solde_pieces} pièces disponibles, {amount} demandées."
        )

    wallet.solde_pieces -= amount
    wallet.pieces_reservees += amount
    wallet.date_mise_a_jour = datetime.utcnow()

    tx = TransactionPiece(
        id=generate_uuid(),
        portefeuille_id=wallet.id,
        apprenant_id=student_id,
        montant=-amount,
        type_operation="DEBIT_RESERVATION",
        origine="RETRAIT_MOBILE_MONEY",
        idempotency_key=idempotency_key,
        description=description,
        solde_apres=wallet.solde_pieces,
        metadonnees_json=json.dumps({"reserved": True, "amount_fcfa": amount * TAUX_CONVERSION_PIECE_FCFA}),
        date_creation=datetime.utcnow(),
    )
    db.add(tx)
    db.commit()
    db.refresh(wallet)
    db.refresh(tx)
    return wallet, tx


def confirm_withdrawal_debit(
    db: Session,
    student_id: str,
    amount: int,
    description: str,
) -> Tuple[Portefeuille, TransactionPiece]:
    """
    Confirme le paiement réel Mobile Money :
    Libère la réservation et incrémente le total des pièces retirées.
    """
    wallet = get_or_create_wallet(db, student_id)
    wallet.pieces_reservees = max(0, wallet.pieces_reservees - amount)
    wallet.pieces_retirees_total += amount
    wallet.date_mise_a_jour = datetime.utcnow()

    tx = TransactionPiece(
        id=generate_uuid(),
        portefeuille_id=wallet.id,
        apprenant_id=student_id,
        montant=-amount,
        type_operation="DEBIT_FINAL",
        origine="RETRAIT_MOBILE_MONEY",
        description=description,
        solde_apres=wallet.solde_pieces,
        metadonnees_json=json.dumps({"paid": True, "amount_fcfa": amount * TAUX_CONVERSION_PIECE_FCFA}),
        date_creation=datetime.utcnow(),
    )
    db.add(tx)
    db.commit()
    db.refresh(wallet)
    db.refresh(tx)
    return wallet, tx


def refund_reserved_coins(
    db: Session,
    student_id: str,
    amount: int,
    description: str,
) -> Tuple[Portefeuille, TransactionPiece]:
    """
    Rembourse les pièces réservées en cas de rejet ou d'échec avéré du retrait Mobile Money.
    """
    wallet = get_or_create_wallet(db, student_id)
    wallet.pieces_reservees = max(0, wallet.pieces_reservees - amount)
    wallet.solde_pieces += amount
    wallet.date_mise_a_jour = datetime.utcnow()

    tx = TransactionPiece(
        id=generate_uuid(),
        portefeuille_id=wallet.id,
        apprenant_id=student_id,
        montant=amount,
        type_operation="REMBOURSEMENT",
        origine="RETRAIT_MOBILE_MONEY",
        description=description,
        solde_apres=wallet.solde_pieces,
        metadonnees_json=json.dumps({"refunded": True}),
        date_creation=datetime.utcnow(),
    )
    db.add(tx)
    db.commit()
    db.refresh(wallet)
    db.refresh(tx)
    return wallet, tx


def get_wallet_summary(db: Session, student_id: str) -> Dict[str, Any]:
    """Retourne la synthèse complète du portefeuille pour l'application mobile et l'admin."""
    wallet = get_or_create_wallet(db, student_id)
    solde_dispo = wallet.solde_pieces
    valeur_fcfa = solde_dispo * TAUX_CONVERSION_PIECE_FCFA
    reserve_fcfa = wallet.pieces_reservees * TAUX_CONVERSION_PIECE_FCFA

    return {
        "solde_pieces": solde_dispo,
        "solde_pieces_label": f"{solde_dispo:,}".replace(",", " "),
        "valeur_fcfa": valeur_fcfa,
        "valeur_fcfa_label": f"{valeur_fcfa:,} FCFA".replace(",", " "),
        "pieces_reservees": wallet.pieces_reservees,
        "valeur_reservee_fcfa": reserve_fcfa,
        "pieces_retirees_total": wallet.pieces_retirees_total,
        "argent_total_gagne_fcfa": wallet.argent_total_gagne_fcfa,
        "taux_conversion": TAUX_CONVERSION_PIECE_FCFA,
        "seuil_minimal_retrait": SEUIL_MINIMAL_RETRAIT_PIECES,
        "plafond_maximal_retrait": PLAFOND_MAXIMAL_RETRAIT_PIECES,
        "retrait_possible": solde_dispo >= SEUIL_MINIMAL_RETRAIT_PIECES,
    }


def list_transactions(db: Session, student_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Historique paginé des transactions avec typage clair."""
    txs = (
        db.query(TransactionPiece)
        .filter(TransactionPiece.apprenant_id == student_id)
        .order_by(TransactionPiece.date_creation.desc())  # type: ignore
        .limit(limit)
        .all()
    )
    return [
        {
            "id": t.id,
            "montant": t.montant,
            "montant_label": f"{'+' if t.montant > 0 else ''}{t.montant} pièces",
            "valeur_fcfa": abs(t.montant) * TAUX_CONVERSION_PIECE_FCFA,
            "type_operation": t.type_operation,
            "origine": t.origine,
            "description": t.description,
            "solde_apres": t.solde_apres,
            "date": t.date_creation.isoformat() if t.date_creation else None,
        }
        for t in txs
    ]
