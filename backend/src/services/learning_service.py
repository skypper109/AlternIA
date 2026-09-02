"""
Service d'enregistrement en temps réel des interactions pédagogiques et détection intelligente d'alertes.
"""

from datetime import datetime
import json
import logging
from typing import Any, List, Optional
import uuid

from backend.src.db.database import SessionLocal
from backend.src.db.models import (
    AlertePedagogique,
    Apprenant,
    InteractionPedagogique,
    SessionApprentissage,
    StatistiquePedagogique,
)

logger = logging.getLogger("AlternIA.LearningService")

CONFUSION_KEYWORDS = [
    "ne comprends pas",
    "comprends rien",
    "trop dur",
    "difficile",
    "compliqué",
    "aide-moi",
    "aide moi",
    "bloqué",
    "pas compris",
    "pourquoi",
    "impossible",
    "erreur",
]


def sanitize_pedagogical_context(
    subject: Optional[str],
    topic: Optional[str],
    chapter: Optional[str],
    question: str
) -> tuple[str, str, str]:
    q_low = (question or "").lower()
    
    # 1. Biologie / SVT
    if any(k in q_low for k in ["photosynth", "chlorophyl", "amidon", "calvin"]):
        return "SVT", "La Photosynthèse et Métabolisme", "Biochimie végétale"
    if any(k in q_low for k in ["mitose", "meiose", "chromosome", "cellule", "membrane", "adn", "genetique"]):
        return "SVT", "Division Cellulaire & Génétique", "Génétique et Biologie Cellulaire"
    if any(k in q_low for k in ["zonation", "ecologie", "ecosysteme", "sahel", "biotop"]):
        return "SVT", "Écologie & Zonation végétale", "Environnement et Écosystèmes Sahéliens"
    
    # 2. Chimie
    if any(k in q_low for k in ["oxydo", "redox", "oxydant", "reducteur", "couple"]):
        return "Chimie", "Oxydoréduction & Couples Redox", "Chimie Générale"
    if any(k in q_low for k in ["alcool", "aldehide", "aldehyde", "cetone", "ester", "acide carboxylique"]):
        return "Chimie", "Chimie Organique & Fonctions Oxygénées", "Chimie Organique"
    if any(k in q_low for k in ["ph", "acide", "base", "solution aqueuse", "pka"]):
        return "Chimie", "Réactions Acido-Basiques & Calculs de pH", "Solutions Aqueuses"
    if any(k in q_low for k in ["chatelier", "equilibre chimique"]):
        return "Chimie", "Équilibres Chimiques", "Cinétique et Équilibres"

    # 3. Physique
    if any(k in q_low for k in ["gravitation", "newton", "satellite", "attraction"]):
        return "Physique", "Gravitation Universelle & Lois de Newton", "Mécanique Classique"
    if any(k in q_low for k in ["doppler", "onde", "frequence", "longueur d'onde", "sonore"]):
        return "Physique", "Ondes Mécaniques & Effet Doppler", "Physique Ondulatoire"
    if any(k in q_low for k in ["cinematique", "vitesse", "acceleration", "trajectoire", "vecteur position"]):
        return "Physique", "Cinématique du Point Matériel", "Mécanique du Point"

    # 4. Mathématiques
    if any(k in q_low for k in ["complexe", "module", "argument", "forme trigonometrique", "z ="]):
        return "Mathématiques", "Nombres Complexes & Trigonométrie", "Analyse et Algèbre"
    if any(k in q_low for k in ["equation", "polynome", "discriminant", "delta", "racine"]):
        return "Mathématiques", "Équations & Polynômes du Second Degré", "Algèbre"
    if any(k in q_low for k in ["derivee", "derivation", "tangente", "limite", "continuite"]):
        return "Mathématiques", "Dérivation & Étude de Fonctions", "Analyse Fonctionnelle"
    if any(k in q_low for k in ["integrale", "primitive", "integration par parties"]):
        return "Mathématiques", "Calcul Intégral & Primitives", "Analyse"

    # 5. Économie
    if any(k in q_low for k in ["pib", "comptabilite", "macroeconomie", "inflation", "chomage"]):
        return "Économie", "Comptabilité Nationale & Agrégats Économiques", "Macroéconomie"

    # 6. Français & Philosophie
    if any(k in q_low for k in ["dissertation", "commentaire", "these", "antithese"]):
        return "Français", "Méthodologie de la Dissertation et du Commentaire", "Expression et Littérature"

    clean_topic = topic or "Programme officiel"
    for noisy in ["CONTENU DE COURS", "Guide", "Chap", "Cours 11", ".pdf", ".docx", "(6h)", "(4h)"]:
        clean_topic = clean_topic.replace(noisy, "").strip(" -_:")
    if not clean_topic or clean_topic.lower() == "general":
        clean_topic = "Méthodologie et Synthèse"

    clean_subject = (subject or "Général").capitalize()
    if clean_subject.lower() in ["biologie", "svt"]:
        clean_subject = "SVT"

    return clean_subject, clean_topic, chapter or "Programme National"


