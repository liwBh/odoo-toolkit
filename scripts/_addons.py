#!/usr/bin/env python3
"""Helpers compartidos: ubican módulos según addons_path de odoo.conf en vez
de asumir que todo vive en extra_addons/.
"""
import configparser
import sys
from pathlib import Path

ROOT = Path.cwd()
CONF = ROOT / "odoo.conf"
DEFAULT_ADDONS_PATH = "./addons,./extra_addons"


def addons_paths(conf=CONF):
    """Lista de paths (absolutos) declarados en addons_path, en orden."""
    raw = DEFAULT_ADDONS_PATH
    if conf.exists():
        parser = configparser.ConfigParser()
        parser.read(conf)
        raw = parser.get("options", "addons_path", fallback=DEFAULT_ADDONS_PATH)
    paths = []
    for p in raw.split(","):
        p = p.strip()
        if not p:
            continue
        path = Path(p)
        if not path.is_absolute():
            path = ROOT / path
        paths.append(path)
    return paths


def find_module_dir(name, paths=None):
    """Busca <name>/__manifest__.py en cada entrada de addons_path. None si no está en ninguna."""
    for base in (paths if paths is not None else addons_paths()):
        candidate = base / name
        if (candidate / "__manifest__.py").is_file():
            return candidate
    return None


def new_module_dir(name, paths=None):
    """Destino para crear un módulo nuevo: última entrada de addons_path
    (por convención, donde vive el código custom del proyecto)."""
    paths = paths if paths is not None else addons_paths()
    base = paths[-1] if paths else ROOT / "extra_addons"
    return base / name


if __name__ == "__main__":
    # CLI mínima para uso desde Makefile/bash: python scripts/_addons.py find|new <modulo>
    if len(sys.argv) != 3 or sys.argv[1] not in ("find", "new"):
        print("Uso: _addons.py find|new <modulo>", file=sys.stderr)
        sys.exit(1)
    action, name = sys.argv[1], sys.argv[2]
    result = find_module_dir(name) if action == "find" else new_module_dir(name)
    print(result if result else "", end="")