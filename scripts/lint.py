#!/usr/bin/env python3
"""
Uso:
  python scripts/lint.py

Chequeo rápido y manual del código custom (última entrada de addons_path,
mismo criterio que sync_modules.py):
  - .py       -> ruff (se instala solo, una sola vez, si falta)
  - .xml      -> bien-formado (sin dependencia extra, xml.etree de la stdlib)
  - .js/.css  -> biome, vía npx (necesita Node/npm instalado — si no está,
                 avisa y salta esta parte en vez de romper todo el comando)

No toca DB ni servidor, no reemplaza la validación real de Odoo (-u) — solo
pesca errores obvios (imports sin usar, tags sin cerrar) antes de llegar ahí.
"""
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from _addons import addons_paths

ROOT = Path.cwd()
PYTHON = ROOT / ".venv" / "bin" / "python"
RUFF_CONFIG = Path(__file__).parent / "ruff.toml"

GREEN = "\033[32m"
RED = "\033[31m"
BOLD = "\033[1m"
RESET = "\033[0m"


def custom_dir():
    paths = addons_paths()
    return paths[-1] if paths else ROOT / "extra_addons"


def ensure_ruff():
    check = subprocess.run(
        [str(PYTHON), "-c", "import ruff"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    if check.returncode != 0:
        print(f"{BOLD}[lint] ruff no está instalado — instalando (una sola vez)...{RESET}", flush=True)
        subprocess.run([str(PYTHON), "-m", "pip", "install", "--quiet", "ruff"], check=True)


def lint_python(target):
    ensure_ruff()
    result = subprocess.run(
        [str(PYTHON), "-m", "ruff", "check", "--config", str(RUFF_CONFIG), str(target)]
    )
    return result.returncode == 0


def lint_js_css(target):
    if not shutil.which("npx"):
        print(f"[lint] npx no disponible (¿Node.js instalado?) — salteo chequeo de .js/.css")
        return True
    has_files = next(target.rglob("*.js"), None) or next(target.rglob("*.css"), None)
    if not has_files:
        return True
    result = subprocess.run(["npx", "--yes", "@biomejs/biome@latest", "lint", str(target)])
    return result.returncode == 0


def lint_xml(target):
    ok = True
    for path in sorted(target.rglob("*.xml")):
        try:
            ET.parse(path)
        except ET.ParseError as exc:
            print(f"{RED}{path}: {exc}{RESET}")
            ok = False
    if ok:
        print(f"{GREEN}[lint] XML — todos bien formados{RESET}")
    return ok


def main():
    target = custom_dir()
    if not target.is_dir():
        print(f"[lint] {target}/ no existe — nada que revisar")
        return
    print(f"{BOLD}[lint] revisando {target}/{RESET}\n", flush=True)
    py_ok = lint_python(target)
    print()
    xml_ok = lint_xml(target)
    print()
    js_ok = lint_js_css(target)
    if not (py_ok and xml_ok and js_ok):
        sys.exit(1)


if __name__ == "__main__":
    main()
