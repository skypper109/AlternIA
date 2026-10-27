"""
Service de gestion du Parrainage Éducatif AlterniA (Module A).
Génère les codes uniques, lie les parrains et nouveaux élèves,
valide l'éligibilité avec détection anti-fraude,
crédite les récompenses de pièces côté serveur,
et active automatiquement l'abonnement Premium dès le seuil de 5 filleuls atteint.
"""

from datetime import datetime, timedelta, timezone
import json
import logging
import random
import string
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.src.db.models import (
    AbonnementUtilisateur,
    JournalAuditSecurite,
    ParrainageCode,
    ParrainageFilleul,
    generate_uuid,
)
from backend.src.services.wallet_service import credit_coins

logger = logging.getLogger("AlternIA.ParrainageService")

def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

SEUIL_FILLEULS_POUR_PREMIUM = 5
RECOMPENSE_PARRAIN_PIECES = 50
RECOMPENSE_FILLEUL_PIECES = 25
DUREE_PREMIUM_JOURS = 30


def _generer_code_parrainage(nom: str = "ALT") -> str:
    """Génère un code de parrainage mémorisable et unique (ex: DIA-482)."""
    clean_prefix = "".join(c for c in nom.upper() if c.isalnum())[:3]
    if len(clean_prefix) < 3:
        clean_prefix = "ALT"
    digits = "".join(random.choices(string.digits, k=3))
    return f"{clean_prefix}-{digits}"


def get_or_create_referral_code(db: Session, student_id: str, student_name: str = "Élève") -> ParrainageCode:
    """Récupère ou crée le code unique de parrainage pour un élève."""
    existing = db.query(ParrainageCode).filter(ParrainageCode.apprenant_id == student_id).first()
    if existing:
        return existing

    # Garantir l'unicité du code
    for _ in range(10):
        code_candidat = _generer_code_parrainage(student_name)
        if not db.query(ParrainageCode).filter(ParrainageCode.code == code_candidat).first():
            break
    else:
        code_candidat = f"ALT-{random.randint(1000, 9999)}"

    nouveau = ParrainageCode(
        id=generate_uuid(),
        apprenant_id=student_id,
        code=code_candidat,
        total_filleuls=0,
        total_filleuls_actifs=0,
        pieces_gagnees_parrainage=0,
        date_creation=_utc_now(),
    )
    db.add(nouveau)
    db.commit()
    db.refresh(nouveau)
    return nouveau


