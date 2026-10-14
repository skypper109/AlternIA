"""
Routes API pour la conversion de pièces et retraits Mobile Money (Module G).
Supporte Orange Money, Moov Money et Wave.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional

from backend.src.db.database import get_db
from backend.src.services.retrait_service import (
    OPERATEURS_AUTORISES,
    creer_demande_retrait,
    lister_demandes_apprenant,
)

router = APIRouter(prefix="/api/retraits", tags=["Retraits Mobile Money"])


class DemandeRetraitRequest(BaseModel):
    apprenant_id: str
    pieces: int = Field(ge=100, le=25000, description="Nombre de pièces à convertir (min 100)")
    operateur: str = Field(description="ORANGE_MONEY, MOOV_MONEY ou WAVE")
    numero_telephone: str = Field(description="Numéro malien à 8 chiffres")
    nom_titulaire: str = Field(min_length=3, description="Nom et prénom du titulaire du compte")


@router.get("/operateurs")
def get_operateurs():
    """Retourne la liste des opérateurs Mobile Money agréés au Mali."""
    return [
        {"code": code, "nom": nom}
        for code, nom in OPERATEURS_AUTORISES.items()
    ]


@router.post("/demande")
def api_creer_demande(
    req: DemandeRetraitRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Crée une demande de retrait en réservant immédiatement les pièces.
    Enregistre les détails du titulaire et prépare le paiement Mobile Money.
    """
    client_ip = request.client.host if request.client else None
    try:
        demande = creer_demande_retrait(
            db=db,
            apprenant_id=req.apprenant_id,
            pieces=req.pieces,
            operateur=req.operateur,
            numero_telephone=req.numero_telephone,
            nom_titulaire=req.nom_titulaire,
            ip_client=client_ip,
        )
        return {
            "succes": True,
            "message": f"Demande de retrait de {demande.montant_fcfa} FCFA enregistrée avec succès. Pièces réservées.",
            "reference": demande.numero_transaction_ref,
            "pieces_reservees": demande.pieces_debitees,
            "montant_fcfa": demande.montant_fcfa,
            "statut": demande.statut,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de traitement du retrait : {e}")


@router.get("/mes-demandes")
def get_mes_demandes(
    apprenant_id: str = Query(..., description="ID de l'élève"),
    db: Session = Depends(get_db),
):
    """Retourne l'historique complet des demandes de retrait avec leur statut de paiement."""
    return lister_demandes_apprenant(db, apprenant_id)
