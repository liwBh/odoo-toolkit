#!/usr/bin/env python3
"""
Uso:
  python scripts/remove_view.py --model courses.students --module students

Inverso de new_view.py: borra el/los archivo(s) de vista de ese modelo (busca por
contenido, no por nombre asumido), y saca las referencias en __manifest__.py,
ir.model.access.csv y view_menu.xml (record ir.actions.act_window + menuitem).

No toca la DB — corré 'make update-module module=<module>' después para que Odoo
borre los registros (ir.ui.view, ir.model.access, ir.actions, menuitem) asociados
a los xmlids que ya no están en los XML.
"""
import argparse
import os
import re
import sys


def model_suffix(model_name):
    return model_name.replace(".", "_")


def find_view_files(app_dir, model_name):
    views_dir = os.path.join(app_dir, "views")
    marker = f'<field name="model">{model_name}</field>'
    found = []
    for fname in sorted(os.listdir(views_dir)):
        if not fname.endswith(".xml") or fname == "view_menu.xml":
            continue
        path = os.path.join(views_dir, fname)
        with open(path) as f:
            text = f.read()
        if marker in text:
            found.append(path)
    return found


def remove_from_manifest(app_dir, removed_files):
    path = os.path.join(app_dir, "__manifest__.py")
    with open(path) as f:
        text = f.read()
    changed = False
    for fname in removed_files:
        rel = f"views/{fname}"
        pattern = rf'\n\s*"{re.escape(rel)}",'
        new_text = re.sub(pattern, "", text, count=1)
        if new_text != text:
            text = new_text
            changed = True
    if changed:
        with open(path, "w") as f:
            f.write(text)


def remove_from_access_csv(app_dir, model_name):
    path = os.path.join(app_dir, "security", "ir.model.access.csv")
    suffix = model_suffix(model_name)
    model_ref = f"model_{suffix}"
    with open(path) as f:
        lines = f.readlines()
    new_lines = [l for l in lines if f",{model_ref}," not in l]
    if len(new_lines) != len(lines):
        with open(path, "w") as f:
            f.writelines(new_lines)
        return True
    return False


def remove_from_menu(app_dir, model_name):
    path = os.path.join(app_dir, "views", "view_menu.xml")
    with open(path) as f:
        text = f.read()
    suffix = model_suffix(model_name)
    action_id = f"action_{suffix}"

    action_pattern = (
        rf'\n?\s*<record id="{re.escape(action_id)}"[^>]*>.*?</record>\n?'
    )
    menuitem_pattern = (
        rf'\n?\s*<menuitem id="menu_{re.escape(suffix)}"[^>]*?/>\n?'
    )
    menuitem_pattern_multiline = (
        rf'\n?\s*<menuitem id="menu_{re.escape(suffix)}".*?/>\n?'
    )

    new_text = re.sub(action_pattern, "\n", text, count=1, flags=re.DOTALL)
    changed = new_text != text
    text = new_text
    new_text = re.sub(menuitem_pattern_multiline, "\n", text, count=1, flags=re.DOTALL)
    changed = changed or (new_text != text)
    text = new_text

    if changed:
        with open(path, "w") as f:
            f.write(text)
    return changed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--module", required=True)
    args = parser.parse_args()

    app_dir = os.path.join("extra_addons", args.module)
    if not os.path.isdir(app_dir):
        print(f"Error: {app_dir} no existe")
        sys.exit(1)

    view_files = find_view_files(app_dir, args.model)
    if not view_files:
        print(f"No se encontraron vistas para '{args.model}' en {app_dir}/views/")
        sys.exit(1)

    removed_basenames = []
    for path in view_files:
        print(f"Borrando {path}")
        os.remove(path)
        removed_basenames.append(os.path.basename(path))

    remove_from_manifest(app_dir, removed_basenames)
    csv_changed = remove_from_access_csv(app_dir, args.model)
    menu_changed = remove_from_menu(app_dir, args.model)

    print(f"__manifest__.py: referencias sacadas")
    print(f"ir.model.access.csv: {'fila sacada' if csv_changed else 'sin cambios'}")
    print(f"view_menu.xml: {'action/menuitem sacados' if menu_changed else 'sin cambios'}")
    print(f"\nCorré 'make update-module module={args.module}' (o dejá que make dev lo aplique) para limpiar en DB.")


if __name__ == "__main__":
    main()
