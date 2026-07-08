#!/usr/bin/env python3
"""
Uso:
  python scripts/remove_module.py --name students

Inverso de new_module.sh: desinstala el módulo desde Odoo (limpia tablas,
ir.model.data, ir.model.access, vistas, menús asociados), borra la carpeta
extra_addons/<name>/ y lo saca de modules.txt.

Destructivo e irreversible — pide confirmación escribiendo el nombre del módulo,
salvo que se pase --yes.
"""
import argparse
import os
import shutil
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--yes", action="store_true", help="Salta la confirmación interactiva")
    args = parser.parse_args()

    app_dir = os.path.join("extra_addons", args.name)
    if not os.path.isdir(app_dir):
        print(f"Error: {app_dir} no existe")
        sys.exit(1)

    if not args.yes:
        print(f"Esto desinstala '{args.name}' de la DB y borra {app_dir}/ por completo. No se puede deshacer.")
        typed = input(f"Escribí '{args.name}' para confirmar: ")
        if typed != args.name:
            print("Cancelado.")
            sys.exit(1)

    reg = odoo.modules.registry.Registry.new(DB)
    with reg.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        module = env["ir.module.module"].search([("name", "=", args.name)], limit=1)
        if module and module.state not in ("uninstalled", "uninstallable"):
            print(f"Desinstalando módulo '{args.name}' (state actual: {module.state})...")
            module.button_immediate_uninstall()
            cr.commit()
        else:
            print(f"Módulo '{args.name}' no está instalado en DB (o no existe registro) — salto la desinstalación.")

    shutil.rmtree(app_dir)
    print(f"Carpeta {app_dir}/ borrada.")

    modules_file = "modules.txt"
    if os.path.exists(modules_file):
        with open(modules_file) as f:
            lines = f.readlines()
        new_lines = [l for l in lines if l.strip() != args.name]
        if len(new_lines) != len(lines):
            with open(modules_file, "w") as f:
                f.writelines(new_lines)
            print(f"Sacado de {modules_file}")

    print(f"\n'{args.name}' eliminado por completo.")


if __name__ == "__main__":
    main()
