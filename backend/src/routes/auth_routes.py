"""
Routes API pour l'authentification et la gestion des utilisateurs.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.src.db.database import get_db
from backend.src.models.auth import (
    ConnexionRequest,
    CreerUtilisateurRequest,
    InscriptionEtablissementRequest,
    InscriptionParentRequest,
    ModifierProfilRequest,
    ModifierUtilisateurRequest,
)
from backend.src.services.auth_service import (
    authenticate_user,
    create_user,
    get_current_user_info,
    list_users,
    register_parent,
    register_school,
    toggle_user_status,
    update_profile,
    update_user_by_admin,
)

router = APIRouter(prefix="/api/auth", tags=["Authentification & Profils"])


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


@router.put("/profile")
def api_update_profile(req: ModifierProfilRequest, db: Session = Depends(get_db)):
    """Met à jour les informations et/ou mot de passe de l'utilisateur connecté."""
    return update_profile(db, req)


@router.get("/users")
def api_list_users(db: Session = Depends(get_db)):
    """Liste tous les utilisateurs enregistrés."""
    return list_users(db)


@router.post("/users")
def api_create_user(req: CreerUtilisateurRequest, db: Session = Depends(get_db)):
    """Crée un nouvel utilisateur depuis l'interface d'administration."""
    return create_user(db, req)


@router.put("/users/{user_id}")
def api_update_user(user_id: str, req: ModifierUtilisateurRequest, db: Session = Depends(get_db)):
    """Modifie un utilisateur par ID."""
    return update_user_by_admin(db, user_id, req)


@router.post("/users/{user_id}/toggle-status")
def api_toggle_user_status(user_id: str, db: Session = Depends(get_db)):
    """Active ou désactive un compte utilisateur."""
    return toggle_user_status(db, user_id)
