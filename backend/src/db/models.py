"""
Modèles de données SQLAlchemy pour la base alta_db.
"""

import uuid
from datetime import UTC, datetime
from typing import Optional

from backend.src.db.database import Base
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    mot_de_passe_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(30), nullable=False, default="parent")  # 'admin_ecole', 'parent', 'enseignant'
    nom_complet: Mapped[str] = mapped_column(String(120), nullable=False)
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    date_creation: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)
    dernier_acces: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)
    actif: Mapped[bool] = mapped_column(Boolean, default=True)


class Etablissement(Base):
    __tablename__ = "etablissements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    nom: Mapped[str] = mapped_column(String(150), nullable=False)
    type_etablissement: Mapped[str] = mapped_column(String(50), default="Lycée")  # 'Lycée', 'Collège', 'Complexe Scolaire'
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    adresse: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ville: Mapped[str] = mapped_column(String(100), default="Bamako")
    pays: Mapped[str] = mapped_column(String(100), default="Mali")
    telephone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(120), nullable=True)
    date_creation: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)

    boitiers: Mapped[list["Boitier"]] = relationship("Boitier", back_populates="etablissement")
    apprenants: Mapped[list["Apprenant"]] = relationship("Apprenant", back_populates="etablissement")


class Boitier(Base):
    __tablename__ = "boitiers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    numero_serie: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    modele: Mapped[str] = mapped_column(String(80), default="AlternIA Box v2.0")
    firmware: Mapped[str] = mapped_column(String(50), default="v2.0-LocalEdge")
    statut: Mapped[str] = mapped_column(String(30), default="en_ligne")  # 'en_ligne', 'hors_ligne', 'synchronisation', 'en_charge'
    batterie: Mapped[int] = mapped_column(Integer, default=95)
    stockage_go: Mapped[float] = mapped_column(Float, default=32.0)
    stockage_utilise_go: Mapped[float] = mapped_column(Float, default=8.4)
    wifi_ssid: Mapped[str] = mapped_column(String(100), default="AlternIA-Box-WiFi")
    ip_locale: Mapped[str] = mapped_column(String(45), default="192.168.4.1")
    derniere_synchro: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)
    date_activation: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)

    etablissement_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("etablissements.id"), nullable=True)
    enfant_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    etablissement: Mapped[Optional["Etablissement"]] = relationship("Etablissement", back_populates="boitiers")
    apprenants: Mapped[list["Apprenant"]] = relationship("Apprenant", back_populates="boitier")


class Apprenant(Base):
    __tablename__ = "apprenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    nom: Mapped[str] = mapped_column(String(80), nullable=False)
    prenom: Mapped[str] = mapped_column(String(80), nullable=False)
    matricule: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    classe: Mapped[str] = mapped_column(String(20), nullable=False, default="11eme")  # '10eme', '11eme', '12eme'
    serie: Mapped[str | None] = mapped_column(String(30), nullable=True, default="11S")       # '11S', '11L', 'TSE', 'TSExp', etc.
    niveau_maitrise: Mapped[float] = mapped_column(Float, default=74.5)                  # Pourcentage global
    temps_total_sec: Mapped[int] = mapped_column(Integer, default=14200)
    questions_posees: Mapped[int] = mapped_column(Integer, default=42)
    dernier_acces: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)
    date_inscription: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)
    photo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)

    etablissement_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("etablissements.id"), nullable=True)
    boitier_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("boitiers.id"), nullable=True)

    etablissement: Mapped[Optional["Etablissement"]] = relationship("Etablissement", back_populates="apprenants")
    boitier: Mapped[Optional["Boitier"]] = relationship("Boitier", back_populates="apprenants")
    sessions: Mapped[list["SessionApprentissage"]] = relationship("SessionApprentissage", back_populates="apprenant")
    alertes: Mapped[list["AlertePedagogique"]] = relationship("AlertePedagogique", back_populates="apprenant")


