"""
Routes API pour l'authentification et l'inscription.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.src.db.database import get_db
from backend.src.models.auth import (
    ConnexionRequest,
    InscriptionEtablissementRequest,
    InscriptionParentRequest,
)
from backend.src.services.auth_service import (
    authenticate_user,
    get_current_user_info,
    register_parent,
    register_school,
)

router = APIRouter(prefix="/api/auth", tags=["Authentification"])


@router.post("/connexion")
def api_connexion(req: ConnexionRequest, db: Session = Depends(get_db)):
    """Authentification utilisateur (Établissement ou Parent)."""
    return authenticate_user(db, req)


@router.post("/inscription-parent")
def api_inscription_parent(req: InscriptionParentRequest, db: Session = Depends(get_db)):
    """Inscription d'un compte parent."""
    return register_parent(db, req)


@router.post("/inscription-etablissement")
def api_inscription_etablissement(req: InscriptionEtablissementRequest, db: Session = Depends(get_db)):
    """Inscription d'un établissement scolaire."""
    return register_school(db, req)


@router.get("/me")
def api_auth_me(db: Session = Depends(get_db)):
    """Retourne l'utilisateur connecté courant."""
    return get_current_user_info(db)
