#!/usr/bin/env python3
"""
Uso:
  python scripts/sync_modules.py

Escanea el dir custom (última entrada de addons_path) buscando carpetas con
__manifest__.py y agrega a modules.txt las que todavía no estén listadas.
Aditivo: nunca borra ni reordena líneas existentes (ni las comentadas).

Útil al clonar un proyecto existente donde modules.txt no viene versionado
(o quedó vacío) pero los módulos custom ya están en el repo.
"""
import sys
from pathlib import Path

from _addons import addons_paths

ROOT = Path.cwd()
MODULES_FILE = ROOT / "modules.txt"


def listed_modules(path):
    if not path.exists():
        return []
    return [line.strip().lstrip("#").strip() for line in path.read_text().splitlines() if line.strip()]


def found_modules(custom_dir):
    if not custom_dir.is_dir():
        return []
    mods = []
    for entry in sorted(custom_dir.iterdir()):
        if entry.is_dir() and (entry / "__manifest__.py").is_file():
            mods.append(entry.name)
    return mods


def main():
    paths = addons_paths()
    if not paths:
        print("Error: no se pudo resolver addons_path")
        sys.exit(1)
    custom_dir = paths[-1]

    found = found_modules(custom_dir)
    if not found:
        print(f"No se encontraron módulos (con __manifest__.py) en {custom_dir}/")
        sys.exit(0)

    already = set(listed_modules(MODULES_FILE))
    missing = [m for m in found if m not in already]

    if not missing:
        print(f"modules.txt ya tiene los {len(found)} módulo(s) encontrados en {custom_dir}/ — nada que agregar")
        return

    with open(MODULES_FILE, "a") as f:
        if MODULES_FILE.exists() and MODULES_FILE.stat().st_size > 0:
            content = MODULES_FILE.read_text()
            if content and not content.endswith("\n"):
                f.write("\n")
        for mod in missing:
            f.write(mod + "\n")

    print(f"Agregados a modules.txt: {', '.join(missing)}")
    skipped = set(found) - set(missing)
    if skipped:
        print(f"Ya listados (sin tocar): {', '.join(sorted(skipped))}")


if __name__ == "__main__":
    main()