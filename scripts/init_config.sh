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

if [ -f "$CONF" ] && [ "$FORCE" != "1" ]; then
    echo "Error: $CONF ya existe. Usa force=1 para sobreescribir."
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