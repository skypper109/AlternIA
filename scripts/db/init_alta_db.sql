-- =============================================================================
-- BASE DE DONNÉES OFFICIELLE : alta_db (AlternIA Box)
-- Système de gestion des établissements, boîtiers, apprenants et tuteurs IA
-- =============================================================================

CREATE DATABASE IF NOT EXISTS alta_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE alta_db;

-- 1. Table des utilisateurs (Établissements & Parents)
CREATE TABLE IF NOT EXISTS utilisateurs (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(120) NOT NULL UNIQUE,
    mot_de_passe_hash VARCHAR(255) NULL,
    role VARCHAR(30) NOT NULL DEFAULT 'parent',
    nom_complet VARCHAR(120) NOT NULL,
    avatar VARCHAR(255) NULL,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
    dernier_acces DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    actif BOOLEAN DEFAULT TRUE,
    INDEX idx_user_email (email),
    INDEX idx_user_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Table des établissements scolaires
CREATE TABLE IF NOT EXISTS etablissements (
    id VARCHAR(36) PRIMARY KEY,
    nom VARCHAR(150) NOT NULL,
    type_etablissement VARCHAR(50) DEFAULT 'Lycée',
    code VARCHAR(50) NOT NULL UNIQUE,
    adresse VARCHAR(255) NULL,
    ville VARCHAR(100) DEFAULT 'Bamako',
    pays VARCHAR(100) DEFAULT 'Mali',
    telephone VARCHAR(50) NULL,
    email VARCHAR(120) NULL,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_etab_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Table des boîtiers physiques (AlternIA Box)
CREATE TABLE IF NOT EXISTS boitiers (
    id VARCHAR(36) PRIMARY KEY,
    numero_serie VARCHAR(80) NOT NULL UNIQUE,
    modele VARCHAR(80) DEFAULT 'AlternIA Box v2.0',
    firmware VARCHAR(50) DEFAULT 'v2.0-LocalEdge',
    statut VARCHAR(30) DEFAULT 'en_ligne',
    batterie INT DEFAULT 95,
    stockage_go FLOAT DEFAULT 32.0,
    stockage_utilise_go FLOAT DEFAULT 8.4,
    wifi_ssid VARCHAR(100) DEFAULT 'AlternIA-Box-WiFi',
    ip_locale VARCHAR(45) DEFAULT '192.168.4.1',
    derniere_synchro DATETIME DEFAULT CURRENT_TIMESTAMP,
    date_activation DATETIME DEFAULT CURRENT_TIMESTAMP,
    etablissement_id VARCHAR(36) NULL,
    enfant_id VARCHAR(36) NULL,
    INDEX idx_boitier_sn (numero_serie),
    INDEX idx_boitier_statut (statut),
    FOREIGN KEY (etablissement_id) REFERENCES etablissements(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Table des apprenants / élèves
CREATE TABLE IF NOT EXISTS apprenants (
    id VARCHAR(36) PRIMARY KEY,
    nom VARCHAR(80) NOT NULL,
    prenom VARCHAR(80) NOT NULL,
    matricule VARCHAR(50) NOT NULL UNIQUE,
    classe VARCHAR(20) NOT NULL DEFAULT '11eme',
    serie VARCHAR(30) NULL DEFAULT '11S',
    niveau_maitrise FLOAT DEFAULT 75.0,
    temps_total_sec INT DEFAULT 0,
    questions_posees INT DEFAULT 0,
    dernier_acces DATETIME DEFAULT CURRENT_TIMESTAMP,
    date_inscription DATETIME DEFAULT CURRENT_TIMESTAMP,
    photo_url VARCHAR(255) NULL,
    etablissement_id VARCHAR(36) NULL,
    boitier_id VARCHAR(36) NULL,
    INDEX idx_apprenant_matricule (matricule),
    INDEX idx_apprenant_classe (classe),
    FOREIGN KEY (etablissement_id) REFERENCES etablissements(id) ON DELETE SET NULL,
    FOREIGN KEY (boitier_id) REFERENCES boitiers(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Table des sessions d'apprentissage
CREATE TABLE IF NOT EXISTS sessions_apprentissage (
    id VARCHAR(36) PRIMARY KEY,
    apprenant_id VARCHAR(36) NOT NULL,
    boitier_id VARCHAR(36) NULL,
    matiere VARCHAR(50) NOT NULL,
    chapitre VARCHAR(100) NULL,
    notion VARCHAR(100) NULL,
    date_debut DATETIME DEFAULT CURRENT_TIMESTAMP,
    date_fin DATETIME DEFAULT CURRENT_TIMESTAMP,
    duree_sec INT DEFAULT 0,
    questions_count INT DEFAULT 0,
    reussite_taux FLOAT DEFAULT 0.0,
    INDEX idx_session_apprenant (apprenant_id),
    FOREIGN KEY (apprenant_id) REFERENCES apprenants(id) ON DELETE CASCADE,
    FOREIGN KEY (boitier_id) REFERENCES boitiers(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Table des interactions pédagogiques (Questions / Réponses)
CREATE TABLE IF NOT EXISTS interactions_pedagogiques (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NULL,
    apprenant_id VARCHAR(36) NOT NULL,
    question TEXT NOT NULL,
    reponse TEXT NOT NULL,
    matiere VARCHAR(50) NULL,
    notion VARCHAR(100) NULL,
    intention VARCHAR(50) DEFAULT 'explanation',
    difficulte VARCHAR(30) DEFAULT 'moyen',
    succes BOOLEAN DEFAULT TRUE,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_inter_apprenant (apprenant_id),
    FOREIGN KEY (session_id) REFERENCES sessions_apprentissage(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Table des avatars et personnalités pédagogiques (avec Vivienne)
CREATE TABLE IF NOT EXISTS avatars_pedagogiques (
    id VARCHAR(36) PRIMARY KEY,
    nom VARCHAR(80) NOT NULL,
    matiere VARCHAR(80) NOT NULL DEFAULT 'Toutes matières',
    style_pedagogique VARCHAR(120) DEFAULT 'Bienveillant et interactif',
    voix_tts VARCHAR(60) DEFAULT 'vivienne',
    photo_url VARCHAR(255) NULL,
    audio_sample_url VARCHAR(255) NULL,
    audio_file_name VARCHAR(120) NULL,
    actif BOOLEAN DEFAULT TRUE,
    par_defaut BOOLEAN DEFAULT FALSE,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Table des alertes pédagogiques
CREATE TABLE IF NOT EXISTS alertes_pedagogiques (
    id VARCHAR(36) PRIMARY KEY,
    apprenant_id VARCHAR(36) NOT NULL,
    titre VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    type_alerte VARCHAR(50) DEFAULT 'difficulte_recurrente',
    gravite VARCHAR(20) DEFAULT 'moyenne',
    matiere VARCHAR(50) NULL,
    resolu BOOLEAN DEFAULT FALSE,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_alerte_apprenant (apprenant_id),
    INDEX idx_alerte_resolu (resolu),
    FOREIGN KEY (apprenant_id) REFERENCES apprenants(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. Table des statistiques agrégées
CREATE TABLE IF NOT EXISTS statistiques_pedagogiques (
    id VARCHAR(36) PRIMARY KEY,
    date_jour VARCHAR(10) NOT NULL,
    classe VARCHAR(20) NOT NULL,
    matiere VARCHAR(50) NOT NULL,
    total_interactions INT DEFAULT 0,
    total_temps_sec INT DEFAULT 0,
    taux_comprehension FLOAT DEFAULT 75.0,
    notions_difficiles_json TEXT NULL,
    INDEX idx_stat_date (date_jour),
    INDEX idx_stat_classe (classe)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- Données initiales de démonstration
-- -----------------------------------------------------------------------------

INSERT INTO utilisateurs (id, email, role, nom_complet, actif)
VALUES 
    ('usr-directeur', 'directeur@altern.ia', 'admin_ecole', 'Directeur', TRUE),
    ('usr-parent', 'parent@altern.ia', 'parent', 'Parent', TRUE),
    ('usr-admin', 'admin@altern.ia', 'admin_ecole', 'Administrateur AlternIA', TRUE)
ON DUPLICATE KEY UPDATE nom_complet=VALUES(nom_complet);

INSERT INTO boitiers (id, numero_serie, modele, statut, batterie, stockage_go, stockage_utilise_go, wifi_ssid, etablissement_id)
VALUES 
    ('box-alta-01', 'ALT-BOX-2026-001', 'AlternIA Box v2.0 (Raspberry Pi 5)', 'en_ligne', 98, 32.0, 8.6, 'AlternIA-Box-WiFi', 'etab-test-bamako')
ON DUPLICATE KEY UPDATE batterie=VALUES(batterie);

INSERT INTO avatars_pedagogiques (id, nom, matiere, style_pedagogique, voix_tts, actif, par_defaut)
VALUES 
    ('avatar-vivienne', 'Professeure Vivienne', 'SVT & Sciences Naturelles', 'Chaleureuse, bienveillante et explicite avec exemples concrets', 'vivienne', TRUE, TRUE)
ON DUPLICATE KEY UPDATE nom=VALUES(nom);
