#!/bin/bash
# ==============================================================================
# Script d'Installation & Configuration MySQL pour AlternIA (alta_db)
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${GREEN}   🇲🇱  INSTALLATION & CONFIGURATION MYSQL POUR ALTERNIA (alta_db)  🇲🇱${NC}"
echo -e "${BLUE}==============================================================================${NC}"

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Veuillez exécuter ce script en root (sudo ./setup_mysql.sh)${NC}"
    exit 1
fi

REAL_USER=${SUDO_USER:-ubuntu}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

DB_NAME="alta_db"
DB_USER="alternia"
DB_PASS="skypper19"

echo -e "\n${BLUE}[1/4] Installation et activation de MySQL Server...${NC}"
apt-get update -y
apt-get install -y mysql-server

systemctl enable mysql
systemctl start mysql
echo "✅ Serveur MySQL actif et activé au démarrage de l'OS."

echo -e "\n${BLUE}[2/4] Création de la base de données '$DB_NAME' et de l'utilisateur '$DB_USER'...${NC}"
mysql -e "CREATE DATABASE IF NOT EXISTS ${DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -e "CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASS}';"
mysql -e "GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"
echo "✅ Base de données '$DB_NAME' et utilisateur configurés."

# Import du schéma initial si disponible
if [ -f "$APP_DIR/scripts/db/init_alta_db.sql" ]; then
    echo "📥 Importation du schéma officiel init_alta_db.sql..."
    mysql -u "${DB_USER}" -p"${DB_PASS}" "${DB_NAME}" < "$APP_DIR/scripts/db/init_alta_db.sql" || true
    echo "✅ Schéma SQL initial importé."
fi

echo -e "\n${BLUE}[3/4] Mise à jour du fichier .env avec DATABASE_URL...${NC}"
ENV_FILE="$APP_DIR/.env"
MYSQL_URL="mysql+pymysql://${DB_USER}:${DB_PASS}@localhost:3306/${DB_NAME}?charset=utf8mb4"

if [ -f "$ENV_FILE" ]; then
    if grep -q "DATABASE_URL=" "$ENV_FILE"; then
        sed -i "s|DATABASE_URL=.*|DATABASE_URL=${MYSQL_URL}|g" "$ENV_FILE"
    else
        echo -e "\n# Configuration Base de Données MySQL\nDATABASE_URL=${MYSQL_URL}" >> "$ENV_FILE"
    fi
else
    cat << EOF > "$ENV_FILE"
DATABASE_URL=${MYSQL_URL}
EOF
fi
chown "$REAL_USER:$REAL_USER" "$ENV_FILE"
echo "✅ DATABASE_URL configuré dans $ENV_FILE."

echo -e "\n${BLUE}[4/4] Synchronisation des tables et peuplement initial...${NC}"
if [ -d "$APP_DIR/.venv" ]; then
    sudo -u "$REAL_USER" "$APP_DIR/.venv/bin/python" "$APP_DIR/scripts/seed_db.py" || true
    echo "✅ Tables et données initiales synchronisées."
fi

# Redémarrage du backend pour prise en compte immédiate
if systemctl is-active --quiet alternia-backend.service; then
    echo "🔄 Redémarrage du backend AlternIA pour connexion à MySQL..."
    systemctl restart alternia-backend.service
fi

echo -e "\n${GREEN}==============================================================================${NC}"
echo -e "${GREEN}  🎉 MYSQL EST PRÊT ET CONNECTÉ À ALTERNIA AVEC SUCCÈS !                    ${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo -e "Informations de connexion locale :"
echo -e "  • Base : ${GREEN}${DB_NAME}${NC}"
echo -e "  • Utilisateur : ${GREEN}${DB_USER}${NC}"
echo -e "  • Mot de passe : ${GREEN}${DB_PASS}${NC}"
echo -e "  • URL SQLAlchemy : ${BLUE}${MYSQL_URL}${NC}"
echo -e "\nPour vous connecter en ligne de commande : ${YELLOW}mysql -u alternia -p alta_db${NC}"
