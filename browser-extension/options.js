// Mismo shim que background.js — en Firefox `chrome.*` es callback-based,
// no Promise, y estos await no funcionarían sin esto.
const api = typeof browser !== "undefined" ? browser : chrome;

const hostInput = document.getElementById("host");
const portInput = document.getElementById("port");
const sidecarPortInput = document.getElementById("sidecarPort");
const status = document.getElementById("status");

async function load() {
  const { host, port, sidecarPort } = await api.storage.local.get([
    "host",
    "port",
    "sidecarPort",
  ]);
  hostInput.value = host || "localhost";
  portInput.value = port || "8069";
  sidecarPortInput.value = sidecarPort || "";
}

async function save() {
  const host = hostInput.value.trim() || "localhost";
  const port = Number(portInput.value) || 8069;
  const sidecarPort = Number(sidecarPortInput.value) || port + 1;

  const origins = [`http://${host}:${port}/*`, `http://${host}:${sidecarPort}/*`];

  const granted = await api.permissions.request({ origins });
  if (!granted) {
    status.textContent = "Permiso denegado — no se guardó.";
    status.style.color = "#b00020";
    return;
  }

  await api.storage.local.set({ host, port, sidecarPort });
  status.textContent = `Guardado — escuchando ${host}:${sidecarPort}, refrescando pestañas de ${host}:${port}.`;
  status.style.color = "#1a7f37";
}

document.getElementById("save").addEventListener("click", save);
load();