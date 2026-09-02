"""
Modèles de données SQLAlchemy pour la base alta_db.
"""

from datetime import datetime
from typing import List, Optional
import uuid
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

from backend.src.db.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    mot_de_passe_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(30), nullable=False, default="parent")  # 'admin_ecole', 'parent', 'enseignant'
    nom_complet: Mapped[str] = mapped_column(String(120), nullable=False)
    avatar: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    date_creation: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    dernier_acces: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    actif: Mapped[bool] = mapped_column(Boolean, default=True)


class Etablissement(Base):
    __tablename__ = "etablissements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    nom: Mapped[str] = mapped_column(String(150), nullable=False)
    type_etablissement: Mapped[str] = mapped_column(String(50), default="Lycée")  # 'Lycée', 'Collège', 'Complexe Scolaire'
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    adresse: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ville: Mapped[str] = mapped_column(String(100), default="Bamako")
    pays: Mapped[str] = mapped_column(String(100), default="Mali")
    telephone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    date_creation: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    boitiers: Mapped[List["Boitier"]] = relationship("Boitier", back_populates="etablissement")
    apprenants: Mapped[List["Apprenant"]] = relationship("Apprenant", back_populates="etablissement")


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
    derniere_synchro: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    date_activation: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    etablissement_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("etablissements.id"), nullable=True)
    enfant_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    etablissement: Mapped[Optional["Etablissement"]] = relationship("Etablissement", back_populates="boitiers")
    apprenants: Mapped[List["Apprenant"]] = relationship("Apprenant", back_populates="boitier")


class Apprenant(Base):
    __tablename__ = "apprenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    nom: Mapped[str] = mapped_column(String(80), nullable=False)
    prenom: Mapped[str] = mapped_column(String(80), nullable=False)
    matricule: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    classe: Mapped[str] = mapped_column(String(20), nullable=False, default="11eme")  # '10eme', '11eme', '12eme'
    serie: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, default="11S")       # '11S', '11L', 'TSE', 'TSExp', etc.
    niveau_maitrise: Mapped[float] = mapped_column(Float, default=74.5)                  # Pourcentage global
    temps_total_sec: Mapped[int] = mapped_column(Integer, default=14200)
    questions_posees: Mapped[int] = mapped_column(Integer, default=42)
    dernier_acces: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    date_inscription: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    photo_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    etablissement_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("etablissements.id"), nullable=True)
    boitier_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("boitiers.id"), nullable=True)

    etablissement: Mapped[Optional["Etablissement"]] = relationship("Etablissement", back_populates="apprenants")
    boitier: Mapped[Optional["Boitier"]] = relationship("Boitier", back_populates="apprenants")
    sessions: Mapped[List["SessionApprentissage"]] = relationship("SessionApprentissage", back_populates="apprenant")
    alertes: Mapped[List["AlertePedagogique"]] = relationship("AlertePedagogique", back_populates="apprenant")


class SessionApprentissage(Base):
    __tablename__ = "sessions_apprentissage"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    apprenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("apprenants.id"), nullable=False)
    boitier_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("boitiers.id"), nullable=True)
    matiere: Mapped[str] = mapped_column(String(50), nullable=False, default="biologie")
    chapitre: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notion: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    date_debut: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    date_fin: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    duree_sec: Mapped[int] = mapped_column(Integer, default=900)
    questions_count: Mapped[int] = mapped_column(Integer, default=5)
    reussite_taux: Mapped[float] = mapped_column(Float, default=80.0)

    apprenant: Mapped[Optional["Apprenant"]] = relationship("Apprenant", back_populates="sessions")
    interactions: Mapped[List["InteractionPedagogique"]] = relationship("InteractionPedagogique", back_populates="session")


class InteractionPedagogique(Base):
    __tablename__ = "interactions_pedagogiques"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    session_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("sessions_apprentissage.id"), nullable=True)
    apprenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    reponse: Mapped[str] = mapped_column(Text, nullable=False)
    matiere: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notion: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    intention: Mapped[str] = mapped_column(String(50), default="explanation")
    difficulte: Mapped[str] = mapped_column(String(30), default="moyen")
    succes: Mapped[bool] = mapped_column(Boolean, default=True)
    timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped[Optional["SessionApprentissage"]] = relationship("SessionApprentissage", back_populates="interactions")


class AvatarPedagogique(Base):
    __tablename__ = "avatars_pedagogiques"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    nom: Mapped[str] = mapped_column(String(80), nullable=False)
    matiere: Mapped[str] = mapped_column(String(80), nullable=False, default="Toutes matières")
    style_pedagogique: Mapped[str] = mapped_column(String(120), default="Bienveillant, rigoureux et interactif")
    voix_tts: Mapped[str] = mapped_column(String(60), default="vivienne")
    photo_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    video_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    audio_sample_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    audio_file_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    actif: Mapped[bool] = mapped_column(Boolean, default=True)
    par_defaut: Mapped[bool] = mapped_column(Boolean, default=False)
    landmarks_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    viseme_photos_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    date_creation: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)


class AlertePedagogique(Base):
    __tablename__ = "alertes_pedagogiques"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    apprenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("apprenants.id"), nullable=False)
    titre: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    type_alerte: Mapped[str] = mapped_column(String(50), default="difficulte_recurrente")  # 'difficulte_recurrente', 'inactivite', 'reussite_remarquable'
    gravite: Mapped[str] = mapped_column(String(20), default="moyenne")                   # 'faible', 'moyenne', 'elevee'
    matiere: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    resolu: Mapped[bool] = mapped_column(Boolean, default=False)
    date_creation: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

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
    notions_difficiles_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array


class SeanceRevisionModel(Base):
    __tablename__ = "seances_revision"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    titre: Mapped[str] = mapped_column(String(150), nullable=False)
    matiere: Mapped[str] = mapped_column(String(50), nullable=False)
    jour: Mapped[str] = mapped_column(String(10), nullable=False)  # 'YYYY-MM-DD'
    heure_debut: Mapped[str] = mapped_column(String(10), nullable=False)  # 'HH:MM'
    heure_fin: Mapped[str] = mapped_column(String(10), nullable=False)
    duree_minutes: Mapped[int] = mapped_column(Integer, default=45)
    commentaire: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    statut: Mapped[str] = mapped_column(String(30), default="PROGRAMMÉE")
    rappel_minutes_avant: Mapped[int] = mapped_column(Integer, default=30)
    date_creation: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)


class RapportModel(Base):
    __tablename__ = "rapports_pedagogiques"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    etablissement_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    titre: Mapped[str] = mapped_column(String(150), nullable=False)
    periode: Mapped[str] = mapped_column(String(80), default="Semaine en cours")
    date_debut: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    date_fin: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    type_fichier: Mapped[str] = mapped_column(String(20), default="pdf")  # 'pdf', 'excel'
    statut: Mapped[str] = mapped_column(String(30), default="genere")
    taille_fichier_octets: Mapped[int] = mapped_column(Integer, default=450000)
    url_telechargement: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    date_generation: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