class SessionApprentissage(Base):
    __tablename__ = "sessions_apprentissage"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    apprenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("apprenants.id"), nullable=False)
    boitier_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("boitiers.id"), nullable=True)
    matiere: Mapped[str] = mapped_column(String(50), nullable=False, default="biologie")
    chapitre: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notion: Mapped[str | None] = mapped_column(String(100), nullable=True)
    date_debut: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)
    date_fin: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)
    duree_sec: Mapped[int] = mapped_column(Integer, default=900)
    questions_count: Mapped[int] = mapped_column(Integer, default=5)
    reussite_taux: Mapped[float] = mapped_column(Float, default=80.0)

    apprenant: Mapped[Optional["Apprenant"]] = relationship("Apprenant", back_populates="sessions")
    interactions: Mapped[list["InteractionPedagogique"]] = relationship("InteractionPedagogique", back_populates="session")


class InteractionPedagogique(Base):
    __tablename__ = "interactions_pedagogiques"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    session_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("sessions_apprentissage.id"), nullable=True)
    apprenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    reponse: Mapped[str] = mapped_column(Text, nullable=False)
    matiere: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notion: Mapped[str | None] = mapped_column(String(100), nullable=True)
    intention: Mapped[str] = mapped_column(String(50), default="explanation")
    difficulte: Mapped[str] = mapped_column(String(30), default="moyen")
    succes: Mapped[bool] = mapped_column(Boolean, default=True)
    timestamp: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)

    session: Mapped[Optional["SessionApprentissage"]] = relationship("SessionApprentissage", back_populates="interactions")


class AvatarPedagogique(Base):
    __tablename__ = "avatars_pedagogiques"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    nom: Mapped[str] = mapped_column(String(80), nullable=False)
    matiere: Mapped[str] = mapped_column(String(80), nullable=False, default="Toutes matières")
    style_pedagogique: Mapped[str] = mapped_column(String(120), default="Bienveillant, rigoureux et interactif")
    voix_tts: Mapped[str] = mapped_column(String(60), default="vivienne")
    face_id: Mapped[str | None] = mapped_column(String(255), nullable=True, default="bb1212ec-2cc5-4ca0-ad32-4a4427600345")
    photo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    audio_sample_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    audio_file_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    actif: Mapped[bool] = mapped_column(Boolean, default=True)
    par_defaut: Mapped[bool] = mapped_column(Boolean, default=False)
    landmarks_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    viseme_photos_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    date_creation: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)


class AlertePedagogique(Base):
    __tablename__ = "alertes_pedagogiques"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    apprenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("apprenants.id"), nullable=False)
    titre: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    type_alerte: Mapped[str] = mapped_column(String(50), default="difficulte_recurrente")  # 'difficulte_recurrente', 'inactivite', 'reussite_remarquable'
    gravite: Mapped[str] = mapped_column(String(20), default="moyenne")                   # 'faible', 'moyenne', 'elevee'
    matiere: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resolu: Mapped[bool] = mapped_column(Boolean, default=False)
    date_creation: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)

    apprenant: Mapped[Optional["Apprenant"]] = relationship("Apprenant", back_populates="alertes")


class StatistiquePedagogique(Base):
    __tablename__ = "statistiques_pedagogiques"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    date_jour: Mapped[str] = mapped_column(String(10), index=True, nullable=False)  # 'YYYY-MM-DD'
    classe: Mapped[str] = mapped_column(String(20), nullable=False)
    matiere: Mapped[str] = mapped_column(String(50), nullable=False)
    total_interactions: Mapped[int] = mapped_column(Integer, default=0)
    total_temps_sec: Mapped[int] = mapped_column(Integer, default=0)
    taux_comprehension: Mapped[float] = mapped_column(Float, default=75.0)
    notions_difficiles_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array


class SeanceRevisionModel(Base):
    __tablename__ = "seances_revision"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    titre: Mapped[str] = mapped_column(String(150), nullable=False)
    matiere: Mapped[str] = mapped_column(String(50), nullable=False)
    jour: Mapped[str] = mapped_column(String(10), nullable=False)  # 'YYYY-MM-DD'
    heure_debut: Mapped[str] = mapped_column(String(10), nullable=False)  # 'HH:MM'
    heure_fin: Mapped[str] = mapped_column(String(10), nullable=False)
    duree_minutes: Mapped[int] = mapped_column(Integer, default=45)
    commentaire: Mapped[str | None] = mapped_column(Text, nullable=True)
    statut: Mapped[str] = mapped_column(String(30), default="PROGRAMMÉE")
    rappel_minutes_avant: Mapped[int] = mapped_column(Integer, default=30)
    date_creation: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)


