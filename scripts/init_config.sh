#!/usr/bin/env bash
set -euo pipefail

ADMIN_PASSWD="${1:-Admin1234}"
DB_HOST="${2:-localhost}"
DB_PORT="${3:-5432}"
DB_USER="${4:-odoo_user}"
DB_PASSWORD="${5:-$DB_USER}"
DB_NAME="${6:-odoo_db}"
FORCE="${7:-}"
HTTP_PORT="${8:-8069}"

CONF="odoo.conf"

RED='\033[31m'
BOLD='\033[1m'
RESET='\033[0m'

if [ -f "$CONF" ] && [ "$FORCE" != "1" ]; then
    echo ""
    echo -e "${RED}${BOLD}[init-config] ERROR: $CONF ya existe — NO se modificó nada.${RESET}"
    echo -e "${BOLD}Tus valores nuevos NO se aplicaron. Para sobreescribir agregá force=1:${RESET}"
    echo "  make init-config ... force=1"
    echo ""
    exit 1
fi

cat > "$CONF" <<EOF
[options]
admin_passwd = $ADMIN_PASSWD
db_host = $DB_HOST
db_port = $DB_PORT
db_user = $DB_USER
db_password = $DB_PASSWORD
db_name = $DB_NAME
addons_path = ./addons,./extra_addons
http_port = $HTTP_PORT
EOF

mkdir -p extra_addons

echo ""
echo "$CONF creado."
echo "Siguiente paso: make init-db"