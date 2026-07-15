#!/usr/bin/env python3
"""Watch extra_addons/ y auto-aplica -u + restart en cada cambio (make dev)."""
import configparser
import subprocess
import sys
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

ROOT = Path.cwd()
ADDONS_DIR = ROOT / "extra_addons"
MODULES_FILE = ROOT / "modules.txt"
CONF = ROOT / "odoo.conf"
PYTHON = ROOT / ".venv" / "bin" / "python"
ODOO_BIN = ROOT / "odoo-bin"
WATCHED_SUFFIXES = {".py", ".xml", ".csv", ".po", ".css", ".scss", ".js"}
DEBOUNCE_SECONDS = 1.5

server_proc = None
lock = threading.Lock()
apply_lock = threading.Lock()


def http_port():
    parser = configparser.ConfigParser()
    if CONF.exists():
        parser.read(CONF)
        return parser.get("options", "http_port", fallback="8069")
    return "8069"


def custom_modules():
    if not MODULES_FILE.exists():
        return []
    mods = []
    for line in MODULES_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            mods.append(line)
    return mods


def stop_server():
    global server_proc
    if server_proc and server_proc.poll() is None:
        server_proc.terminate()
        try:
            server_proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            server_proc.kill()
            server_proc.wait()
    server_proc = None
    subprocess.run(["pkill", "-f", "[o]doo-bin"])
    while subprocess.run(["pgrep", "-f", "[o]doo-bin"], stdout=subprocess.DEVNULL).returncode == 0:
        time.sleep(0.3)


def start_server():
    global server_proc
    # sin "reload": nuestro watcher ya maneja restart — evita que el
    # autoreload nativo de Odoo (activado por tener watchdog instalado)
    # reinicie el server por su cuenta y compita con este script.
    server_proc = subprocess.Popen(
        [str(PYTHON), str(ODOO_BIN), "-c", str(CONF), "--dev=access,qweb,xml"],
        cwd=str(ROOT),
    )
    print(f"[dev] servidor en http://localhost:{http_port()}")


def apply_changes(reason):
    with apply_lock:
        mods = custom_modules()
        if not mods:
            print(f"[dev] modules.txt vacío o inexistente — nada que actualizar ({reason})")
            return
        print(f"[dev] cambio detectado ({reason}) — deteniendo server")
        stop_server()
        print(f"[dev] aplicando -u {','.join(mods)}")
        result = subprocess.run(
            [str(PYTHON), str(ODOO_BIN), "-c", str(CONF), "-u", ",".join(mods), "--stop-after-init"],
            cwd=str(ROOT),
        )
        if result.returncode != 0:
            print(f"[dev] ERROR al actualizar módulos (exit {result.returncode}) — server NO se levanta. Corregí y guardá de nuevo.")
            return
    print("[dev] update ok — levantando server")
    start_server()


class DebouncedHandler(FileSystemEventHandler):
    def __init__(self):
        self.timer = None

    def _schedule(self, reason):
        with lock:
            if self.timer:
                self.timer.cancel()
            self.timer = threading.Timer(DEBOUNCE_SECONDS, apply_changes, args=(reason,))
            self.timer.daemon = True
            self.timer.start()

    def on_any_event(self, event):
        if event.event_type not in ("created", "modified", "deleted", "moved"):
            return  # ignora "opened"/"closed_no_write" (lecturas, no cambios reales)
        path = Path(getattr(event, "dest_path", None) or event.src_path)
        if path.suffix in WATCHED_SUFFIXES and "__pycache__" not in path.parts:
            self._schedule(path.relative_to(ROOT))


def main():
    if not ADDONS_DIR.exists():
        print(f"[dev] {ADDONS_DIR} no existe")
        sys.exit(1)

    apply_changes("arranque inicial")

    observer = Observer()
    observer.schedule(DebouncedHandler(), str(ADDONS_DIR), recursive=True)
    observer.start()
    print(f"[dev] watching {ADDONS_DIR} (.py/.xml/.csv/.po/.css/.scss/.js) — Ctrl+C para salir")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()
        stop_server()
        print("[dev] detenido")


if __name__ == "__main__":
    main()