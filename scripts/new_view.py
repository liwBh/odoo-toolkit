#!/usr/bin/env python3
"""
Uso:
  python scripts/new_view.py --model courses.students --module students [--editable]

Dado un modelo ya definido en extra_addons/<module>/models/, genera (si no existen)
view_list_<modelo>.xml y view_form_<modelo>.xml, los cuelga de menu_<module> (debe
existir), y agrega la fila que falte en __manifest__.py / ir.model.access.csv.

Si las vistas YA existen: modo update aditivo — solo agrega los campos del modelo
que todavía no están en el XML. Nunca borra ni reordena nada existente.

Relaciones:
  Many2one   -> <field name="x_id"/>
  Many2many  -> <field name="x_ids" widget="many2many_tags"/>
  One2many   -> solo en form, embebido. Por default solo-lectura
                (create="false" edit="false" delete="false"); --editable lo saca.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import odoo
from odoo.tools import config

config.parse_config(["-c", "odoo.conf"])

import odoo.modules.registry
from odoo import SUPERUSER_ID, api

DB = config["db_name"]
if isinstance(DB, list):
    DB = DB[0]

EXCLUDED_FIELDS = {
    "id", "display_name", "create_uid", "create_date",
    "write_uid", "write_date", "__last_update",
}


def model_suffix(model_name):
    return model_name.replace(".", "_")


def field_name_in(line):
    m = re.search(r'name="([a-zA-Z0-9_]+)"', line)
    return m.group(1) if m else None


def existing_field_names(xml_text):
    return set(re.findall(r'<field name="([a-zA-Z0-9_]+)"', xml_text))


def find_view_file(app_dir, model_name, root_tag):
    """Busca entre los XML ya existentes uno que ya declare este modelo con este
    tag raíz (<list>/<form>), sin asumir ninguna convención de nombre de archivo."""
    views_dir = os.path.join(app_dir, "views")
    marker = f'<field name="model">{model_name}</field>'
    for fname in sorted(os.listdir(views_dir)):
        if not fname.endswith(".xml") or fname == "view_menu.xml":
            continue
        path = os.path.join(views_dir, fname)
        with open(path) as f:
            text = f.read()
        if marker in text and f"<{root_tag}" in text:
            return path
    return None


def get_field_lines(env, model_name, editable, for_list):
    """Devuelve (lineas_simples, bloques_one2many) para el modelo."""
    Model = env[model_name]
    lines = []
    o2m_blocks = []
    indent = "                " if for_list else "                        "
    for fname, field in Model._fields.items():
        if fname in EXCLUDED_FIELDS:
            continue
        if field.type == "one2many":
            if for_list:
                continue
            comodel = field.comodel_name
            rec_name = env[comodel]._rec_name or "display_name"
            attrs = "" if editable else ' create="false" edit="false" delete="false"'
            o2m_blocks.append(
                f'                    <field name="{fname}" nolabel="1">\n'
                f'                        <list{attrs}>\n'
                f'                            <field name="{rec_name}"/>\n'
                f"                        </list>\n"
                f"                    </field>\n"
            )
            continue
        widget = ' widget="many2many_tags"' if field.type == "many2many" else ""
        lines.append(f'{indent}<field name="{fname}"{widget}/>\n')
    return lines, o2m_blocks


def create_list_view(app_dir, model_name, env, label):
    existing_path = find_view_file(app_dir, model_name, "list")
    if existing_path:
        return update_list_view(existing_path, model_name, env), False
    suffix = model_suffix(model_name)
    path = os.path.join(app_dir, "views", f"view_list_{suffix}.xml")
    lines, _ = get_field_lines(env, model_name, editable=False, for_list=True)
    content = (
        '<?xml version="1.0" encoding="UTF-8" ?>\n'
        "<odoo>\n"
        f'    <record id="view_list_{suffix}" model="ir.ui.view">\n'
        f"        <field name=\"name\">{label} - List</field>\n"
        f"        <field name=\"model\">{model_name}</field>\n"
        '        <field name="arch" type="xml">\n'
        "            <list>\n"
        + "".join(lines)
        + "            </list>\n"
        "        </field>\n"
        "    </record>\n"
        "</odoo>\n"
    )
    with open(path, "w") as f:
        f.write(content)
    return path, True


def update_list_view(path, model_name, env):
    with open(path) as f:
        text = f.read()
    existing = existing_field_names(text)
    lines, _ = get_field_lines(env, model_name, editable=False, for_list=True)
    new_lines = [l for l in lines if field_name_in(l) not in existing]
    if new_lines:
        text = text.replace("</list>", "".join(new_lines) + "            </list>", 1)
        with open(path, "w") as f:
            f.write(text)
    return path


def create_form_view(app_dir, model_name, env, editable, label):
    existing_path = find_view_file(app_dir, model_name, "form")
    if existing_path:
        return update_form_view(existing_path, model_name, env, editable), False
    suffix = model_suffix(model_name)
    path = os.path.join(app_dir, "views", f"view_form_{suffix}.xml")
    lines, o2m_blocks = get_field_lines(env, model_name, editable=editable, for_list=False)
    content = (
        '<?xml version="1.0" encoding="UTF-8" ?>\n'
        "<odoo>\n"
        f'    <record id="view_form_{suffix}" model="ir.ui.view">\n'
        f"        <field name=\"name\">{label} - Form</field>\n"
        f"        <field name=\"model\">{model_name}</field>\n"
        '        <field name="arch" type="xml">\n'
        "            <form>\n"
        "                <sheet>\n"
        "                    <group>\n"
        + "".join(lines)
        + "                    </group>\n"
        + "".join(o2m_blocks)
        + "                </sheet>\n"
        "            </form>\n"
        "        </field>\n"
        "    </record>\n"
        "</odoo>\n"
    )
    with open(path, "w") as f:
        f.write(content)
    return path, True


def update_form_view(path, model_name, env, editable):
    with open(path) as f:
        text = f.read()
    existing = existing_field_names(text)
    lines, o2m_blocks = get_field_lines(env, model_name, editable=editable, for_list=False)
    new_lines = [l for l in lines if field_name_in(l) not in existing]
    changed = False
    if new_lines:
        text = text.replace("</group>", "".join(new_lines) + "                    </group>", 1)
        changed = True
    for block in o2m_blocks:
        fname = field_name_in(block)
        if fname not in existing:
            text = text.replace("</sheet>", block + "                </sheet>", 1)
            changed = True
    if changed:
        with open(path, "w") as f:
            f.write(text)
    return path


def ensure_manifest(app_dir, new_files):
    path = os.path.join(app_dir, "__manifest__.py")
    with open(path) as f:
        text = f.read()
    added = False
    for fname in new_files:
        rel = f"views/{fname}"
        if rel not in text:
            text = text.replace(
                '"views/view_menu.xml",',
                f'"{rel}",\n        "views/view_menu.xml",',
            )
            added = True
    if added:
        with open(path, "w") as f:
            f.write(text)


def ensure_access(app_dir, model_name):
    path = os.path.join(app_dir, "security", "ir.model.access.csv")
    suffix = model_suffix(model_name)
    model_ref = f"model_{suffix}"
    with open(path) as f:
        text = f.read()
    if model_ref in text:
        return
    line = f"access_{suffix},access.{model_name},{model_ref},base.group_user,1,1,1,1\n"
    if not text.endswith("\n"):
        text += "\n"
    text += line
    with open(path, "w") as f:
        f.write(text)


def ensure_menu(app_dir, module, model_name, label):
    path = os.path.join(app_dir, "views", "view_menu.xml")
    with open(path) as f:
        text = f.read()
    parent_id = f"menu_{module}"
    if f'id="{parent_id}"' not in text:
        print(f"Error: no existe menu_{parent_id} en {path} — creá el menú principal del módulo primero.")
        sys.exit(1)
    if f'>{model_name}<' in text:
        return
    suffix = model_suffix(model_name)
    action_id = f"action_{suffix}"
    menu_id = f"menu_{suffix}"
    block = (
        f'\n    <record id="{action_id}" model="ir.actions.act_window">\n'
        f"        <field name=\"name\">{label}</field>\n"
        f"        <field name=\"res_model\">{model_name}</field>\n"
        '        <field name="view_mode">list,form</field>\n'
        "    </record>\n\n"
        f'    <menuitem id="{menu_id}"\n'
        f'              action="{action_id}"\n'
        f"              name=\"{label}\"\n"
        f'              parent="{parent_id}"\n'
        "    />\n"
    )
    text = text.replace("</odoo>", block + "</odoo>")
    with open(path, "w") as f:
        f.write(text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--editable", action="store_true")
    args = parser.parse_args()

    app_dir = os.path.join("extra_addons", args.module)
    if not os.path.isdir(app_dir):
        print(f"Error: {app_dir} no existe")
        sys.exit(1)

    reg = odoo.modules.registry.Registry.new(DB)
    with reg.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        try:
            Model = env[args.model]
        except KeyError:
            print(
                f"Error: modelo '{args.model}' no existe en el registry "
                f"(¿está definido en extra_addons/{args.module}/models/ y el módulo está instalado?)"
            )
            sys.exit(1)
        label = Model._description or args.model

        list_path, list_created = create_list_view(app_dir, args.model, env, label)
        form_path, form_created = create_form_view(app_dir, args.model, env, args.editable, label)

        new_files = []
        if list_created:
            new_files.append(os.path.basename(list_path))
        if form_created:
            new_files.append(os.path.basename(form_path))
        if new_files:
            ensure_manifest(app_dir, new_files)

        ensure_access(app_dir, args.model)
        ensure_menu(app_dir, args.module, args.model, label)

    print(f"Listo: {list_path}{' (nuevo)' if list_created else ' (actualizado)'}")
    print(f"Listo: {form_path}{' (nuevo)' if form_created else ' (actualizado)'}")
    print(f"Corré 'make update-module module={args.module}' (o dejá que make dev lo aplique) para ver los cambios.")


if __name__ == "__main__":
    main()