class RapportModel(Base):
    __tablename__ = "rapports_pedagogiques"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    etablissement_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    titre: Mapped[str] = mapped_column(String(150), nullable=False)
    periode: Mapped[str] = mapped_column(String(80), default="Semaine en cours")
    date_debut: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)
    date_fin: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)
    type_fichier: Mapped[str] = mapped_column(String(20), default="pdf")  # 'pdf', 'excel'
    statut: Mapped[str] = mapped_column(String(30), default="genere")
    taille_fichier_octets: Mapped[int] = mapped_column(Integer, default=450000)
    url_telechargement: Mapped[str | None] = mapped_column(String(255), nullable=True)
    date_generation: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)


# ==============================================================================
# MODÈLES CULTURELENS & PATRIMOINE DU MALI (BASE DE DONNÉES CENTRALE)
# ==============================================================================

class CultureMonument(Base):
    __tablename__ = "culture_monuments"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)  # ex: 'monument_independance_bamako'
    nom: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    sous_titre: Mapped[str] = mapped_column(String(200), nullable=False)
    region_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    region_nom: Mapped[str] = mapped_column(String(100), nullable=False)
    ville: Mapped[str] = mapped_column(String(100), nullable=False, index=True, default="Bamako")
    epoque: Mapped[str] = mapped_column(String(150), nullable=False)
    style_architectural: Mapped[str] = mapped_column(Text, nullable=False)
    details_localisation: Mapped[str] = mapped_column(String(255), nullable=False)
    photo_url: Mapped[str] = mapped_column(String(255), nullable=False)
    tag: Mapped[str] = mapped_column(String(100), default="Monument National")
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    badge_debloque: Mapped[str] = mapped_column(String(150), nullable=False)
    xp_recompense: Mapped[int] = mapped_column(Integer, default=50)
    mots_cles_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON list
    caracteristiques_detection_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON list
    secrets_et_mysteres: Mapped[str] = mapped_column(Text, nullable=False)
    recit_historique: Mapped[str] = mapped_column(Text, nullable=False)
    narration_audio_texte: Mapped[str] = mapped_column(Text, nullable=False)
    pourquoi_ce_lieu_compte: Mapped[str] = mapped_column(Text, nullable=False)
    route_path: Mapped[str] = mapped_column(String(200), nullable=False)
    modele_3d_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ar_disponible: Mapped[bool] = mapped_column(Boolean, default=False)
    audio_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    statut_validation: Mapped[str] = mapped_column(String(100), default="Patrimoine vérifié")
    date_mise_a_jour: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)

    decouvertes: Mapped[list["CultureDecouverte"]] = relationship("CultureDecouverte", back_populates="monument")


class CulturePersonnage(Base):
    __tablename__ = "culture_personnages"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    nom: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    titre_honorifique: Mapped[str] = mapped_column(String(200), nullable=False)
    periode: Mapped[str] = mapped_column(String(100), nullable=False)
    region_id: Mapped[str] = mapped_column(String(50), nullable=False)
    region_nom: Mapped[str] = mapped_column(String(100), nullable=False)
    tag: Mapped[str] = mapped_column(String(100), default="Héros Historique")
    photo_url: Mapped[str] = mapped_column(String(255), nullable=False)
    photo_credits: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resume: Mapped[str] = mapped_column(Text, nullable=False)
    citation_historique: Mapped[str | None] = mapped_column(Text, nullable=True)
    faits_marquants_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON list
    chapitres_json: Mapped[str] = mapped_column(Text, nullable=False)        # JSON list
    elements_lies_json: Mapped[str] = mapped_column(Text, nullable=False)     # JSON list
    audio_narration: Mapped[str | None] = mapped_column(Text, nullable=True)
    date_creation: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)


