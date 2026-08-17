"""
Données initiales de démarrage pour alta_db (Établissements, Boîtiers, Apprenants, Avatars, Alertes).
"""

from datetime import datetime, timedelta
import json
from sqlalchemy.orm import Session
from backend.src.db.models import (
    Utilisateur,
    Etablissement,
    Boitier,
    Apprenant,
    SessionApprentissage,
    AvatarPedagogique,
    AlertePedagogique,
    StatistiquePedagogique,
)


def seed_initial_data(db: Session, force: bool = False):
    """Insère les données de base si la base est vide et garantit le hachage des mots de passe."""
    from backend.src.services.security import hash_password

    try:
        # Vérification si les données existent déjà
        existing_users = db.query(Utilisateur).all()
        if existing_users and not force:
            for u in existing_users:
                if not u.mot_de_passe_hash:
                    u.mot_de_passe_hash = hash_password("alternia2026")
            db.commit()
            return

        print("🌱 Peuplement initial de la base alta_db...")

        # 1. Établissement de référence
        etablissement = Etablissement(
            id="etab-lbad-bamako",
            nom="Lycée Ba Aminata Diallo (LBAD)",
            type_etablissement="Lycée d'Enseignement Général",
            code="ML-BKO-0042",
            adresse="Quartier du Fleuve, Commune III",
            ville="Bamako",
            pays="Mali",
            telephone="+223 20 22 45 10",
            email="direction@lbad.altern.ia",
        )
        db.add(etablissement)

        # 2. Utilisateurs de démonstration (@altern.ia) avec mot de passe haché
        from backend.src.services.security import hash_password

        admin_ecole = Utilisateur(
            id="usr-directeur",
            email="directeur@altern.ia",
            nom_complet="Dr. Konaté Moussa",
            role="admin_ecole",
            mot_de_passe_hash=hash_password("alternia2026"),
            actif=True,
        )
        parent_user = Utilisateur(
            id="usr-parent",
            email="parent@altern.ia",
            nom_complet="Aïssata Coulibaly",
            role="parent",
            mot_de_passe_hash=hash_password("alternia2026"),
            actif=True,
        )
        admin_sys = Utilisateur(
            id="usr-admin",
            email="admin@altern.ia",
            nom_complet="Administrateur AlternIA",
            role="admin_ecole",
            mot_de_passe_hash=hash_password("alternia2026"),
            actif=True,
        )
        db.add_all([admin_ecole, parent_user, admin_sys])

        # 3. Boîtiers physiques AlternIA Box
        boitier_principal = Boitier(
            id="box-alta-01",
            numero_serie="ALT-BOX-2026-001",
            modele="AlternIA Box v2.0 (Raspberry Pi 5)",
            firmware="v2.0-LocalEdge",
            statut="en_ligne",
            batterie=98,
            stockage_go=32.0,
            stockage_utilise_go=8.6,
            wifi_ssid="AlternIA-Box-WiFi",
            ip_locale="192.168.4.1",
            etablissement_id=etablissement.id,
            enfant_id="appr-amadou-diallo",
        )
        boitier_secondaire = Boitier(
            id="box-alta-02",
            numero_serie="ALT-BOX-2026-002",
            modele="AlternIA Box v2.0 (Raspberry Pi 4)",
            firmware="v2.0-LocalEdge",
            statut="en_ligne",
            batterie=85,
            stockage_go=32.0,
            stockage_utilise_go=7.8,
            wifi_ssid="AlternIA-Box-WiFi-2",
            ip_locale="192.168.4.2",
            etablissement_id=etablissement.id,
            enfant_id="appr-fatou-traore",
        )
        db.add_all([boitier_principal, boitier_secondaire])

        # 4. Apprenants (10e, 11e Sciences, 12e Terminale TSE)
        apprenant_1 = Apprenant(
            id="appr-amadou-diallo",
            nom="Diallo",
            prenom="Amadou",
            matricule="ML2026-11S-089",
            classe="11eme",
            serie="11S",
            niveau_maitrise=78.5,
            temps_total_sec=18400,
            questions_posees=64,
            etablissement_id=etablissement.id,
            boitier_id=boitier_principal.id,
        )
        apprenant_2 = Apprenant(
            id="appr-fatou-traore",
            nom="Traoré",
            prenom="Fatoumata",
            matricule="ML2026-TSE-014",
            classe="12eme",
            serie="TSE",
            niveau_maitrise=84.0,
            temps_total_sec=24500,
            questions_posees=92,
            etablissement_id=etablissement.id,
            boitier_id=boitier_secondaire.id,
        )
        apprenant_3 = Apprenant(
            id="appr-ousmane-coulibaly",
            nom="Coulibaly",
            prenom="Ousmane",
            matricule="ML2026-10E-102",
            classe="10eme",
            serie="Tronc Commun",
            niveau_maitrise=68.2,
            temps_total_sec=11200,
            questions_posees=38,
            etablissement_id=etablissement.id,
            boitier_id=boitier_principal.id,
        )
        db.add_all([apprenant_1, apprenant_2, apprenant_3])

        # 5. Avatars pédagogiques avec Vivienne
        avatar_vivienne = AvatarPedagogique(
            id="avatar-vivienne",
            nom="Professeure Vivienne",
            matiere="SVT & Sciences Naturelles",
            style_pedagogique="Chaleureuse, bienveillante et explicite avec exemples concrets",
            voix_tts="vivienne",
            photo_url="assets/avatars/vivienne.svg",
            actif=True,
            par_defaut=True,
        )
        avatar_amadou = AvatarPedagogique(
            id="avatar-amadou",
            nom="Dr. Koné Amadou",
            matiere="Mathématiques & Physique-Chimie",
            style_pedagogique="Méthodique, étape par étape avec rigueur scientifique",
            voix_tts="remy",
            photo_url="assets/avatars/amadou.svg",
            actif=True,
            par_defaut=False,
        )
        avatar_fatou = AvatarPedagogique(
            id="avatar-fatou",
            nom="Mme Samaké Fatou",
            matiere="Français & Philosophie",
            style_pedagogique="Littéraire, interactive avec vocabulaire riche",
            voix_tts="denise",
            photo_url="assets/avatars/fatou.svg",
            actif=True,
            par_defaut=False,
        )
        db.add_all([avatar_vivienne, avatar_amadou, avatar_fatou])

        # 6. Alertes pédagogiques
        alerte_1 = AlertePedagogique(
            id="alt-001",
            apprenant_id=apprenant_1.id,
            titre="Difficulté récurrente : Les Réactions Acide-Base",
            description="L'apprenant Amadou Diallo a sollicité 4 explications successives sur la notion de pH et couples acide-base.",
            type_alerte="difficulte_recurrente",
            gravite="moyenne",
            matiere="chimie",
            resolu=False,
        )
        alerte_2 = AlertePedagogique(
            id="alt-002",
            apprenant_id=apprenant_2.id,
            titre="Excellente progression en Nombres Complexes",
            description="Fatoumata a validé 95% des exercices de terminale TSE sur les transformations géométriques.",
            type_alerte="reussite_remarquable",
            gravite="faible",
            matiere="mathematiques",
            resolu=True,
        )
        db.add_all([alerte_1, alerte_2])

        # 7. Statistiques journalières pour les graphiques
        today = datetime.utcnow().strftime("%Y-%m-%d")
        stat_1 = StatistiquePedagogique(
            id="stat-11s",
            date_jour=today,
            classe="11eme",
            matiere="biologie",
            total_interactions=128,
            total_temps_sec=32400,
            taux_comprehension=79.4,
            notions_difficiles_json=json.dumps(["Zonation écologique", "Structure cellulaire végétale", "Photosynthèse"]),
        )
        stat_2 = StatistiquePedagogique(
            id="stat-tse",
            date_jour=today,
            classe="12eme",
            matiere="mathematiques",
            total_interactions=210,
            total_temps_sec=48600,
            taux_comprehension=82.1,
            notions_difficiles_json=json.dumps(["Intégration par parties", "Équations différentielles"]),
        )
        db.add_all([stat_1, stat_2])

        db.commit()
        print("✅ Base de données alta_db peuplée avec succès.")
    except Exception as exc:
        db.rollback()
        print(f"⚠️ Erreur lors du peuplement de alta_db : {exc}")
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Ajout automatique de la racine du projet au sys.path
    root_dir = Path(__file__).resolve().parents[3]
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))

    from backend.src.db.database import init_db, SessionLocal

    print("🚀 Initialisation et peuplement de la base alta_db...")
    init_db()
    session = SessionLocal()
    seed_initial_data(session)

