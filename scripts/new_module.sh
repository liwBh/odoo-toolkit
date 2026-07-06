#!/usr/bin/env bash
set -euo pipefail

MOD="${1:-}"
DESC="${2:-$MOD}"
CATEGORY="${3:-Uncategorized}"
ADDONS_DIR="extra_addons"

if [ -z "$MOD" ]; then
    echo "Uso: make new-module name=nombre_modulo [description=\"Descripción\"] [category=\"Categoría\"]"
    exit 1
fi

if [[ ! "$MOD" =~ ^[a-z][a-z0-9_]*$ ]]; then
    echo "Error: name debe ser snake_case (minúsculas, números, _) — ej: courses_info"
    exit 1
fi

DIR="$ADDONS_DIR/$MOD"
if [ -e "$DIR" ]; then
    echo "Error: $DIR ya existe"
    exit 1
fi

MODEL="${MOD//_/.}"
CLASS=$(echo "$MOD" | awk -F'_' '{for(i=1;i<=NF;i++){$i=toupper(substr($i,1,1)) substr($i,2)}}1' OFS='')

mkdir -p "$DIR/models" "$DIR/views" "$DIR/security"

echo "from . import models" > "$DIR/__init__.py"

cat > "$DIR/__manifest__.py" <<EOF
{
    "name": "$DESC",
    "category": "$CATEGORY",
    "author": "",
    "version": "19.0.1.0.0",
    "application": True,
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "views/view_list.xml",
        "views/view_form.xml",
        "views/view_menu.xml",
    ],
}
EOF

echo "from . import $MOD" > "$DIR/models/__init__.py"

cat > "$DIR/models/$MOD.py" <<EOF
from odoo import fields, models


class $CLASS(models.Model):
    _name = "$MODEL"
    _description = "$DESC"

    name = fields.Char(string="Nombre", required=True)
EOF

cat > "$DIR/views/view_list.xml" <<EOF
<?xml version="1.0" encoding="UTF-8" ?>
<odoo>
    <record id="view_list_$MOD" model="ir.ui.view">
        <field name="name">$MOD.list</field>
        <field name="model">$MODEL</field>
        <field name="arch" type="xml">
            <list>
                <field name="name"/>
            </list>
        </field>
    </record>
</odoo>
EOF

cat > "$DIR/views/view_form.xml" <<EOF
<?xml version="1.0" encoding="UTF-8" ?>
<odoo>
    <record id="view_form_$MOD" model="ir.ui.view">
        <field name="name">$MOD.form</field>
        <field name="model">$MODEL</field>
        <field name="arch" type="xml">
            <form>
                <sheet>
                    <group>
                        <field name="name"/>
                    </group>
                </sheet>
            </form>
        </field>
    </record>
</odoo>
EOF

cat > "$DIR/views/view_menu.xml" <<EOF
<?xml version="1.0" encoding="UTF-8" ?>
<odoo>
    <record id="action_$MOD" model="ir.actions.act_window">
        <field name="name">$DESC</field>
        <field name="res_model">$MODEL</field>
        <field name="view_mode">list,form</field>
    </record>

    <menuitem id="menu_$MOD"
              action="action_$MOD"
              name="$DESC"
    />
</odoo>
EOF

cat > "$DIR/security/ir.model.access.csv" <<EOF
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_$MOD,access_$MOD,model_$MOD,base.group_user,1,1,1,1
EOF

if [ -f "modules.txt" ]; then
    grep -qx "$MOD" modules.txt || echo "$MOD" >> modules.txt
else
    echo "$MOD" > modules.txt
fi

echo ""
echo "Módulo '$MOD' creado en $DIR/"
echo "Agregado a modules.txt"
echo "Siguiente paso: make install-module module=$MOD"