class CultureLieu(Base):
    __tablename__ = "culture_lieux"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    nom: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    sous_titre: Mapped[str] = mapped_column(String(200), nullable=False)
    region_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    region_nom: Mapped[str] = mapped_column(String(100), nullable=False)
    tag: Mapped[str] = mapped_column(String(100), default="Cité Historique")
    photo_url: Mapped[str] = mapped_column(String(255), nullable=False)
    photo_credits: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fondation: Mapped[str] = mapped_column(String(150), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, default=12.6392)
    longitude: Mapped[float] = mapped_column(Float, default=-8.0029)
    population_ou_details: Mapped[str | None] = mapped_column(String(150), nullable=True)
    resume: Mapped[str] = mapped_column(Text, nullable=False)
    chapitres_json: Mapped[str] = mapped_column(Text, nullable=False)
    elements_lies_json: Mapped[str] = mapped_column(Text, nullable=False)
    date_creation: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)

    @property
    def surnom(self) -> str:
        return self.sous_titre

    @property
    def description_detaillee(self) -> str:
        return self.resume

    @property
    def evenements_majeurs(self) -> str:
        return self.fondation



class CultureConte(Base):
    __tablename__ = "culture_contes"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    titre: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    sous_titre: Mapped[str] = mapped_column(String(200), nullable=False)
    origine: Mapped[str] = mapped_column(String(150), nullable=False)
    region_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    region_nom: Mapped[str] = mapped_column(String(100), default="Tout le Mali")
    tag: Mapped[str] = mapped_column(String(100), default="Fable & Conte")
    photo_url: Mapped[str] = mapped_column(String(255), nullable=False)
    photo_credits: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resume: Mapped[str] = mapped_column(Text, nullable=False)
    conteur: Mapped[str] = mapped_column(String(120), default="Griot AlternIA")
    duree_audio: Mapped[str] = mapped_column(String(30), default="5 min")
    duree_lecture: Mapped[str] = mapped_column(String(30), default="3 min")
    morale: Mapped[str] = mapped_column(Text, nullable=False)
    scenes_json: Mapped[str] = mapped_column(Text, nullable=False)
    elements_lies_json: Mapped[str] = mapped_column(Text, nullable=False)
    date_creation: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)


class CultureProverbe(Base):
    __tablename__ = "culture_proverbes"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    texte: Mapped[str] = mapped_column(Text, nullable=False)
    texte_original: Mapped[str | None] = mapped_column(Text, nullable=True)
    signification: Mapped[str] = mapped_column(Text, nullable=False)
    morale: Mapped[str] = mapped_column(String(255), nullable=False)
    origine: Mapped[str] = mapped_column(String(150), nullable=False)
    theme: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    region_id: Mapped[str] = mapped_column(String(50), nullable=False)
    region_nom: Mapped[str] = mapped_column(String(100), nullable=False)
    xp_recompense: Mapped[int] = mapped_column(Integer, default=40)
    orateur_nom: Mapped[str | None] = mapped_column(String(100), nullable=True)
    orateur_role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    accent_color_hex: Mapped[str] = mapped_column(String(10), default="#F1851F")


class CultureDecouverte(Base):
    __tablename__ = "culture_decouvertes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    apprenant_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    monument_id: Mapped[str] = mapped_column(String(100), ForeignKey("culture_monuments.id"), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.98)
    est_favori: Mapped[bool] = mapped_column(Boolean, default=False)
    notes_personnelles: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_scannee_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    date_decouverte: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)

    monument: Mapped["CultureMonument"] = relationship("CultureMonument", back_populates="decouvertes")


class CulturePack(Base):
    __tablename__ = "culture_packs"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    titre: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    region_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    region_nom: Mapped[str] = mapped_column(String(100), nullable=False)
    taille_mo: Mapped[float] = mapped_column(Float, default=12.5)
    version: Mapped[str] = mapped_column(String(20), default="1.0.0")
    elements_count: Mapped[int] = mapped_column(Integer, default=15)
    inclus_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON summary
    bundle_data_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # Full offline JSON
    date_mise_a_jour: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)


