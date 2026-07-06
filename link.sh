#!/usr/bin/env bash
# Conecta un proyecto Odoo a este toolkit via symlinks.
# Uso: ./link.sh /ruta/al/proyecto-odoo
set -euo pipefail

TOOLKIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-}"

if [ -z "$TARGET" ]; then
    echo "Uso: ./link.sh /ruta/al/proyecto-odoo"
    exit 1
fi

if [ ! -d "$TARGET" ]; then
    echo "Error: $TARGET no existe"
    exit 1
fi

cd "$TARGET"

for f in Apuntes.md Makefile scripts; do
    if [ -e "$f" ] && [ ! -L "$f" ]; then
        echo "Error: $TARGET/$f ya existe y no es symlink. Bórralo o muévelo antes de continuar."
        exit 1
    fi
done

ln -sf "$TOOLKIT_DIR/Apuntes.md" Apuntes.md
ln -sf "$TOOLKIT_DIR/Makefile" Makefile
ln -sf "$TOOLKIT_DIR/scripts" scripts

echo "Listo: $TARGET conectado a odoo-toolkit ($TOOLKIT_DIR)"