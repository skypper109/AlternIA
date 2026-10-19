"""
Service central de gestion des Abonnements Scolaires et Droits d'accès Premium (Module H).
Le backend est la seule et unique source de vérité des droits d'accès.
"""

from datetime import datetime, timedelta, timezone
import json
import logging
import math
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.src.db.models import (
    AbonnementUtilisateur,
    JournalAuditSecurite,
    OffreAbonnement,
    generate_uuid,
)
from backend.src.services.wallet_service import (
    get_or_create_wallet,
    credit_coins,
    TAUX_CONVERSION_PIECE_FCFA,
)

logger = logging.getLogger("AlternIA.AbonnementService")

OFFRES_CATALOGUE_DEFAUT = [
    {
        "id": "mensuel_standard",
        "titre": "Pass Mensuel Révision & Bac",
        "description": "Accès complet aux podcasts IA illimités, aux arènes de duel et aux annales du Bac.",
        "prix_fcfa": 2500,
        "duree_jours": 30,
        "avantages": [
            "Podcasts audio de cours illimités",
            "Duels scolaires et défis illimités",
            "Annales d'examens corrigées par l'IA",
            "Mode hors-ligne prioritaire",
        ],
    },
    {
        "id": "trimestriel_trimestre",
        "titre": "Pack Trimestre d'Excellence",
        "description": "Couvre l'intégralité d'un trimestre scolaire avec tutorat vocal personnalisé.",
        "prix_fcfa": 6500,
        "duree_jours": 90,
        "avantages": [
            "Tous les avantages du Pass Mensuel",
            "Économie de 1 000 FCFA",
            "Rapports de progression hebdomadaires pour les parents",
            "Accès anticipé aux nouveaux modules culturels",
        ],
    },
    {
        "id": "annuel_examen",
        "titre": "Abonnement Annuel DEF & Baccalauréat",
        "description": "Préparation intensive pour décrocher la mention aux examens nationaux.",
        "prix_fcfa": 20000,
        "duree_jours": 365,
        "avantages": [
            "Accès illimité toute l'année scolaire",
            "Simulateur complet d'épreuves d'examen d'État",
            "Tutorat vocal Vivienne illimité 24h/24",
            "Support d'assistance pédagogique prioritaire",
        ],
    },
]


def _utc_now() -> datetime:
    """Retourne la date/heure UTC naive compatible avec SQLite et les modèles existants."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def init_offres_catalogue_si_besoin(db: Session):
    """Vérifie et insère les offres officielles dans la base de données."""
    try:
        for off in OFFRES_CATALOGUE_DEFAUT:
            existant = db.query(OffreAbonnement).filter(OffreAbonnement.id == off["id"]).first()
            if not existant:
                nouveau = OffreAbonnement(
                    id=off["id"],
                    titre=off["titre"],
                    description=off["description"],
                    prix_fcfa=off["prix_fcfa"],
                    duree_jours=off["duree_jours"],
                    avantages_json=json.dumps(off["avantages"], ensure_ascii=False),
                    actif=True,
                )
                db.add(nouveau)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur lors de l'initialisation du catalogue d'offres : {e}")


def get_offres_disponibles(db: Session) -> List[Dict[str, Any]]:
    """Retourne la liste des offres d'abonnement actives."""
    init_offres_catalogue_si_besoin(db)
    offres = db.query(OffreAbonnement).filter(OffreAbonnement.actif.is_(True)).all()
    return [
        {
            "id": o.id,
            "titre": o.titre,
            "description": o.description,
            "prix_fcfa": o.prix_fcfa,
            "prix_fcfa_label": f"{o.prix_fcfa:,} FCFA".replace(",", " "),
            "duree_jours": o.duree_jours,
            "avantages": json.loads(o.avantages_json) if o.avantages_json else [],
        }
        for o in offres
    ]


def get_statut_abonnement_apprenant(db: Session, student_id: str) -> Dict[str, Any]:
    """
    Source de vérité pour vérifier les droits d'accès Premium de l'élève.
    L'interface ne doit jamais débloquer les fonctions sans cette validation backend.
    """
    now = _utc_now()

    # Clôturer automatiquement les abonnements expirés
    try:
        expirés = (
            db.query(AbonnementUtilisateur)
            .filter(
                AbonnementUtilisateur.apprenant_id == student_id,
                AbonnementUtilisateur.statut == "ACTIF",
                AbonnementUtilisateur.date_expiration <= now,
            )
            .all()
        )
        if expirés:
            for exp in expirés:
                exp.statut = "EXPIRE"
            db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"Erreur lors de la mise à jour des abonnements expirés : {e}")

    abo = (
        db.query(AbonnementUtilisateur)
        .filter(
            AbonnementUtilisateur.apprenant_id == student_id,
            AbonnementUtilisateur.statut == "ACTIF",
            AbonnementUtilisateur.date_expiration > now,
        )
        .order_by(AbonnementUtilisateur.date_expiration.desc())  # type: ignore
        .first()
    )

    if not abo or not abo.date_expiration:
        return {
            "est_premium": False,
            "statut": "STANDARD",
            "message": "Compte standard (quota gratuit)",
            "offre_titre": "Formule Gratuite",
            "date_expiration": None,
            "jours_restants": 0,
        }

    delta = abo.date_expiration - now
    jours_restants = max(1, math.ceil(delta.total_seconds() / 86400)) if delta.total_seconds() > 0 else 0

    offre = db.query(OffreAbonnement).filter(OffreAbonnement.id == abo.offre_id).first()
    offre_titre = offre.titre if offre else "Pass Scolaire AlterniA"

    return {
        "est_premium": True,
        "statut": "ACTIF",
        "id_abonnement": abo.id,
        "offre_id": abo.offre_id,
        "offre_titre": offre_titre,
        "source": abo.source,
        "date_debut": abo.date_debut.isoformat() if abo.date_debut else None,
        "date_expiration": abo.date_expiration.isoformat(),
        "jours_restants": jours_restants,
        "message": f"Abonnement actif — {jours_restants} jours restants",
    }