class CultureNom(Base):
    __tablename__ = "culture_noms"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)  # ex: 'nom_keita', 'prenom_fatoumata'
    nom: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    nom_normalise: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="nom")  # 'nom' ou 'prenom'
    ethnie_ou_region: Mapped[str] = mapped_column(String(150), nullable=False)
    signification: Mapped[str] = mapped_column(Text, nullable=False)
    clan_role: Mapped[str] = mapped_column(String(200), nullable=False)
    totem: Mapped[str] = mapped_column(String(150), nullable=False)  # Tanan ancestral
    senankouya: Mapped[str] = mapped_column(String(255), nullable=False)  # Cousinage à plaisanterie
    devise_ou_louange: Mapped[str | None] = mapped_column(Text, nullable=True)  # Louange griotique
    anecdote: Mapped[str] = mapped_column(Text, nullable=False)
    variantes_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON list
    date_creation: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)


class CultureContribution(Base):
    __tablename__ = "culture_contributions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    
    # Contributeur
    auteur_nom: Mapped[str] = mapped_column(String(120), nullable=False)
    auteur_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    auteur_role: Mapped[str] = mapped_column(String(50), default="Apprenant")  # 'Apprenant', 'Parent', 'Enseignant', 'Griot'

    # Nature du contenu
    type_contenu: Mapped[str] = mapped_column(String(30), nullable=False, index=True)  # 'proverbe', 'devinette', 'conte', 'patronyme'

    # Données culturelles
    texte: Mapped[str] = mapped_column(Text, nullable=False)
    texte_original: Mapped[str | None] = mapped_column(Text, nullable=True)  # Version Bambara, Peul, etc.
    signification: Mapped[str] = mapped_column(Text, nullable=False)
    morale: Mapped[str | None] = mapped_column(String(255), nullable=True)   # Ou réponse à la devinette
    origine: Mapped[str] = mapped_column(String(150), default="Tradition Orale")
    theme: Mapped[str] = mapped_column(String(80), default="Sagesse & Culture")
    region_id: Mapped[str] = mapped_column(String(50), default="bamako")
    region_nom: Mapped[str] = mapped_column(String(100), default="Tout le Mali")
    
    # Médias & Données multimédias étendues
    titre: Mapped[str | None] = mapped_column(String(150), nullable=True)           # Pour les monuments, contes, cités
    photo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)       # Pour les photos de sites, visages ou manuscrits
    source_temoin: Mapped[str | None] = mapped_column(String(150), nullable=True)  # Ex: "Mon grand-père à Bandiagara"
    audio_url: Mapped[str | None] = mapped_column(String(255), nullable=True)       # Enregistrement vocal
    donnees_supplementaires_json: Mapped[str | None] = mapped_column(Text, nullable=True) # JSON flexible (GPS, totem, variantes, etc.)

    # Workflow de validation
    statut: Mapped[str] = mapped_column(String(30), default="EN_ATTENTE", index=True)  # 'EN_ATTENTE', 'APPROUVE', 'REJETE'
    motif_moderation: Mapped[str | None] = mapped_column(Text, nullable=True)
    traite_par_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    
    # Récompenses gamification
    xp_attribues: Mapped[int] = mapped_column(Integer, default=50)
    pieces_attribuees: Mapped[int] = mapped_column(Integer, default=25)

    # Horodatage
    date_soumission: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)
    date_moderation: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class CultureNom(Base):
    __tablename__ = "culture_noms"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)  # ex: 'nom_keita', 'prenom_fatoumata'
    nom: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    nom_normalise: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="nom")  # 'nom' ou 'prenom'
    ethnie_ou_region: Mapped[str] = mapped_column(String(150), nullable=False)
    signification: Mapped[str] = mapped_column(Text, nullable=False)
    clan_role: Mapped[str] = mapped_column(String(200), nullable=False)
    totem: Mapped[str] = mapped_column(String(150), nullable=False)  # Tanan ancestral
    senankouya: Mapped[str] = mapped_column(String(255), nullable=False)  # Cousinage à plaisanterie
    devise_ou_louange: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Louange griotique
    anecdote: Mapped[str] = mapped_column(Text, nullable=False)
    variantes_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON list
    date_creation: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)