def associer_et_valider_parrainage(
    db: Session,
    filleul_id: str,
    code_parrainage: str,
    ip_client: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Associe un nouvel utilisateur avec un parrain via son code,
    valide l'éligibilité et déclenche les récompenses serveur.
    """
    code_propre = code_parrainage.strip().upper()
    parrain_code = db.query(ParrainageCode).filter(ParrainageCode.code == code_propre).first()

    if not parrain_code:
        raise ValueError(f"Le code de parrainage '{code_propre}' n'existe pas.")

    if parrain_code.apprenant_id == filleul_id:
        raise ValueError("Un utilisateur ne peut pas se parrainer lui-même.")

    # Vérifier si ce filleul a déjà été parrainé
    deja_parraine = db.query(ParrainageFilleul).filter(ParrainageFilleul.filleul_id == filleul_id).first()
    if deja_parraine:
        raise ValueError("Ce compte a déjà utilisé un code de parrainage.")

    # 1. Enregistrer la relation
    relation = ParrainageFilleul(
        id=generate_uuid(),
        parrain_id=parrain_code.apprenant_id,
        filleul_id=filleul_id,
        code_utilise=code_propre,
        statut="VALIDE",
        recompense_attribuee=True,
        date_inscription=_utc_now(),
        date_validation=_utc_now(),
    )
    db.add(relation)

    # 2. Mettre à jour les stats du parrain
    parrain_code.total_filleuls += 1
    parrain_code.total_filleuls_actifs += 1
    parrain_code.pieces_gagnees_parrainage += RECOMPENSE_PARRAIN_PIECES

    # 3. Créditer les pièces au Parrain (50 pièces)
    credit_coins(
        db=db,
        student_id=parrain_code.apprenant_id,
        amount=RECOMPENSE_PARRAIN_PIECES,
        origine="PARRAINAGE",
        description=f"Bonus parrainage : inscription validée de votre filleul",
        idempotency_key=f"parrain_bonus_{relation.id}",
    )

    # 4. Créditer les pièces au Filleul (25 pièces)
    credit_coins(
        db=db,
        student_id=filleul_id,
        amount=RECOMPENSE_FILLEUL_PIECES,
        origine="PARRAINAGE",
        description=f"Cadeau de bienvenue grâce au code parrainage {code_propre}",
        idempotency_key=f"filleul_bonus_{relation.id}",
    )

    # 5. Vérifier si le seuil pour débloquer l'abonnement Premium est atteint
    premium_debloque = False
    if parrain_code.total_filleuls_actifs >= SEUIL_FILLEULS_POUR_PREMIUM:
        # Vérifier si un abonnement actif existe déjà
        now = _utc_now()
        abo_actif = (
            db.query(AbonnementUtilisateur)
            .filter(
                AbonnementUtilisateur.apprenant_id == parrain_code.apprenant_id,
                AbonnementUtilisateur.statut == "ACTIF",
                AbonnementUtilisateur.date_expiration > now,
            )
            .first()
        )

        if abo_actif and abo_actif.date_expiration:
            # Prolonger l'abonnement
            abo_actif.date_expiration = abo_actif.date_expiration + timedelta(days=DUREE_PREMIUM_JOURS)
            premium_debloque = True
        else:
            nouvel_abo = AbonnementUtilisateur(
                id=generate_uuid(),
                apprenant_id=parrain_code.apprenant_id,
                offre_id="mensuel_standard",
                source="PARRAINAGE_OFFERT",
                statut="ACTIF",
                date_debut=now,
                date_expiration=now + timedelta(days=DUREE_PREMIUM_JOURS),
                date_creation=now,
            )
            db.add(nouvel_abo)
            premium_debloque = True

    # 6. Journal d'audit
    db.add(JournalAuditSecurite(
        id=generate_uuid(),
        admin_id_ou_systeme="SYSTEME_PARRAINAGE",
        action_type="PARRAINAGE_VALIDE",
        entite_cible="ParrainageFilleul",
        entite_id=relation.id,
        details_json=json.dumps({
            "parrain_id": parrain_code.apprenant_id,
            "filleul_id": filleul_id,
            "code": code_propre,
            "premium_debloque": premium_debloque,
        }),
        adresse_ip=ip_client,
        date_action=_utc_now(),
    ))

    db.commit()
    db.refresh(parrain_code)

    return {
        "succes": True,
        "message": f"Parrainage validé ! Vous avez reçu {RECOMPENSE_FILLEUL_PIECES} pièces de bienvenue.",
        "parrain_id": parrain_code.apprenant_id,
        "pieces_filleul": RECOMPENSE_FILLEUL_PIECES,
        "pieces_parrain": RECOMPENSE_PARRAIN_PIECES,
        "premium_debloque": premium_debloque,
    }


def get_referral_summary(db: Session, student_id: str, student_name: str = "Élève") -> Dict[str, Any]:
    """Synthèse pour le tableau de bord de parrainage de l'élève."""
    code_obj = get_or_create_referral_code(db, student_id, student_name)
    filleuls = (
        db.query(ParrainageFilleul)
        .filter(ParrainageFilleul.parrain_id == student_id)
        .order_by(ParrainageFilleul.date_inscription.desc())  # type: ignore
        .all()
    )

    progression_seuil = min(1.0, code_obj.total_filleuls_actifs / SEUIL_FILLEULS_POUR_PREMIUM)

    return {
        "code": code_obj.code,
        "lien_partage": f"https://alterniamali.com/rejoindre?ref={code_obj.code}",
        "total_filleuls": code_obj.total_filleuls,
        "filleuls_actifs": code_obj.total_filleuls_actifs,
        "pieces_gagnees": code_obj.pieces_gagnees_parrainage,
        "seuil_requis_premium": SEUIL_FILLEULS_POUR_PREMIUM,
        "progression_ratio": progression_seuil,
        "reste_pour_premium": max(0, SEUIL_FILLEULS_POUR_PREMIUM - code_obj.total_filleuls_actifs),
        "recompense_par_filleul": RECOMPENSE_PARRAIN_PIECES,
        "historique_filleuls": [
            {
                "id": f.id,
                "statut": f.statut,
                "date": f.date_inscription.isoformat() if f.date_inscription else None,
            }
            for f in filleuls
        ],
    }
