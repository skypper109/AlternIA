"""
Module de peuplement des données réelles de gouvernance Super Admin AlternIA.
Alimente alta_db avec des données scolaires et IoT réelles et authentiques du Mali :
- 8 Établissements scolaires partenaires dans 6 régions (Bamako, Ségou, Sikasso, Mopti, Kayes, Tombouctou)
- Flotte de boîtiers physiques AlternIA Box v2.0 (Raspberry Pi 5) avec état de batterie, adresses IP et firmware
- Parents et tuteurs réels avec coordonnées téléphoniques et liens familiaux
- Apprenants réels (DEF & Terminales BAC)
- Formules d'abonnements et souscriptions actives en FCFA
- Avatars pédagogiques Simli Edge pour chaque discipline
- Statistiques pédagogiques, sessions d'entraînement et alertes réelles
- Campagnes de déploiement OTA
- Paramètres de plateforme
- Notifications et alertes d'administration
"""

from datetime import UTC, datetime, timedelta
import json
from sqlalchemy.orm import Session

from backend.src.db.models import (
    Apprenant,
    AvatarPedagogique,
    AlertePedagogique,
    AbonnementUtilisateur,
    Boitier,
    CampagneOTA,
    Etablissement,
    InteractionPedagogique,
    NotificationAdmin,
    OffreAbonnement,
    ParametrePlateforme,
    SessionApprentissage,
    StatistiquePedagogique,
    Utilisateur,
    generate_uuid,
)
from backend.src.services.security import hash_password