# ==============================================================================
# MODÈLES MODULE F & G : PORTEFEUILLE CENTRAL, TRANSACTIONS & RETRAITS MOBILE MONEY
# ==============================================================================

class Portefeuille(Base):
    __tablename__ = "portefeuilles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    apprenant_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    solde_pieces: Mapped[int] = mapped_column(Integer, default=0)
    pieces_reservees: Mapped[int] = mapped_column(Integer, default=0)  # Réservées pour un retrait en attente
    pieces_retirees_total: Mapped[int] = mapped_column(Integer, default=0)
    argent_total_gagne_fcfa: Mapped[int] = mapped_column(Integer, default=0)
    date_creation: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)
    date_mise_a_jour: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)

    transactions: Mapped[list["TransactionPiece"]] = relationship("TransactionPiece", back_populates="portefeuille")


class TransactionPiece(Base):
    __tablename__ = "transactions_pieces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    portefeuille_id: Mapped[str] = mapped_column(String(36), ForeignKey("portefeuilles.id"), index=True, nullable=False)
    apprenant_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    montant: Mapped[int] = mapped_column(Integer, nullable=False)  # Positif (crédit) ou négatif (débit)
    type_operation: Mapped[str] = mapped_column(String(40), nullable=False)  # 'CREDIT', 'DEBIT_RESERVATION', 'DEBIT_FINAL', 'REMBOURSEMENT'
    origine: Mapped[str] = mapped_column(String(50), nullable=False)  # 'DEFI_NATIONAL', 'BATTLE_DUEL', 'CHALLENGE_SOLO', 'SESSION_GRIN', 'BONUS_FIDELITE', 'CULTURE_VALIDEE', 'RETRAIT_MOBILE_MONEY', 'PARRAINAGE'
    idempotency_key: Mapped[str | None] = mapped_column(String(100), unique=True, index=True, nullable=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    metadonnees_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    solde_apres: Mapped[int] = mapped_column(Integer, nullable=False)
    date_creation: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)

    portefeuille: Mapped["Portefeuille"] = relationship("Portefeuille", back_populates="transactions")


class DemandeRetrait(Base):
    __tablename__ = "demandes_retrait"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    apprenant_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    numero_transaction_ref: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    pieces_debitees: Mapped[int] = mapped_column(Integer, nullable=False)
    montant_fcfa: Mapped[int] = mapped_column(Integer, nullable=False)
    operateur: Mapped[str] = mapped_column(String(30), nullable=False)  # 'ORANGE_MONEY', 'MOOV_MONEY', 'WAVE'
    numero_telephone: Mapped[str] = mapped_column(String(30), nullable=False)
    nom_titulaire: Mapped[str] = mapped_column(String(100), nullable=False)
    statut: Mapped[str] = mapped_column(String(40), default="EN_ATTENTE", index=True)  # 'EN_ATTENTE', 'EN_VERIFICATION', 'ACCEPTEE', 'REJETEE', 'EN_COURS_DE_PAIEMENT', 'PAYEE', 'ECHEC'
    motif_rejet: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_operateur: Mapped[str | None] = mapped_column(String(100), nullable=True)
    traite_par_admin_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    date_demande: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)
    date_traitement: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    date_paiement: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ip_demandeur: Mapped[str | None] = mapped_column(String(45), nullable=True)


# ==============================================================================
# MODÈLES MODULE A : PARRAINAGE & RÉCOMPENSES
# ==============================================================================

class ParrainageCode(Base):
    __tablename__ = "parrainage_codes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    apprenant_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    total_filleuls: Mapped[int] = mapped_column(Integer, default=0)
    total_filleuls_actifs: Mapped[int] = mapped_column(Integer, default=0)
    pieces_gagnees_parrainage: Mapped[int] = mapped_column(Integer, default=0)
    date_creation: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)


class ParrainageFilleul(Base):
    __tablename__ = "parrainage_filleuls"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    parrain_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    filleul_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    code_utilise: Mapped[str] = mapped_column(String(20), nullable=False)
    statut: Mapped[str] = mapped_column(String(30), default="EN_ATTENTE")  # 'EN_ATTENTE', 'VALIDE', 'SUSPECT_REJETE'
    recompense_attribuee: Mapped[bool] = mapped_column(Boolean, default=False)
    date_inscription: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)
    date_validation: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