def souscrire_abonnement(
    db: Session,
    student_id: str,
    offre_id: str,
    moyen_paiement: str = "MOBILE_MONEY",
    source: str = "ACHAT_MOBILE_MONEY",
) -> Dict[str, Any]:
    """Active un abonnement scolaire suite à un paiement ou une offre."""
    init_offres_catalogue_si_besoin(db)
    offre = db.query(OffreAbonnement).filter(OffreAbonnement.id == offre_id).first()
    if not offre:
        raise ValueError(f"L'offre '{offre_id}' n'existe pas.")

    now = _utc_now()

    # Si paiement en pièces virtuelles AlterniA, vérifier et débiter le portefeuille
    if moyen_paiement == "PIECES":
        wallet = get_or_create_wallet(db, student_id)
        pieces_requises = offre.prix_fcfa // TAUX_CONVERSION_PIECE_FCFA
        if wallet.solde_pieces < pieces_requises:
            raise ValueError(
                f"Solde insuffisant : {wallet.solde_pieces} pièces disponibles contre {pieces_requises} pièces requises."
            )
        wallet.solde_pieces -= pieces_requises
        wallet.date_mise_a_jour = now
        source = "ACHAT_PIECES_ALTERNIA"

    abo_actif = (
        db.query(AbonnementUtilisateur)
        .filter(
            AbonnementUtilisateur.apprenant_id == student_id,
            AbonnementUtilisateur.statut == "ACTIF",
            AbonnementUtilisateur.date_expiration > now,
        )
        .first()
    )

    if abo_actif and abo_actif.date_expiration:
        date_debut = abo_actif.date_debut or now
        base_expiration = abo_actif.date_expiration or now
        date_expiration = base_expiration + timedelta(days=offre.duree_jours)
        abo_actif.date_expiration = date_expiration
        abo_actif.offre_id = offre.id
        abo_actif.source = source
        abo_actif.statut = "ACTIF"
        cible_abo = abo_actif
    else:
        date_debut = now
        date_expiration = now + timedelta(days=offre.duree_jours)
        cible_abo = AbonnementUtilisateur(
            id=generate_uuid(),
            apprenant_id=student_id,
            offre_id=offre.id,
            source=source,
            statut="ACTIF",
            date_debut=date_debut,
            date_expiration=date_expiration,
            date_creation=now,
        )
        db.add(cible_abo)

    db.add(JournalAuditSecurite(
        id=generate_uuid(),
        admin_id_ou_systeme="SYSTEME_PAIEMENT",
        action_type="SOUSCRIPTION_ABONNEMENT",
        entite_cible="AbonnementUtilisateur",
        entite_id=cible_abo.id,
        details_json=json.dumps({
            "student_id": student_id,
            "offre_id": offre.id,
            "prix_fcfa": offre.prix_fcfa,
            "moyen_paiement": moyen_paiement,
            "source": source,
            "date_expiration": date_expiration.isoformat(),
        }, ensure_ascii=False),
        date_action=now,
    ))

    # Bonus de fidélité en pièces offert à chaque réabonnement / abonnement
    bonus_pieces = 100 if offre.duree_jours >= 90 else 50
    try:
        credit_coins(
            db=db,
            student_id=student_id,
            amount=bonus_pieces,
            origine="BONUS_FIDELITE",
            description=f"Bonus pièces souscription à '{offre.titre}'",
            idempotency_key=f"bonus_abo_{cible_abo.id}_{offre.id}",
            metadata={"offre_id": offre.id, "duree_jours": offre.duree_jours},
        )
    except Exception as e:
        logger.warning(f"Note bonus souscription : {e}")

    try:
        db.commit()
        db.refresh(cible_abo)
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur commit souscription : {e}")
        raise

    return {
        "succes": True,
        "message": f"Abonnement '{offre.titre}' activé avec succès jusqu'au {date_expiration.strftime('%d/%m/%Y')}.",
        "date_expiration": date_expiration.isoformat(),
        "jours_actifs": offre.duree_jours,
        "offre_titre": offre.titre,
    }

