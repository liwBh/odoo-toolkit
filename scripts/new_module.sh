#!/usr/bin/env bash
set -euo pipefail

MOD="${1:-}"
DESC="${2:-$MOD}"
CATEGORY="${3:-Uncategorized}"
AUTHOR="${4:-}"
PYTHON="${PYTHON:-.venv/bin/python}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -z "$MOD" ]; then
    echo "Uso: make new-module name=nombre_modulo [description=\"Descripción\"] [category=\"Categoría\"] [author=\"Autor\"]"
    exit 1
fi

if [[ ! "$MOD" =~ ^[a-z][a-z0-9_]*$ ]]; then
    echo "Error: name debe ser snake_case (minúsculas, números, _) — ej: courses_info"
    exit 1
fi

DIR="$("$PYTHON" "$SCRIPT_DIR/_addons.py" new "$MOD")"
if [ -z "$DIR" ]; then
    echo "Error: no se pudo resolver directorio destino vía addons_path"
    exit 1
fi
if [ -e "$DIR" ]; then
    echo "Error: $DIR ya existe"
    exit 1
fi

if [[ "$MOD" == *_* ]]; then
    MODEL="${MOD//_/.}"
else
    MODEL="$MOD.info"
fi
CLASS=$(echo "$MOD" | awk -F'_' '{for(i=1;i<=NF;i++){$i=toupper(substr($i,1,1)) substr($i,2)}}1' OFS='')

mkdir -p "$DIR/models" "$DIR/views" "$DIR/security" "$DIR/controllers" "$DIR/wizards" \
         "$DIR/static/src/js" "$DIR/static/src/css" "$DIR/static/src/xml"

cat > "$DIR/__init__.py" <<EOF
from . import models
from . import controllers
from . import wizards
EOF

cat > "$DIR/__manifest__.py" <<EOF
{
    "name": "$DESC",
    "summary": "$DESC",
    "description": "$DESC",
    "category": "$CATEGORY",
    "author": "$AUTHOR",
    "version": "19.0.1.0.0",
    "application": True,
    "depends": ["base", "web", "website"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/view_list.xml",
        "views/view_form.xml",
        "views/view_menu.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "$MOD/static/src/js/**/*.js",
            "$MOD/static/src/css/**/*.css",
            "$MOD/static/src/xml/**/*.xml",
        ]
    },
}
EOF

echo "from . import $MOD" > "$DIR/models/__init__.py"

touch "$DIR/controllers/__init__.py" "$DIR/wizards/__init__.py"

cat > "$DIR/controllers/$MOD.py" <<EOF
# CRUD base para $MODEL — comentado, no registra ninguna ruta hasta que lo actives
# (y esta carpeta no se importa sola: agregá "from . import $MOD" a controllers/__init__.py
# cuando lo uses). Descomentá el/los métodos que necesites y ajustá auth/type/csrf
# según el caso real (ver Apuntes.md sección 15).
#
# import json
#
# from odoo.http import request, route, Controller
#
#
# class ${CLASS}Controller(Controller):
#
#     @route("/$MOD", auth="user", type="http", methods=["GET"])
#     def ${MOD}_list(self, **kwargs):
#         records = request.env["$MODEL"].search([])
#         return request.make_response(
#             json.dumps([{"id": r.id, "name": r.name} for r in records])
#         )
#
#     @route("/$MOD/<int:record_id>", auth="user", type="http", methods=["GET"])
#     def ${MOD}_get(self, record_id, **kwargs):
#         record = request.env["$MODEL"].browse(record_id)
#         if not record.exists():
#             return request.make_response(json.dumps({"error": "not found"}), status=404)
#         return request.make_response(json.dumps({"id": record.id, "name": record.name}))
#
#     @route("/$MOD", auth="user", type="http", csrf=False, methods=["POST"])
#     def ${MOD}_create(self, **kwargs):
#         record = request.env["$MODEL"].create({"name": kwargs.get("name")})
#         return request.make_response(json.dumps({"id": record.id}), status=201)
#
#     @route("/$MOD/<int:record_id>", auth="user", type="http", csrf=False, methods=["DELETE"])
#     def ${MOD}_delete(self, record_id, **kwargs):
#         request.env["$MODEL"].browse(record_id).unlink()
#         return request.make_response(json.dumps({"status": "deleted"}))
#
#     # Página website (request.render) — necesita un template QWeb server-side
#     # (<odoo><template id="...">, no el stub OWL de static/src/xml/templates.xml).
#     # Creá views/page_$MOD.xml con <template id="page_$MOD"> (mismo id que el
#     # archivo, ver 9.1/15.8) y agregalo a "data" antes de descomentar esto.
#     @route("/$MOD/view", auth="public", type="http", csrf=False, website=True)
#     def ${MOD}_view(self, **kwargs):
#         return request.render("$MOD.page_$MOD")
EOF

cat > "$DIR/static/src/js/main.js" <<EOF
/** @odoo-module **/

// Base rápida para un componente OWL público — comentado, no registra nada hasta
// que lo actives. Usa el template stub de static/src/xml/templates.xml ($MOD.placeholder)
// y se monta con <owl-component name="$MOD.component"/> en cualquier vista website
// (ver Apuntes.md sección 15.8/9.1).
//
// import { Component } from "@odoo/owl";
// import { registry } from "@web/core/registry";
//
// export class ${CLASS}Component extends Component {
//     static template = "$MOD.placeholder";
//
//     setup() {
//         console.log("Loading component...");
//     }
// }
//
// registry.category("public_components").add("$MOD.component", ${CLASS}Component);
EOF

cat > "$DIR/static/src/css/main.css" <<EOF
/* $DESC */
EOF

cat > "$DIR/static/src/xml/templates.xml" <<EOF
<?xml version="1.0" encoding="UTF-8" ?>
<templates>
    <t t-name="$MOD.placeholder">
        <div/>
    </t>
</templates>
EOF

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
              groups="$MOD.group_${MOD}_access"
    />
</odoo>
EOF

cat > "$DIR/security/security.xml" <<EOF
<?xml version="1.0" encoding="UTF-8" ?>
<odoo>
    <!-- Categoria de seguridad -->
    <record id="category_${MOD}_security" model="ir.module.category">
        <field name="name">$DESC</field>
        <field name="description">Grupo de seguridad para el modulo $DESC</field>
    </record>

    <!-- Grupo de privilegios -->
    <record id="privilege_$MOD" model="res.groups.privilege">
        <field name="name">$DESC</field>
        <field name="category_id" ref="$MOD.category_${MOD}_security"/>
    </record>

    <!-- Grupo de seguridad -->
    <record id="group_${MOD}_access" model="res.groups">
        <field name="name">Acceso a $DESC</field>
        <field name="privilege_id" ref="$MOD.privilege_$MOD"/>
        <!-- admin queda adentro del grupo para no bloquearlo al instalar -->
        <field name="user_ids" eval="[(4, ref('base.user_admin'))]"/>
    </record>
</odoo>
EOF

MODEL_US="${MODEL//./_}"
cat > "$DIR/security/ir.model.access.csv" <<EOF
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_$MODEL_US,access.$MODEL,model_$MODEL_US,$MOD.group_${MOD}_access,1,1,1,1
EOF

if [ -f "modules.txt" ]; then
    grep -qx "$MOD" modules.txt || echo "$MOD" >> modules.txt
else
    echo "$MOD" > modules.txt
fi

echo ""
echo "Módulo '$MOD' creado en $DIR/"
echo "Agregado a modules.txt"
echo "Corré 'make install-module module=$MOD' para instalarlo (make dev no lo instala solo — recién actualiza módulos ya instalados)."