# ==============================================================================
# MODÈLES MODULE H : ABONNEMENTS & DROITS PREMIUM
# ==============================================================================

class OffreAbonnement(Base):
    __tablename__ = "offres_abonnement"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # 'mensuel_standard', 'trimestriel', 'annuel'
    titre: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    prix_fcfa: Mapped[int] = mapped_column(Integer, nullable=False)
    duree_jours: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    avantages_json: Mapped[str] = mapped_column(Text, nullable=False)
    actif: Mapped[bool] = mapped_column(Boolean, default=True)


class AbonnementUtilisateur(Base):
    __tablename__ = "abonnements_utilisateurs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    apprenant_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    offre_id: Mapped[str] = mapped_column(String(50), nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="ACHAT_MOBILE_MONEY")  # 'ACHAT_MOBILE_MONEY', 'PARRAINAGE_OFFERT', 'ADMIN_GRATIFIE'
    statut: Mapped[str] = mapped_column(String(30), default="ACTIF", index=True)  # 'ACTIF', 'EXPIRE', 'RESILIE'
    date_debut: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)
    date_expiration: Mapped[datetime | None] = mapped_column(DateTime, nullable=False)
    date_creation: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)


# ==============================================================================
# MODÈLES MODULE B : DÉFI NATIONAL DU PROGRAMME MALIEN
# ==============================================================================

class DefiNational(Base):
    __tablename__ = "defis_nationaux"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    titre: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    classe: Mapped[str] = mapped_column(String(30), nullable=False, index=True)  # '12eme', '10eme', 'TSE', etc.
    matiere: Mapped[str] = mapped_column(String(80), nullable=False)
    statut: Mapped[str] = mapped_column(String(30), default="EN_COURS", index=True)  # 'A_VENIR', 'EN_COURS', 'CLOTURE'
    date_debut: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)
    date_fin: Mapped[datetime | None] = mapped_column(DateTime, nullable=False)
    duree_minutes: Mapped[int] = mapped_column(Integer, default=15)
    recompense_pieces_premier: Mapped[int] = mapped_column(Integer, default=500)
    recompense_pieces_top10: Mapped[int] = mapped_column(Integer, default=250)
    recompense_pieces_participation: Mapped[int] = mapped_column(Integer, default=50)
    questions_json: Mapped[str] = mapped_column(Text, nullable=False)  # Questions officielles
    date_creation: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)

    participations: Mapped[list["ParticipationDefiNational"]] = relationship("ParticipationDefiNational", back_populates="defi")


class ParticipationDefiNational(Base):
    __tablename__ = "participations_defi_national"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    defi_id: Mapped[str] = mapped_column(String(36), ForeignKey("defis_nationaux.id"), index=True, nullable=False)
    apprenant_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    apprenant_nom: Mapped[str] = mapped_column(String(100), nullable=False)
    apprenant_classe: Mapped[str] = mapped_column(String(30), nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0)
    temps_secondes: Mapped[int] = mapped_column(Integer, default=0)
    pieces_remportees: Mapped[int] = mapped_column(Integer, default=0)
    xp_remportes: Mapped[int] = mapped_column(Integer, default=0)
    rang_final: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reponses_soumises_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    soumis_a: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)

    defi: Mapped["DefiNational"] = relationship("DefiNational", back_populates="participations")


# ==============================================================================
# JOURNAL D'AUDIT SÉCURISÉ (ADMINISTRATION & FINANCES)
# ==============================================================================

class JournalAuditSecurite(Base):
    __tablename__ = "journaux_audit_securite"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    admin_id_ou_systeme: Mapped[str] = mapped_column(String(100), nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 'RETRAIT_APPROUVE', 'RETRAIT_REJETE', 'RETRAIT_PAYE', 'RESET_CLASSEMENT', etc.
    entite_cible: Mapped[str] = mapped_column(String(50), nullable=False)
    entite_id: Mapped[str] = mapped_column(String(100), nullable=False)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    adresse_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    date_action: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)


