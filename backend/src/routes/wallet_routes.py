"""
Routes API pour la gestion du Portefeuille et des Pièces AlterniA (Module F).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional

from backend.src.db.database import get_db
from backend.src.services.wallet_service import (
    credit_coins,
    get_wallet_summary,
    list_transactions,
)

router = APIRouter(prefix="/api/wallet", tags=["Portefeuille & Pièces AlterniA"])


class CreditRewardRequest(BaseModel):
    student_id: str
    amount: int = Field(gt=0, description="Montant de pièces à créditer")
    origine: str = Field(description="Origine de l'opération (BATTLE_DUEL, DEFI_NATIONAL, etc.)")
    description: str
    idempotency_key: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@router.get("/summary")
def get_summary(
    student_id: str = Query("eleve_defaut", description="Identifiant unique de l'élève"),
    db: Session = Depends(get_db),
):
    """Retourne le solde actuel de pièces, la valeur en FCFA, les pièces réservées et les plafonds."""
    return get_wallet_summary(db, student_id)


@router.get("/transactions")
def get_transactions_history(
    student_id: str = Query("eleve_defaut", description="Identifiant unique de l'élève"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Retourne l'historique détaillé et horodaté des transactions de pièces."""
    return list_transactions(db, student_id, limit=limit)


@router.post("/credit-reward")
def api_credit_reward(req: CreditRewardRequest, db: Session = Depends(get_db)):
    """Crédite le portefeuille d'un élève avec protection anti-doublon (idempotence)."""
    try:
        wallet, tx = credit_coins(
            db=db,
            student_id=req.student_id,
            amount=req.amount,
            origine=req.origine,
            description=req.description,
            idempotency_key=req.idempotency_key,
            metadata=req.metadata,
        )
        return {
            "succes": True,
            "solde_pieces": wallet.solde_pieces,
            "transaction_id": tx.id if tx else None,
            "montant_credite": req.amount,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