def record_student_interaction(
    student_id: str = "appr-amadou-diallo",
    student_class: str = "11eme",
    series: Optional[str] = "11S",
    subject: Optional[str] = "biologie",
    question: str = "",
    answer: str = "",
    sources: Optional[List[Any]] = None,
    intent: str = "explanation",
    difficulty: str = "moyen",
    success: bool = True,
    session_id: Optional[str] = None,
    boitier_id: Optional[str] = "box-alta-01",
    chapter: Optional[str] = None,
    topic: Optional[str] = None,
) -> Optional[InteractionPedagogique]:
    """
    Enregistre l'interaction de l'élève (depuis le CLI Chat ou l'API Web)
    dans la base de données réelle alta_db, met à jour le profil de l'apprenant,
    agrège les statistiques et crée des alertes pédagogiques en direct si nécessaire.
    """
    if not question:
        return None

    db = SessionLocal()
    try:
        # Résolution didactique propre de la matière, de la notion et du chapitre
        effective_subject, effective_topic, effective_chapter = sanitize_pedagogical_context(
            subject, topic, chapter, question
        )

        # 1. Vérification ou création de l'apprenant
        apprenant = db.query(Apprenant).filter(
            (Apprenant.id == student_id) | (Apprenant.matricule == student_id)
        ).first()

        if not apprenant:
            # Fallback sur le premier apprenant si identifiant générique
            apprenant = db.query(Apprenant).first()
            if not apprenant:
                apprenant = Apprenant(
                    id=student_id or f"appr-{uuid.uuid4().hex[:8]}",
                    nom="Élève",
                    prenom="AlternIA",
                    matricule=f"ML-{uuid.uuid4().hex[:6].upper()}",
                    classe=student_class or "11eme",
                    serie=series or "11S",
                    niveau_maitrise=75.0,
                    temps_total_sec=300,
                    questions_posees=1,
                    dernier_acces=datetime.utcnow(),
                )
                db.add(apprenant)
                db.commit()
                db.refresh(apprenant)

        # Mise à jour des stats de l'élève
        apprenant.questions_posees = (apprenant.questions_posees or 0) + 1
        apprenant.temps_total_sec = (apprenant.temps_total_sec or 0) + 45
        apprenant.dernier_acces = datetime.utcnow()

        # 2. Gestion de la session active
        session_obj = None
        if session_id:
            session_obj = db.query(SessionApprentissage).filter(
                SessionApprentissage.id == session_id
            ).first()

        if not session_obj:
            session_obj = SessionApprentissage(
                id=session_id or f"sess-{uuid.uuid4().hex[:8]}",
                apprenant_id=apprenant.id,
                boitier_id=boitier_id or apprenant.boitier_id or "box-alta-01",
                matiere=effective_subject.lower(),
                chapitre=effective_chapter,
                notion=effective_topic or effective_subject,
                date_debut=datetime.utcnow(),
                date_fin=datetime.utcnow(),
                duree_sec=60,
                questions_count=1,
                reussite_taux=80.0 if success else 40.0,
            )
            db.add(session_obj)
        else:
            session_obj.questions_count = (session_obj.questions_count or 0) + 1
            session_obj.date_fin = datetime.utcnow()
            session_obj.duree_sec = (session_obj.duree_sec or 0) + 45

        # 3. Enregistrement de l'interaction
        interaction = InteractionPedagogique(
            id=f"inter-{uuid.uuid4().hex[:10]}",
            session_id=session_obj.id,
            apprenant_id=apprenant.id,
            question=question,
            reponse=answer,
            matiere=effective_subject.lower(),
            notion=effective_topic or effective_chapter or effective_subject,
            intention=intent,
            difficulte=difficulty,
            succes=success,
            timestamp=datetime.utcnow(),
        )
        db.add(interaction)

        # 4. Détection intelligente de difficulté pour création d'une Alerte Pédagogique
        q_lower = question.lower()
        has_confusion = any(kw in q_lower for kw in CONFUSION_KEYWORDS) or not success

        if has_confusion:
            topic_label = effective_topic or effective_chapter or effective_subject
            nom_eleve = f"{apprenant.prenom} {apprenant.nom}"
            titre_alerte = f"Difficulté détectée en {effective_subject} : {topic_label}"
            description_alerte = (
                f"L'élève {nom_eleve} ({apprenant.classe} {apprenant.serie or ''}) "
                f"a rencontré une difficulté sur la notion « {topic_label} » lors d'un échange avec ALTA.\n"
                f"Question posée : « {question[:120]}... »"
            )

            alerte = AlertePedagogique(
                id=f"alt-{uuid.uuid4().hex[:8]}",
                apprenant_id=apprenant.id,
                titre=titre_alerte,
                description=description_alerte,
                type_alerte="difficulte_recurrente",
                gravite="moyenne" if not has_confusion else "elevee",
                matiere=effective_subject.lower(),
                resolu=False,
                date_creation=datetime.utcnow(),
            )
            db.add(alerte)
            logger.info(f"🚨 Nouvelle alerte pédagogique créée en direct : {titre_alerte}")

        # 5. Mise à jour des statistiques journalières
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        stat = db.query(StatistiquePedagogique).filter(
            StatistiquePedagogique.date_jour == today_str,
            StatistiquePedagogique.classe == apprenant.classe,
            StatistiquePedagogique.matiere == effective_subject.lower(),
        ).first()

        if not stat:
            notions = [effective_topic] if (effective_topic and has_confusion) else []
            stat = StatistiquePedagogique(
                id=f"stat-{uuid.uuid4().hex[:8]}",
                date_jour=today_str,
                classe=apprenant.classe,
                matiere=effective_subject.lower(),
                total_interactions=1,
                total_temps_sec=45,
                taux_comprehension=70.0 if has_confusion else 85.0,
                notions_difficiles_json=json.dumps(notions),
            )
            db.add(stat)
        else:
            stat.total_interactions = (stat.total_interactions or 0) + 1
            stat.total_temps_sec = (stat.total_temps_sec or 0) + 45
            if has_confusion and effective_topic:
                try:
                    notions_list = json.loads(stat.notions_difficiles_json or "[]")
                    if effective_topic not in notions_list:
                        notions_list.append(effective_topic)
                    stat.notions_difficiles_json = json.dumps(notions_list)
                except Exception:
                    pass

        db.commit()
        db.refresh(interaction)
        return interaction
    except Exception as exc:
        db.rollback()
        logger.warning(f"Erreur lors de l'enregistrement de l'interaction : {exc}")
        return None
    finally:
        db.close()
