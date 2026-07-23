#!/usr/bin/env python3
"""
Uso:
  python scripts/status.py

Panorama rápido del proyecto: odoo.conf, venv, server corriendo, DB accesible,
y estado real (ir_module_module) de cada módulo listado en modules.txt.
No bootea el registry completo de Odoo (rápido) — consulta la DB directo
con psycopg2 (dependencia que Odoo ya trae).
"""
import configparser
import subprocess
from pathlib import Path

from _addons import addons_paths, find_module_dir

ROOT = Path.cwd()
CONF = ROOT / "odoo.conf"
MODULES_FILE = ROOT / "modules.txt"
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"

GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
BOLD = "\033[1m"
RESET = "\033[0m"


def ok(msg):
    print(f"{GREEN}✓{RESET} {msg}")


def warn(msg):
    print(f"{YELLOW}!{RESET} {msg}")


def bad(msg):
    print(f"{RED}✗{RESET} {msg}")


def custom_modules():
    if not MODULES_FILE.exists():
        return []
    return [
        line.strip() for line in MODULES_FILE.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def main():
    print(f"{BOLD}[status] {ROOT}{RESET}\n")

    if not CONF.exists():
        bad("odoo.conf no existe — corré: make init-config db_name=... admin_passwd=...")
        db_name = db_user = db_host = db_port = http_port = None
    else:
        parser = configparser.ConfigParser()
        parser.read(CONF)
        db_name = parser.get("options", "db_name", fallback=None)
        db_user = parser.get("options", "db_user", fallback=None)
        db_host = parser.get("options", "db_host", fallback="localhost")
        db_port = parser.get("options", "db_port", fallback="5432")
        http_port = parser.get("options", "http_port", fallback="8069")
        ok(f"odoo.conf — db={db_name} user={db_user} http_port={http_port}")

    if VENV_PYTHON.exists():
        ok(".venv — OK")
    else:
        bad(".venv no existe — corré: make setup")

    result = subprocess.run(["pgrep", "-f", "[o]doo-bin"], stdout=subprocess.PIPE, text=True)
    pids = result.stdout.split()
    if pids:
        ok(f"server corriendo (PID {', '.join(pids)}, puerto {http_port or '?'})")
    else:
        warn("server no está corriendo — make run / make dev")

    if not db_name:
        return

    try:
        import psycopg2
        conn = psycopg2.connect(dbname=db_name, user=db_user, host=db_host, port=db_port, connect_timeout=3)
    except Exception as exc:
        bad(f"DB '{db_name}' no accesible: {exc}")
        print("  Corré: make init-db (o make reset-db si ya existía y algo quedó mal)")
        return

    ok(f"DB '{db_name}' — accesible")

    mods = custom_modules()
    if not mods:
        warn("modules.txt vacío o inexistente — make sync-modules si ya tenés módulos en el repo")
        conn.close()
        return

    with conn.cursor() as cur:
        try:
            cur.execute("SELECT name, state FROM ir_module_module WHERE name = ANY(%s)", (mods,))
            states = dict(cur.fetchall())
        except Exception:
            bad("tabla ir_module_module no existe — la DB no tiene 'base' instalado. Corré: make init-db")
            conn.close()
            return
    conn.close()

    paths = addons_paths()
    print(f"\n{BOLD}modules.txt ({len(mods)}):{RESET}")
    for mod in mods:
        state = states.get(mod)
        loc = "" if find_module_dir(mod, paths) else "  (⚠ no encontrado en addons_path)"
        if state == "installed":
            ok(f"{mod} — installed{loc}")
        elif state:
            warn(f"{mod} — {state}{loc}")
        else:
            bad(f"{mod} — no instalado{loc}  (make install-module module={mod})")


if __name__ == "__main__":
    main()
