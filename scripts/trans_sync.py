#!/usr/bin/env python3
"""Exporta el .po de un idioma para uno o más módulos, preservando los
msgstr que ya estaban traducidos — a diferencia de `odoo-bin i18n export`,
que pisa el archivo entero con lo que trae del export nuevo (make trans-sync).
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import polib

from _addons import find_module_dir

ROOT = Path.cwd()
PYTHON = ROOT / ".venv" / "bin" / "python"


def sync_module(conf, db, lang, module):
    app_dir = find_module_dir(module)
    if not app_dir:
        print(f"[trans-sync] módulo '{module}' no encontrado en addons_path — salteado")
        return
    po_path = app_dir / "i18n" / f"{lang}.po"

    old_translations = {}
    if po_path.exists():
        old = polib.pofile(str(po_path))
        old_translations = {entry.msgid: entry.msgstr for entry in old if entry.msgstr}

    with tempfile.NamedTemporaryFile(suffix=".po") as tmp:
        subprocess.run(
            [
                str(PYTHON), "odoo-bin", "i18n", "export",
                "-c", conf, "-d", db, module, "-l", lang, "-o", tmp.name,
            ],
            check=True,
        )
        fresh = polib.pofile(tmp.name)

    restored = 0
    for entry in fresh:
        if entry.msgid in old_translations and not entry.msgstr:
            entry.msgstr = old_translations[entry.msgid]
            restored += 1

    po_path.parent.mkdir(parents=True, exist_ok=True)
    fresh.save(str(po_path))
    print(f"[trans-sync] {po_path} — {restored} traducciones existentes preservadas")


def main():
    if len(sys.argv) < 5:
        print("Uso: trans_sync.py <conf> <db> <lang> <modulo> [<modulo> ...]")
        sys.exit(1)
    conf, db, lang, *modules = sys.argv[1:]
    for module in modules:
        sync_module(conf, db, lang, module)


if __name__ == "__main__":
    main()