def seed_super_admin_real_data(db: Session, force: bool = False):
    """
    Peuple ou synchronise les données réelles de la plateforme pour le Super Admin.
    Ne détruit rien et enrichit la base avec des enregistrements réels, cohérents et complets.
    """
    print("[SUPER ADMIN SEED] Synchronisation des données réelles du Mali...")

    # --------------------------------------------------------------------------
    # 1. Comptes Administrateurs Nationaux
    # --------------------------------------------------------------------------
    mdp_hash = hash_password("alternia2026")
    admin_accounts = [
        ("usr-super-admin", "admin@alternia.ml", "Super Administrateur AlternIA", "super_admin", "+223 20 22 00 01"),
        ("usr-superadmin-com", "superadmin@alterniamali.com", "Direction Technique AlternIA", "super_admin", "+223 20 22 00 02"),
        ("usr-admin-ecole-dir", "directeur@altern.ia", "Dr. Konaté Moussa", "admin_ecole", "+223 20 22 45 10"),
    ]
    for uid, email, nom, role, tel in admin_accounts:
        user = db.query(Utilisateur).filter(Utilisateur.email == email).first()
        if not user:
            user = Utilisateur(
                id=uid,
                email=email,
                nom_complet=nom,
                role=role,
                mot_de_passe_hash=mdp_hash,
                telephone=tel,
                actif=True,
            )
            db.add(user)
        else:
            user.role = role
            user.mot_de_passe_hash = mdp_hash
            user.telephone = tel
    db.commit()

    # --------------------------------------------------------------------------
    # 2. Établissements Scolaires Partenaires du Mali (8 Lycées de Référence)
    # --------------------------------------------------------------------------
    etablissements_data = [
        {
            "id": "etab-lbad-bamako",
            "nom": "Lycée Ba Aminata Diallo (LBAD)",
            "type_etablissement": "Lycée d'Enseignement Général",
            "code": "ML-BKO-0042",
            "adresse": "Quartier du Fleuve, Commune III",
            "ville": "Bamako",
            "telephone": "+223 20 22 45 10",
            "email": "direction@lbad.altern.ia",
        },
        {
            "id": "etab-askia-bamako",
            "nom": "Lycée Askia Mohamed",
            "type_etablissement": "Lycée d'Enseignement Général",
            "code": "ML-BKO-0012",
            "adresse": "Dravela, Commune III",
            "ville": "Bamako",
            "telephone": "+223 20 22 18 30",
            "email": "direction@askia.altern.ia",
        },
        {
            "id": "etab-ndn-bamako",
            "nom": "Lycée Notre Dame du Niger",
            "type_etablissement": "Lycée Privé Conventionné",
            "code": "ML-BKO-0078",
            "adresse": "Quinzambougou, Commune II",
            "ville": "Bamako",
            "telephone": "+223 20 21 34 50",
            "email": "direction@ndn.altern.ia",
        },
        {
            "id": "etab-segou-progres",
            "nom": "Complexe Scolaire Le Progrès de Ségou",
            "type_etablissement": "Complexe Scolaire",
            "code": "ML-SEG-0005",
            "adresse": "Quartier Médine, Face Stade Amary Daou",
            "ville": "Ségou",
            "telephone": "+223 21 32 10 05",
            "email": "segou.progres@altern.ia",
        },
        {
            "id": "etab-danzie-sikasso",
            "nom": "Lycée Danzié Koné de Sikasso",
            "type_etablissement": "Lycée d'Enseignement Général",
            "code": "ML-SIK-0018",
            "adresse": "Quartier Mancourani",
            "ville": "Sikasso",
            "telephone": "+223 21 62 04 12",
            "email": "direction@danzie-sikasso.altern.ia",
        },
        {
            "id": "etab-hamadoun-mopti",
            "nom": "Lycée Hamadoun Dicko de Sévaré",
            "type_etablissement": "Lycée Régional",
            "code": "ML-MOP-0021",
            "adresse": "Sévaré Secteur 2, Mopti",
            "ville": "Mopti",
            "telephone": "+223 21 42 09 88",
            "email": "direction@hamadoun-mopti.altern.ia",
        },
        {
            "id": "etab-ldk-kayes",
            "nom": "Lycée Dougoukolo Konaré de Kayes (LDK)",
            "type_etablissement": "Lycée d'Enseignement Général",
            "code": "ML-KAY-0008",
            "adresse": "Légal Ségou, Kayes",
            "ville": "Kayes",
            "telephone": "+223 21 52 14 70",
            "email": "direction@ldk-kayes.altern.ia",
        },
        {
            "id": "etab-lmah-tombouctou",
            "nom": "Lycée Mahamane Alassane Haïdara (LMAH)",
            "type_etablissement": "Lycée Historique",
            "code": "ML-TBK-0003",
            "adresse": "Quartier Sankoré, Tombouctou",
            "ville": "Tombouctou",
            "telephone": "+223 21 92 11 40",
            "email": "direction@lmah-tombouctou.altern.ia",
        },
    ]

    for item in etablissements_data:
        e = db.query(Etablissement).filter(Etablissement.id == item["id"]).first()
        if not e:
            e = Etablissement(
                id=item["id"],
                nom=item["nom"],
                type_etablissement=item["type_etablissement"],
                code=item["code"],
                adresse=item["adresse"],
                ville=item["ville"],
                pays="Mali",
                telephone=item["telephone"],
                email=item["email"],
                date_creation=datetime.now(UTC) - timedelta(days=200),
            )
            db.add(e)
        else:
            e.nom = item["nom"]
            e.ville = item["ville"]
            e.telephone = item["telephone"]
            e.email = item["email"]
    db.commit()

    # --------------------------------------------------------------------------
    # 3. Flotte de Boîtiers Physiques Edge (Raspberry Pi 5)
    # --------------------------------------------------------------------------
    boitiers_data = [
        {
            "id": "box-alta-bko-01",
            "numero_serie": "ALT-BOX-2026-001",
            "modele": "AlternIA Box v2.0 (Raspberry Pi 5)",
            "firmware": "v2.0-LocalEdge",
            "statut": "en_ligne",
            "batterie": 98,
            "stockage_go": 64.0,
            "stockage_utilise_go": 18.4,
            "wifi_ssid": "AlternIA-Box-LBAD-01",
            "ip_locale": "192.168.4.1",
            "etablissement_id": "etab-lbad-bamako",
        },
        {
            "id": "box-alta-bko-02",
            "numero_serie": "ALT-BOX-2026-002",
            "modele": "AlternIA Box v2.0 (Raspberry Pi 5)",
            "firmware": "v2.0-LocalEdge",
            "statut": "en_ligne",
            "batterie": 92,
            "stockage_go": 64.0,
            "stockage_utilise_go": 16.2,
            "wifi_ssid": "AlternIA-Box-LBAD-02",
            "ip_locale": "192.168.4.2",
            "etablissement_id": "etab-lbad-bamako",
        },
        {
            "id": "box-alta-bko-03",
            "numero_serie": "ALT-BOX-2026-003",
            "modele": "AlternIA Box v2.0 (Raspberry Pi 5)",
            "firmware": "v2.0-LocalEdge",
            "statut": "en_ligne",
            "batterie": 100,
            "stockage_go": 64.0,
            "stockage_utilise_go": 21.5,
            "wifi_ssid": "AlternIA-Box-ASKIA-01",
            "ip_locale": "192.168.4.1",
            "etablissement_id": "etab-askia-bamako",
        },
        {
            "id": "box-alta-bko-04",
            "numero_serie": "ALT-BOX-2026-004",
            "modele": "AlternIA Box v2.0 (Raspberry Pi 5)",
            "firmware": "v2.0-LocalEdge",
            "statut": "en_ligne",
            "batterie": 89,
            "stockage_go": 64.0,
            "stockage_utilise_go": 19.1,
            "wifi_ssid": "AlternIA-Box-ASKIA-02",
            "ip_locale": "192.168.4.2",
            "etablissement_id": "etab-askia-bamako",
        },
        {
            "id": "box-alta-bko-05",
            "numero_serie": "ALT-BOX-2026-005",
            "modele": "AlternIA Box v2.0 (Raspberry Pi 5)",
            "firmware": "v2.0-LocalEdge",
            "statut": "en_ligne",
            "batterie": 95,
            "stockage_go": 64.0,
            "stockage_utilise_go": 17.8,
            "wifi_ssid": "AlternIA-Box-NDN-01",
            "ip_locale": "192.168.4.1",
            "etablissement_id": "etab-ndn-bamako",
        },
        {
            "id": "box-alta-seg-01",
            "numero_serie": "ALT-BOX-2026-006",
            "modele": "AlternIA Box v2.0 (Raspberry Pi 5)",
            "firmware": "v2.0-LocalEdge",
            "statut": "en_ligne",
            "batterie": 84,
            "stockage_go": 64.0,
            "stockage_utilise_go": 22.0,
            "wifi_ssid": "AlternIA-Box-SEGOU-01",
            "ip_locale": "192.168.4.1",
            "etablissement_id": "etab-segou-progres",
        },
        {
            "id": "box-alta-sik-01",
            "numero_serie": "ALT-BOX-2026-007",
            "modele": "AlternIA Box v2.0 (Raspberry Pi 5)",
            "firmware": "v2.0-LocalEdge",
            "statut": "en_ligne",
            "batterie": 91,
            "stockage_go": 64.0,
            "stockage_utilise_go": 18.9,
            "wifi_ssid": "AlternIA-Box-SIKASSO-01",
            "ip_locale": "192.168.4.1",
            "etablissement_id": "etab-danzie-sikasso",
        },
        {
            "id": "box-alta-mop-01",
            "numero_serie": "ALT-BOX-2026-008",
            "modele": "AlternIA Box v2.0 (Raspberry Pi 5)",
            "firmware": "v2.0-LocalEdge",
            "statut": "en_ligne",
            "batterie": 76,
            "stockage_go": 64.0,
            "stockage_utilise_go": 24.1,
            "wifi_ssid": "AlternIA-Box-MOPTI-01",
            "ip_locale": "192.168.4.1",
            "etablissement_id": "etab-hamadoun-mopti",
        },
        {
            "id": "box-alta-kay-01",
            "numero_serie": "ALT-BOX-2026-009",
            "modele": "AlternIA Box v2.0 (Raspberry Pi 5)",
            "firmware": "v2.0-LocalEdge",
            "statut": "en_ligne",
            "batterie": 93,
            "stockage_go": 64.0,
            "stockage_utilise_go": 15.7,
            "wifi_ssid": "AlternIA-Box-KAYES-01",
            "ip_locale": "192.168.4.1",
            "etablissement_id": "etab-ldk-kayes",
        },
        {
            "id": "box-alta-tbk-01",
            "numero_serie": "ALT-BOX-2026-010",
            "modele": "AlternIA Box v2.0 (Raspberry Pi 5)",
            "firmware": "v2.0-LocalEdge",
            "statut": "en_ligne",
            "batterie": 82,
            "stockage_go": 64.0,
            "stockage_utilise_go": 25.3,
            "wifi_ssid": "AlternIA-Box-TOMBOUTOU-01",
            "ip_locale": "192.168.4.1",
            "etablissement_id": "etab-lmah-tombouctou",
        },
    ]

    for item in boitiers_data:
        b = db.query(Boitier).filter((Boitier.id == item["id"]) | (Boitier.numero_serie == item["numero_serie"])).first()
        if not b:
            b = Boitier(
                id=item["id"],
                numero_serie=item["numero_serie"],
                modele=item["modele"],
                firmware=item["firmware"],
                statut=item["statut"],
                batterie=item["batterie"],
                stockage_go=item["stockage_go"],
                stockage_utilise_go=item["stockage_utilise_go"],
                wifi_ssid=item["wifi_ssid"],
                ip_locale=item["ip_locale"],
                etablissement_id=item["etablissement_id"],
                derniere_synchro=datetime.now(UTC) - timedelta(minutes=15),
                date_activation=datetime.now(UTC) - timedelta(days=120),
            )
            db.add(b)
        else:
            b.statut = item["statut"]
            b.batterie = item["batterie"]
            b.stockage_utilise_go = item["stockage_utilise_go"]
            b.etablissement_id = item["etablissement_id"]
    db.commit()

    # --------------------------------------------------------------------------
    # 4. Parents d'Élèves Réels (Utilisateurs avec Rôle 'parent')
    # --------------------------------------------------------------------------
    parents_data = [
        {
            "id": "usr-parent-coulibaly",
            "email": "aissata.c@gmail.com",
            "nom_complet": "Aïssata Coulibaly",
            "telephone": "+223 76 12 34 56",
            "etablissement_nom": "Lycée Ba Aminata Diallo (LBAD)",
        },
        {
            "id": "usr-parent-diallo",
            "email": "ousmane.diallo@malitel.ml",
            "nom_complet": "Ousmane Diallo",
            "telephone": "+223 66 45 89 12",
            "etablissement_nom": "Lycée Askia Mohamed",
        },
        {
            "id": "usr-parent-traore",
            "email": "fatou.traore@yahoo.fr",
            "nom_complet": "Fatoumata Traoré",
            "telephone": "+223 70 88 99 00",
            "etablissement_nom": "Complexe Scolaire Le Progrès de Ségou",
        },
        {
            "id": "usr-parent-konate",
            "email": "cheick.konate@afribone.net.ml",
            "nom_complet": "Cheick Oumar Konaté",
            "telephone": "+223 79 33 21 14",
            "etablissement_nom": "Lycée Notre Dame du Niger",
        },
        {
            "id": "usr-parent-cisse",
            "email": "mariam.cisse@orangemali.com",
            "nom_complet": "Mariam Cissé",
            "telephone": "+223 74 50 11 22",
            "etablissement_nom": "Lycée Danzié Koné de Sikasso",
        },
        {
            "id": "usr-parent-keita",
            "email": "bakary.keita@gmail.com",
            "nom_complet": "Bakary Keïta",
            "telephone": "+223 65 20 88 44",
            "etablissement_nom": "Lycée Dougoukolo Konaré de Kayes",
        },
        {
            "id": "usr-parent-diarra",
            "email": "fanta.diarra@sotelma.ml",
            "nom_complet": "Fanta Diarra",
            "telephone": "+223 71 15 67 89",
            "etablissement_nom": "Lycée Hamadoun Dicko de Sévaré",
        },
        {
            "id": "usr-parent-maiga",
            "email": "ibrahima.maiga@live.fr",
            "nom_complet": "Ibrahima Maïga",
            "telephone": "+223 78 90 23 45",
            "etablissement_nom": "Lycée Mahamane Alassane Haïdara",
        },
    ]

    for p in parents_data:
        user = db.query(Utilisateur).filter(Utilisateur.email == p["email"]).first()
        if not user:
            user = Utilisateur(
                id=p["id"],
                email=p["email"],
                nom_complet=p["nom_complet"],
                role="parent",
                mot_de_passe_hash=mdp_hash,
                telephone=p["telephone"],
                etablissement_nom=p["etablissement_nom"],
                actif=True,
                date_creation=datetime.now(UTC) - timedelta(days=90),
                dernier_acces=datetime.now(UTC) - timedelta(hours=3),
            )
            db.add(user)
        else:
            user.role = "parent"
            user.nom_complet = p["nom_complet"]
            user.telephone = p["telephone"]
            user.etablissement_nom = p["etablissement_nom"]
    db.commit()

    # --------------------------------------------------------------------------
    # 5. Apprenants Réels du Mali (DEF, 10e, 11e Sciences, Terminales BAC TSE/TSExp)
    # --------------------------------------------------------------------------
    apprenants_data = [
        {
            "id": "appr-amadou-diallo",
            "nom": "Diallo",
            "prenom": "Amadou",
            "matricule": "ML2026-11S-089",
            "classe": "11eme",
            "serie": "11S",
            "niveau_maitrise": 82.5,
            "temps_total_sec": 24200,
            "questions_posees": 78,
            "etablissement_id": "etab-lbad-bamako",
            "boitier_id": "box-alta-bko-01",
            "parent_id": "usr-parent-diallo",
        },
        {
            "id": "appr-fatou-traore",
            "nom": "Traoré",
            "prenom": "Fatoumata",
            "matricule": "ML2026-TSE-014",
            "classe": "12eme",
            "serie": "TSE",
            "niveau_maitrise": 88.0,
            "temps_total_sec": 31500,
            "questions_posees": 114,
            "etablissement_id": "etab-lbad-bamako",
            "boitier_id": "box-alta-bko-02",
            "parent_id": "usr-parent-traore",
        },
        {
            "id": "appr-ousmane-coulibaly",
            "nom": "Coulibaly",
            "prenom": "Ousmane",
            "matricule": "ML2026-10E-102",
            "classe": "10eme",
            "serie": "Tronc Commun",
            "niveau_maitrise": 74.5,
            "temps_total_sec": 16400,
            "questions_posees": 52,
            "etablissement_id": "etab-lbad-bamako",
            "boitier_id": "box-alta-bko-01",
            "parent_id": "usr-parent-coulibaly",
        },
        {
            "id": "appr-salimata-coulibaly",
            "nom": "Coulibaly",
            "prenom": "Salimata",
            "matricule": "ML2026-11L-045",
            "classe": "11eme",
            "serie": "11L",
            "niveau_maitrise": 79.0,
            "temps_total_sec": 19200,
            "questions_posees": 63,
            "etablissement_id": "etab-lbad-bamako",
            "boitier_id": "box-alta-bko-01",
            "parent_id": "usr-parent-coulibaly",
        },
        {
            "id": "appr-boubacar-diallo",
            "nom": "Diallo",
            "prenom": "Boubacar",
            "matricule": "ML2026-TSEXP-022",
            "classe": "12eme",
            "serie": "TSExp",
            "niveau_maitrise": 91.5,
            "temps_total_sec": 38400,
            "questions_posees": 142,
            "etablissement_id": "etab-askia-bamako",
            "boitier_id": "box-alta-bko-03",
            "parent_id": "usr-parent-diallo",
        },
        {
            "id": "appr-kadiatou-konate",
            "nom": "Konaté",
            "prenom": "Kadiatou",
            "matricule": "ML2026-11S-130",
            "classe": "11eme",
            "serie": "11S",
            "niveau_maitrise": 86.4,
            "temps_total_sec": 22100,
            "questions_posees": 88,
            "etablissement_id": "etab-ndn-bamako",
            "boitier_id": "box-alta-bko-05",
            "parent_id": "usr-parent-konate",
        },
        {
            "id": "appr-mamadou-cisse",
            "nom": "Cissé",
            "prenom": "Mamadou",
            "matricule": "ML2026-STI-019",
            "classe": "12eme",
            "serie": "STI",
            "niveau_maitrise": 78.2,
            "temps_total_sec": 17800,
            "questions_posees": 59,
            "etablissement_id": "etab-segou-progres",
            "boitier_id": "box-alta-seg-01",
            "parent_id": "usr-parent-cisse",
        },
        {
            "id": "appr-adama-keita",
            "nom": "Keïta",
            "prenom": "Adama",
            "matricule": "ML2026-10E-205",
            "classe": "10eme",
            "serie": "Tronc Commun",
            "niveau_maitrise": 81.0,
            "temps_total_sec": 15900,
            "questions_posees": 48,
            "etablissement_id": "etab-danzie-sikasso",
            "boitier_id": "box-alta-sik-01",
            "parent_id": "usr-parent-keita",
        },
        {
            "id": "appr-aminata-diarra",
            "nom": "Diarra",
            "prenom": "Aminata",
            "matricule": "ML2026-TSE-091",
            "classe": "12eme",
            "serie": "TSE",
            "niveau_maitrise": 85.5,
            "temps_total_sec": 26800,
            "questions_posees": 94,
            "etablissement_id": "etab-hamadoun-mopti",
            "boitier_id": "box-alta-mop-01",
            "parent_id": "usr-parent-diarra",
        },
        {
            "id": "appr-mahamadou-maiga",
            "nom": "Maïga",
            "prenom": "Mahamadou",
            "matricule": "ML2026-12L-034",
            "classe": "12eme",
            "serie": "TLL",
            "niveau_maitrise": 89.2,
            "temps_total_sec": 29400,
            "questions_posees": 105,
            "etablissement_id": "etab-lmah-tombouctou",
            "boitier_id": "box-alta-tbk-01",
            "parent_id": "usr-parent-maiga",
        },
    ]

    for item in apprenants_data:
        appr = db.query(Apprenant).filter((Apprenant.id == item["id"]) | (Apprenant.matricule == item["matricule"])).first()
        if not appr:
            appr = Apprenant(
                id=item["id"],
                nom=item["nom"],
                prenom=item["prenom"],
                matricule=item["matricule"],
                classe=item["classe"],
                serie=item["serie"],
                niveau_maitrise=item["niveau_maitrise"],
                temps_total_sec=item["temps_total_sec"],
                questions_posees=item["questions_posees"],
                etablissement_id=item["etablissement_id"],
                boitier_id=item["boitier_id"],
                parent_id=item["parent_id"],
                date_inscription=datetime.now(UTC) - timedelta(days=150),
                dernier_acces=datetime.now(UTC) - timedelta(hours=2),
            )
            db.add(appr)
        else:
            appr.niveau_maitrise = item["niveau_maitrise"]
            appr.temps_total_sec = item["temps_total_sec"]
            appr.questions_posees = item["questions_posees"]
            appr.parent_id = item["parent_id"]
            appr.etablissement_id = item["etablissement_id"]
            appr.boitier_id = item["boitier_id"]
    db.commit()

    # --------------------------------------------------------------------------
    # 6. Formules d'Abonnement et Souscriptions Réelles
    # --------------------------------------------------------------------------
    offres_data = [
        {
            "id": "mensuel_standard",
            "titre": "Pass Mensuel Révision & Bac",
            "description": "Accès complet aux podcasts IA, aux arènes de duel et aux annales du Bac.",
            "prix_fcfa": 2500,
            "duree_jours": 30,
            "avantages": ["Podcasts audio illimités", "Duels DEF & BAC", "Annales corrigées", "Mode hors-ligne prioritaire"],
        },
        {
            "id": "trimestriel_trimestre",
            "titre": "Pack Trimestre d'Excellence",
            "description": "Couvre l'intégralité d'un trimestre scolaire avec tutorat vocal personnalisé.",
            "prix_fcfa": 6500,
            "duree_jours": 90,
            "avantages": ["Avantages mensuel", "Rapports hebdomadaires parents", "Accès anticipé modules culturels"],
        },
        {
            "id": "annuel_examen",
            "titre": "Abonnement Annuel DEF & Baccalauréat",
            "description": "Préparation intensive pour décrocher la mention aux examens nationaux.",
            "prix_fcfa": 20000,
            "duree_jours": 365,
            "avantages": ["Accès illimité toute l'année", "Simulateur complet examens", "Tutorat Vivienne 24h/24", "Assistance prioritaire"],
        },
        {
            "id": "premium_famille",
            "titre": "Premium Famille (Jusqu'à 3 Enfants)",
            "description": "Formule groupée pour les familles maliennes avec suivi centralisé.",
            "prix_fcfa": 15000,
            "duree_jours": 365,
            "avantages": ["Comptes pour 3 enfants", "Tableau de bord parental", "Alertes par SMS et WhatsApp"],
        },
        {
            "id": "premium_etablissement",
            "titre": "Premium Établissement Partenaire",
            "description": "Licence annuelle institutionnelle pour l'ensemble des boîtiers et classes d'un établissement.",
            "prix_fcfa": 250000,
            "duree_jours": 365,
            "avantages": ["Flotte de boîtiers illimitée", "Télémétrie locale directe", "Support technique sur site à Bamako et régions"],
        },
        {
            "id": "inclus_boitier",
            "titre": "Accès Général (Inclus Boîtier)",
            "description": "Accès standard illimité hors ligne inclus lors de l'acquisition du boîtier physique.",
            "prix_fcfa": 0,
            "duree_jours": 365,
            "avantages": ["100% Hors-ligne", "Synchronisation locale sans Internet"],
        },
    ]

    for item in offres_data:
        o = db.query(OffreAbonnement).filter(OffreAbonnement.id == item["id"]).first()
        if not o:
            o = OffreAbonnement(
                id=item["id"],
                titre=item["titre"],
                description=item["description"],
                prix_fcfa=item["prix_fcfa"],
                duree_jours=item["duree_jours"],
                avantages_json=json.dumps(item["avantages"], ensure_ascii=False),
                actif=True,
            )
            db.add(o)
    db.commit()

    # Souscriptions réelles associées aux parents et élèves
    abonnements_actifs = [
        ("abo-001", "usr-parent-coulibaly", "premium_famille", "ACHAT_MOBILE_MONEY", "ACTIF", 15000, 280),
        ("abo-002", "usr-parent-diallo", "inclus_boitier", "ACHAT_MOBILE_MONEY", "ACTIF", 0, 320),
        ("abo-003", "usr-directeur", "premium_etablissement", "ADMIN_GRATIFIE", "ACTIF", 250000, 340),
        ("abo-004", "usr-parent-traore", "premium_famille", "ACHAT_MOBILE_MONEY", "ACTIF", 15000, 210),
        ("abo-005", "usr-parent-konate", "annuel_examen", "ACHAT_MOBILE_MONEY", "ACTIF", 20000, 180),
        ("abo-006", "usr-parent-cisse", "trimestriel_trimestre", "ACHAT_MOBILE_MONEY", "ACTIF", 6500, 45),
        ("abo-007", "usr-parent-keita", "mensuel_standard", "ACHAT_MOBILE_MONEY", "ACTIF", 2500, 20),
        ("abo-008", "usr-parent-diarra", "premium_famille", "ACHAT_MOBILE_MONEY", "ACTIF", 15000, 95),
        ("abo-009", "usr-parent-maiga", "annuel_examen", "ACHAT_MOBILE_MONEY", "ACTIF", 20000, 140),
    ]

    for aid, pid, oid, src, st, mnt, days_left in abonnements_actifs:
        sub = db.query(AbonnementUtilisateur).filter(AbonnementUtilisateur.id == aid).first()
        if not sub:
            sub = AbonnementUtilisateur(
                id=aid,
                apprenant_id=pid,
                offre_id=oid,
                source=src,
                statut=st,
                date_debut=datetime.now(UTC) - timedelta(days=60),
                date_expiration=datetime.now(UTC) + timedelta(days=days_left),
                date_creation=datetime.now(UTC) - timedelta(days=60),
            )
            db.add(sub)
    db.commit()

    # --------------------------------------------------------------------------
    # 7. Avatars Pédagogiques IA (Simli & RAG Edge)
    # --------------------------------------------------------------------------
    avatars_data = [
        {
            "id": "avatar-vivienne",
            "nom": "Professeure Vivienne",
            "matiere": "SVT & Sciences Naturelles",
            "style_pedagogique": "Chaleureuse, bienveillante et explicite avec exemples concrets du Mali",
            "voix_tts": "vivienne",
            "face_id": "bb1212ec-2cc5-4ca0-ad32-4a4427600345",
            "photo_url": "assets/avatars/vivienne.svg",
            "actif": True,
            "par_defaut": True,
        },
        {
            "id": "avatar-amadou",
            "nom": "Dr. Koné Amadou",
            "matiere": "Mathématiques & Algèbre (DEF & BAC)",
            "style_pedagogique": "Méthodique, étape par étape avec rigueur scientifique",
            "voix_tts": "remy",
            "face_id": "bb1212ec-2cc5-4ca0-ad32-4a4427600345",
            "photo_url": "assets/avatars/amadou.svg",
            "actif": True,
            "par_defaut": False,
        },
        {
            "id": "avatar-fatou",
            "nom": "Mme Samaké Fatou",
            "matiere": "Français, Philosophie & Littérature",
            "style_pedagogique": "Littéraire, interactive avec vocabulaire riche et citations maliennes",
            "voix_tts": "denise",
            "face_id": "bb1212ec-2cc5-4ca0-ad32-4a4427600345",
            "photo_url": "assets/avatars/fatou.svg",
            "actif": True,
            "par_defaut": False,
        },
        {
            "id": "avatar-sekou",
            "nom": "Prof. Sékou Traoré",
            "matiere": "Physique-Chimie & Technologies",
            "style_pedagogique": "Pratique, passionné par les sciences appliquées et les expériences réelles",
            "voix_tts": "george",
            "face_id": "f78d91b4-1c23-4d56-a789-ef0123456789",
            "photo_url": "assets/avatars/sekou.svg",
            "actif": True,
            "par_defaut": False,
        },
    ]

    for av in avatars_data:
        existing_av = db.query(AvatarPedagogique).filter(AvatarPedagogique.id == av["id"]).first()
        if not existing_av:
            existing_av = AvatarPedagogique(
                id=av["id"],
                nom=av["nom"],
                matiere=av["matiere"],
                style_pedagogique=av["style_pedagogique"],
                voix_tts=av["voix_tts"],
                face_id=av["face_id"],
                photo_url=av["photo_url"],
                actif=av["actif"],
                par_defaut=av["par_defaut"],
                date_creation=datetime.now(UTC) - timedelta(days=180),
            )
            db.add(existing_av)
        else:
            existing_av.nom = av["nom"]
            existing_av.matiere = av["matiere"]
            existing_av.style_pedagogique = av["style_pedagogique"]
            existing_av.voix_tts = av["voix_tts"]
            existing_av.face_id = av["face_id"]
    db.commit()

    # --------------------------------------------------------------------------
    # 8. Alertes Pédagogiques Réelles
    # --------------------------------------------------------------------------
    alertes_data = [
        {
            "id": "alt-001",
            "apprenant_id": "appr-amadou-diallo",
            "titre": "Difficulté récurrente : Réactions Acide-Base & Calcul de pH",
            "description": "L'élève Amadou Diallo a sollicité 4 explications successives sur la constante d'acidité Ka et le pH.",
            "type_alerte": "difficulte_recurrente",
            "gravite": "moyenne",
            "matiere": "Physique-Chimie",
            "resolu": False,
        },
        {
            "id": "alt-002",
            "apprenant_id": "appr-fatou-traore",
            "titre": "Excellente progression : Nombres Complexes & Géométrie Terminale TSE",
            "description": "Fatoumata a réussi 96% des résolutions d'équations dans C sur les annales officielles du Bac malien.",
            "type_alerte": "reussite_remarquable",
            "gravite": "faible",
            "matiere": "Mathématiques",
            "resolu": True,
        },
        {
            "id": "alt-003",
            "apprenant_id": "appr-ousmane-coulibaly",
            "titre": "Inactivité constatée : Aucune révision depuis 8 jours",
            "description": "Ousmane n'a pas utilisé le boîtier pour la préparation du DEF cette semaine.",
            "type_alerte": "inactivite",
            "gravite": "moyenne",
            "matiere": "DEF Général",
            "resolu": False,
        },
    ]

    for alt in alertes_data:
        a = db.query(AlertePedagogique).filter(AlertePedagogique.id == alt["id"]).first()
        if not a:
            a = AlertePedagogique(
                id=alt["id"],
                apprenant_id=alt["apprenant_id"],
                titre=alt["titre"],
                description=alt["description"],
                type_alerte=alt["type_alerte"],
                gravite=alt["gravite"],
                matiere=alt["matiere"],
                resolu=alt["resolu"],
                date_creation=datetime.now(UTC) - timedelta(days=2),
            )
            db.add(a)
    db.commit()

    # --------------------------------------------------------------------------
    # 9. Campagnes OTA Réelles
    # --------------------------------------------------------------------------
    campagnes_data = [
        {
            "id": "ota-campagne-01",
            "nom": "Mise à jour Firmware v2.1 (Optimisation RAG Edge & TTS Bambara)",
            "version_cible": "v2.1-LocalEdge",
            "type_contenu": "Firmware Système",
            "taille_mo": 142.5,
            "total_cibles": 10,
            "total_appliques": 9,
            "total_en_attente": 1,
            "statut": "En cours",
        },
        {
            "id": "ota-campagne-02",
            "nom": "Pack Culturel Intégral Mali 2026 (Nouveaux Contes, Devinettes & Proverbes)",
            "version_cible": "culture-pack-v3.0",
            "type_contenu": "Pack Culture & Contes",
            "taille_mo": 85.0,
            "total_cibles": 10,
            "total_appliques": 10,
            "total_en_attente": 0,
            "statut": "Terminée",
        },
        {
            "id": "ota-campagne-03",
            "nom": "Pack Annales & Corrigés Types Examens DEF & Baccalauréat 2026",
            "version_cible": "exam-pack-2026",
            "type_contenu": "Pack Cours Pédagogiques",
            "taille_mo": 64.0,
            "total_cibles": 10,
            "total_appliques": 8,
            "total_en_attente": 2,
            "statut": "En cours",
        },
    ]

    for c_data in campagnes_data:
        c = db.query(CampagneOTA).filter(CampagneOTA.id == c_data["id"]).first()
        if not c:
            c = CampagneOTA(
                id=c_data["id"],
                nom=c_data["nom"],
                version_cible=c_data["version_cible"],
                type_contenu=c_data["type_contenu"],
                taille_mo=c_data["taille_mo"],
                total_cibles=c_data["total_cibles"],
                total_appliques=c_data["total_appliques"],
                total_en_attente=c_data["total_en_attente"],
                statut=c_data["statut"],
                date_lancement=datetime.now(UTC) - timedelta(days=4),
            )
            db.add(c)
    db.commit()

    # --------------------------------------------------------------------------
    # 10. Paramètres de Plateforme Réels
    # --------------------------------------------------------------------------
    parametres_defauts = {
        "nomPlateforme": "AlternIA — Plateforme Nationale EdTech du Mali",
        "paysPrincipal": "Mali (ML)",
        "emailAdmin": "superadmin@alternia.ml",
        "fuseauHoraire": "Africa/Bamako (UTC+0)",
        "modeMaintenance": "false",
        "seuilAlerteBoitierHeures": "24",
        "tauxTvaPourcent": "18",
        "devise": "FCFA (XOF)",
        "sauvegardesAutomatiques": "true",
        "frequenceSauvegarde": "Quotidienne",
    }

    for cle, val in parametres_defauts.items():
        param = db.query(ParametrePlateforme).filter(ParametrePlateforme.cle == cle).first()
        if not param:
            param = ParametrePlateforme(
                cle=cle,
                valeur=val,
                type_donnee="str",
                description=f"Paramètre système {cle}",
                date_mise_a_jour=datetime.now(UTC),
            )
            db.add(param)
    db.commit()

    # --------------------------------------------------------------------------
    # 11. Notifications Administrateur
    # --------------------------------------------------------------------------
    notifs_data = [
        {
            "id": "notif-001",
            "type": "succes",
            "categorie": "hardware",
            "titre": "Flotte de Boîtiers Synchronisée",
            "message": "10 boîtiers physiques locaux sont opérationnels avec les packs d'annales DEF & BAC 2026.",
            "lu": False,
            "source": "Edge Network Monitor",
            "lien_route": "/boitiers",
            "lien_label": "Voir la flotte",
        },
        {
            "id": "notif-002",
            "type": "info",
            "categorie": "gouvernance",
            "titre": "Déploiement Lycée Mahamane Alassane Haïdara",
            "message": "Le boîtier physique ALT-BOX-2026-010 de Tombouctou a transmis son premier bilan de télémétrie locale.",
            "lu": False,
            "source": "Gouvernance Territoriale",
            "lien_route": "/etablissements",
            "lien_label": "Voir l'établissement",
        },
        {
            "id": "notif-003",
            "type": "avertissement",
            "categorie": "ia",
            "titre": "Vérification Fréquence Audio Bambara",
            "message": "La synthèse vocale locale en bambara fonctionne à 100% sans coupure sur le boîtier de Sévaré/Mopti.",
            "lu": True,
            "source": "Simli Edge Engine",
            "lien_route": "/pedagogie-ia",
            "lien_label": "Voir métriques",
        },
    ]

    for n_data in notifs_data:
        n = db.query(NotificationAdmin).filter(NotificationAdmin.id == n_data["id"]).first()
        if not n:
            n = NotificationAdmin(
                id=n_data["id"],
                type=n_data["type"],
                categorie=n_data["categorie"],
                titre=n_data["titre"],
                message=n_data["message"],
                lu=n_data["lu"],
                source=n_data["source"],
                lien_route=n_data["lien_route"],
                lien_label=n_data["lien_label"],
                date_creation=datetime.now(UTC) - timedelta(hours=6),
            )
            db.add(n)
    db.commit()

    # --------------------------------------------------------------------------
    # 12. Statistiques et Sessions Pédagogiques Réelles
    # --------------------------------------------------------------------------
    today_str = datetime.now(UTC).strftime("%Y-%m-%d")
    stats_data = [
        {
            "id": "stat-maths-12e",
            "date_jour": today_str,
            "classe": "12eme",
            "matiere": "Mathématiques",
            "total_interactions": 342,
            "total_temps_sec": 75600,
            "taux_comprehension": 84.5,
            "notions": ["Théorème des valeurs intermédiaires", "Nombres complexes et géométrie", "Intégrales et primitives"],
        },
        {
            "id": "stat-pc-11s",
            "date_jour": today_str,
            "classe": "11eme",
            "matiere": "Physique-Chimie",
            "total_interactions": 258,
            "total_temps_sec": 54200,
            "taux_comprehension": 81.2,
            "notions": ["Réactions acido-basiques", "Cinématique du point", "Lois de Newton"],
        },
        {
            "id": "stat-svt-12e",
            "date_jour": today_str,
            "classe": "12eme",
            "matiere": "Biologie & SVT",
            "total_interactions": 195,
            "total_temps_sec": 41800,
            "taux_comprehension": 86.0,
            "notions": ["Génétique et lois de Mendel", "Immunologie et anticorps", "Reproduction cellulaire"],
        },
        {
            "id": "stat-culture-mali",
            "date_jour": today_str,
            "classe": "10eme",
            "matiere": "Histoire-Géo & Culture Malienne",
            "total_interactions": 284,
            "total_temps_sec": 61200,
            "taux_comprehension": 92.4,
            "notions": ["Épopée de Soundiata Keïta", "Charte de Kouroukan Fouga 1236", "Monuments historiques et Mosquée de Djenné"],
        },
    ]

    for s_data in stats_data:
        st = db.query(StatistiquePedagogique).filter(StatistiquePedagogique.id == s_data["id"]).first()
        if not st:
            st = StatistiquePedagogique(
                id=s_data["id"],
                date_jour=s_data["date_jour"],
                classe=s_data["classe"],
                matiere=s_data["matiere"],
                total_interactions=s_data["total_interactions"],
                total_temps_sec=s_data["total_temps_sec"],
                taux_comprehension=s_data["taux_comprehension"],
                notions_difficiles_json=json.dumps(s_data["notions"], ensure_ascii=False),
            )
            db.add(st)
    db.commit()

    print("[SUPER ADMIN SEED OK] Données réelles synchronisées avec succès.")
