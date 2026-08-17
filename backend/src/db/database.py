"""
Module de configuration et gestion de la base de données alta_db (MySQL & fallback SQLite).
"""

import logging
import os
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

logger = logging.getLogger("AlternIA.DB")

# Racine du projet et chemin vers la base de données
ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
SQLITE_FALLBACK_URL = f"sqlite:///{DATA_DIR}/alta_db.sqlite"

# URL MySQL par défaut pour alta_db
DEFAULT_MYSQL_URL = os.environ.get(
    "DATABASE_URL",
    "mysql+pymysql://root:skypper19@localhost:3306/alta_db?charset=utf8mb4"
)


class Base(DeclarativeBase):
    pass


def get_engine_and_url():
    """
    Tente d'initialiser le moteur MySQL (alta_db).
    Si le serveur MySQL est inaccessible ou non installé, bascule automatiquement sur SQLite.
    """
    target_url = DEFAULT_MYSQL_URL
    is_sqlite = "sqlite" in target_url

    if not is_sqlite:
        try:
            # Test de connexion rapide au serveur MySQL
            engine = create_engine(
                target_url,
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args={"connect_timeout": 2},
            )
            with engine.connect():
                logger.info(f"Connecté avec succès à la base de données MySQL : alta_db")
                return engine, target_url
        except Exception as exc:
            logger.warning(
                f"Serveur MySQL injoignable ({exc}). "
                f"Basculement automatique sur la base locale embarquée SQLite : {SQLITE_FALLBACK_URL}"
            )

    # Moteur SQLite de fallback
    engine = create_engine(
        SQLITE_FALLBACK_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )
    logger.info("Base de données SQLite active.")
    return engine, SQLITE_FALLBACK_URL


engine, ACTIVE_DATABASE_URL = get_engine_and_url()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """Dépendance FastAPI pour obtenir une session de base de données."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Crée toutes les tables et initialise les données de démarrage si nécessaire."""
    from backend.src.db import models, seed
    Base.metadata.create_all(bind=engine)
    seed.seed_initial_data(SessionLocal())
