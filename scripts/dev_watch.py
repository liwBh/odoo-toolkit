#!/usr/bin/env python3
"""Watch los módulos de modules.txt (ubicados vía addons_path) y auto-aplica
-u + restart en cada cambio (make dev)."""
import configparser
import queue
import subprocess
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from _addons import addons_paths, find_module_dir

ROOT = Path.cwd()
MODULES_FILE = ROOT / "modules.txt"
CONF = ROOT / "odoo.conf"
PYTHON = ROOT / ".venv" / "bin" / "python"
ODOO_BIN = ROOT / "odoo-bin"
WATCHED_SUFFIXES = {".py", ".xml", ".csv", ".po", ".css", ".scss", ".js"}
DEBOUNCE_SECONDS = 1.5

RESET = "\033[0m"
BOLD = "\033[1m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
RED = "\033[31m"

server_proc = None
lock = threading.Lock()
apply_lock = threading.Lock()

# --- Livereload sidecar (opcional) ---------------------------------------
# Servidor SSE aparte, independiente del ciclo de vida de odoo-bin (vive en
# este mismo proceso, no lo mata el stop/restart de cada -u). Sirve para que
# la extensión de navegador (ver browser-extension/ en la raíz del toolkit)
# refresque la pestaña sola cuando termina un update — pero es 100% opcional:
# si nadie la instaló, no hay clientes conectados a /events y esto no hace
# nada más que escuchar en un puerto extra sin efecto sobre make dev/run.
sidecar_clients = []
sidecar_lock = threading.Lock()


class _ReloadHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # silencia el access log default (ya tenemos nuestros propios prints)

    def do_GET(self):
        if self.path != "/events":
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        client_queue = queue.Queue()
        with sidecar_lock:
            sidecar_clients.append(client_queue)
        try:
            while True:
                try:
                    client_queue.get(timeout=15)
                    self.wfile.write(b"data: reload\n\n")
                    self.wfile.flush()
                except queue.Empty:
                    # heartbeat — mantiene viva la conexión y detecta sockets muertos
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            with sidecar_lock:
                if client_queue in sidecar_clients:
                    sidecar_clients.remove(client_queue)


def broadcast_reload():
    with sidecar_lock:
        for client_queue in sidecar_clients:
            client_queue.put(True)


def start_sidecar(port):
    try:
        server = ThreadingHTTPServer(("0.0.0.0", port), _ReloadHandler)
    except OSError as exc:
        print(f"{YELLOW}[dev] livereload sidecar no pudo levantar en el puerto {port} ({exc}) — seguimos sin auto-reload de navegador{RESET}")
        return
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"[dev] livereload sidecar en http://localhost:{port}/events (opcional — ver browser-extension/)")


def wait_server_ready(port, timeout=30):
    url = f"http://localhost:{port}/web/login"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except Exception:
            time.sleep(0.3)
    return False


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


def module_dirs():
    """Resuelve, para cada módulo en modules.txt, su carpeta real según
    addons_path (no asume extra_addons). Ignora los que no se encuentran."""
    paths = addons_paths()
    dirs = []
    for mod in custom_modules():
        found = find_module_dir(mod, paths)
        if found:
            dirs.append(found)
        else:
            print(f"[dev] aviso: módulo '{mod}' no encontrado en addons_path — no se va a vigilar")
    return dirs


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
        if mods:
            print(f"{YELLOW}{BOLD}[dev] ⏳ ACTUALIZANDO ({reason}) — deteniendo server...{RESET}")
            stop_server()
            print(f"{YELLOW}[dev] aplicando -u {','.join(mods)}{RESET}")
            result = subprocess.run(
                [str(PYTHON), str(ODOO_BIN), "-c", str(CONF), "-u", ",".join(mods), "--stop-after-init"],
                cwd=str(ROOT),
            )
            if result.returncode != 0:
                print(f"{RED}{BOLD}[dev] ✗ ERROR al actualizar módulos (exit {result.returncode}) — server NO se levanta. Corregí y guardá de nuevo.{RESET}")
                return
        else:
            print(f"[dev] modules.txt vacío o inexistente — arrancando server sin actualizar módulos ({reason})")
            stop_server()
    print(f"{GREEN}{BOLD}[dev] ✓ ACTUALIZACIÓN COMPLETA — levantando server{RESET}")
    start_server()
    if wait_server_ready(http_port()):
        broadcast_reload()


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
            try:
                reason = path.relative_to(ROOT)
            except ValueError:
                reason = path  # módulo fuera de ROOT (addons_path con ruta absoluta externa)
            self._schedule(reason)


def main():
    dirs = module_dirs()
    if not dirs:
        print("[dev] aviso: ningún módulo de modules.txt se encontró en addons_path — arranca igual, sin nada que vigilar")

    start_sidecar(int(http_port()) + 1)
    apply_changes("arranque inicial")

    observer = Observer()
    for d in dirs:
        observer.schedule(DebouncedHandler(), str(d), recursive=True)
    observer.start()
    if dirs:
        watched = ", ".join(str(d) for d in dirs)
        print(f"[dev] watching {watched} (.py/.xml/.csv/.po/.css/.scss/.js) — Ctrl+C para salir")
    else:
        print("[dev] sin módulos vigilados (modules.txt vacío) — server corriendo. Ctrl+C para salir")

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