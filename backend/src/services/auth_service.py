"""
Service d'authentification et gestion des comptes utilisateurs.
"""

from datetime import datetime, timedelta
import uuid
from typing import Any, Dict
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.src.db.models import Apprenant, Etablissement, Utilisateur
from backend.src.models.auth import (
    ConnexionRequest,
    InscriptionEtablissementRequest,
    InscriptionParentRequest,
)
from backend.src.services.security import hash_password, verify_password


def authenticate_user(db: Session, req: ConnexionRequest) -> Dict[str, Any]:
    """Authentifie un utilisateur (Directeur, Enseignant, Parent) ou auto-crée les démos."""
    user = db.query(Utilisateur).filter(Utilisateur.email == req.email.strip()).first()
    is_etab = any(domain in req.email.lower() for domain in ["@altern.ia", "@ecole", "@lycee", "@college", "@school"])
    role = "admin_ecole" if (is_etab and "parent" not in req.email.lower()) else "parent"

    if not user:
        nom = "Dr. Konaté Moussa" if role == "admin_ecole" else "Aïssata Coulibaly"
        user = Utilisateur(
            email=req.email.strip(),
            role=role,
            nom_complet=nom,
            mot_de_passe_hash=hash_password(req.mot_de_passe or "alternia2026"),
            actif=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Vérification du mot de passe s'il est configuré et renseigné
        if user.mot_de_passe_hash and req.mot_de_passe:
            if not verify_password(req.mot_de_passe, user.mot_de_passe_hash):
                # Tolérance pour la démonstration si mot de passe par défaut
                if req.mot_de_passe not in {"password123", "alternia2026", "admin", "parent", "directeur"}:
                    raise HTTPException(status_code=401, detail="Mot de passe incorrect")
        elif not user.mot_de_passe_hash:
            user.mot_de_passe_hash = hash_password(req.mot_de_passe or "alternia2026")

    user.dernier_acces = datetime.utcnow()
    db.commit()

    token = f"alta-jwt-{uuid.uuid4()}"
    return {
        "succes": True,
        "token": token,
        "expiresAt": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        "utilisateur": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "nomComplet": user.nom_complet,
            "avatar": user.avatar,
            "dateCreation": user.date_creation.isoformat() if user.date_creation else None,
            "dernierAcces": user.dernier_acces.isoformat() if user.dernier_acces else None,
            "actif": user.actif,
        }
    }


def register_parent(db: Session, req: InscriptionParentRequest) -> Dict[str, Any]:
    """Inscrit un nouveau compte parent et son enfant avec mot de passe haché."""
    existant = db.query(Utilisateur).filter(Utilisateur.email == req.email.strip()).first()
    if existant:
        raise HTTPException(status_code=400, detail="Un compte existe déjà avec cette adresse email.")

    user = Utilisateur(
        email=req.email.strip(),
        nom_complet=req.nom_complet,
        role="parent",
        mot_de_passe_hash=hash_password(req.mot_de_passe or "alternia2026"),
        actif=True,
    )
    db.add(user)

    if req.nom_enfant:
        prenom_nom = req.nom_enfant.split(" ", 1)
        prenom = prenom_nom[0]
        nom = prenom_nom[1] if len(prenom_nom) > 1 else "Élève"
        apprenant = Apprenant(
            nom=nom,
            prenom=prenom,
            matricule=f"ML-{uuid.uuid4().hex[:6].upper()}",
            classe=req.classe_enfant or "11eme",
        )
        db.add(apprenant)

    db.commit()
    db.refresh(user)

    return {
        "succes": True,
        "message": "Compte parent créé avec succès",
        "utilisateur": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "nomComplet": user.nom_complet,
        }
    }


def register_school(db: Session, req: InscriptionEtablissementRequest) -> Dict[str, Any]:
    """Inscrit un nouvel établissement scolaire et son administrateur avec mot de passe haché."""
    etab = Etablissement(
        nom=req.nom_etablissement,
        code=req.code_etablissement,
        ville=req.ville or "Bamako",
        telephone=req.telephone,
        email=req.email,
    )
    db.add(etab)

    user = Utilisateur(
        email=req.email.strip(),
        nom_complet=req.nom_responsable,
        role="admin_ecole",
        mot_de_passe_hash=hash_password(req.mot_de_passe or "alternia2026"),
        actif=True,
    )
    db.add(user)
    db.commit()

    return {
        "succes": True,
        "message": "Établissement enregistré avec succès",
        "etablissement": {"id": etab.id, "nom": etab.nom, "code": etab.code},
        "utilisateur": {"id": user.id, "email": user.email, "role": user.role},
    }


def get_current_user_info(db: Session) -> Dict[str, Any]:
    """Retourne les informations du profil utilisateur courant."""
    user = db.query(Utilisateur).first()
    if not user:
        raise HTTPException(status_code=404, detail="Aucun utilisateur trouvé")
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "nomComplet": user.nom_complet,
        "avatar": user.avatar,
        "actif": user.actif,
    }
