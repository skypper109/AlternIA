"""
Service central de gestion des Abonnements Scolaires et Droits d'accès Premium (Module H).
Le backend est la seule et unique source de vérité des droits d'accès.
"""

from datetime import datetime, timedelta
import json
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.src.db.models import (
    AbonnementUtilisateur,
    JournalAuditSecurite,
    OffreAbonnement,
    generate_uuid,
)
from backend.src.services.wallet_service import credit_coins

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


def init_offres_catalogue_si_besoin(db: Session):
    """Vérifie et insère les offres officielles dans la base de données."""
    for off in OFFRES_CATALOGUE_DEFAUT:
        existant = db.query(OffreAbonnement).filter(OffreAbonnement.id == off["id"]).first()
        if not existant:
            nouveau = OffreAbonnement(
                id=off["id"],
                titre=off["titre"],
                description=off["description"],
                prix_fcfa=off["prix_fcfa"],
                duree_jours=off["duree_jours"],
                avantages_json=json.dumps(off["avantages"]),
                actif=True,
            )
            db.add(nouveau)
    db.commit()


def get_offres_disponibles(db: Session) -> List[Dict[str, Any]]:
    """Retourne la liste des offres d'abonnement actives."""
    init_offres_catalogue_si_besoin(db)
    offres = db.query(OffreAbonnement).filter(OffreAbonnement.actif == True).all()
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
    now = datetime.utcnow()
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

    jours_restants = max(0, (abo.date_expiration - now).days)
    return {
        "est_premium": True,
        "statut": "ACTIF",
        "id_abonnement": abo.id,
        "offre_id": abo.offre_id,
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

    now = datetime.utcnow()
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
        date_debut = abo_actif.date_debut
        date_expiration = abo_actif.date_expiration + timedelta(days=offre.duree_jours)
        abo_actif.date_expiration = date_expiration
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
            "source": source,
            "date_expiration": date_expiration.isoformat(),
        }),
        date_action=now,
    ))

    db.commit()
    db.refresh(cible_abo)

    return {
        "succes": True,
        "message": f"Abonnement '{offre.titre}' activé avec succès jusqu'au {date_expiration.strftime('%d/%m/%Y')}.",
        "date_expiration": date_expiration.isoformat(),
        "jours_actifs": offre.duree_jours,
    }
