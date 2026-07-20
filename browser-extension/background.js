// Mantiene una conexión streaming contra el sidecar de dev_watch.py y
// refresca las pestañas del target configurado cuando llega el evento
// "reload". Si nunca se configuró nada en Opciones, no hace nada.
//
// OJO 1: los service workers de Manifest V3 NO tienen `EventSource` en su
// global scope (solo fetch/caches/indexedDB, no XMLHttpRequest/EventSource/
// DOM) — por eso esto lee el stream SSE a mano con fetch() + ReadableStream
// en vez de `new EventSource(...)`, que directamente no existe ahí.
//
// OJO 2: en Firefox, `chrome.*` es un shim de CALLBACKS (no Promises) por
// compat con Chrome viejo — `await chrome.storage.local.get(...)` ahí NO
// espera nada real. `browser.*` sí es Promise nativo en Firefox. En Chrome
// no existe `browser` global, así que cae a `chrome.*` (que en Chrome SÍ es
// Promise-based sin callback). Este shim unifica ambos sin polyfill externo.
const api = typeof browser !== "undefined" ? browser : chrome;

let abortController = null;
let reconnectTimer = null;

async function getConfig() {
  const { host, port, sidecarPort } = await api.storage.local.get([
    "host",
    "port",
    "sidecarPort",
  ]);
  if (!host || !port) return null;
  return {
    host,
    port: Number(port),
    sidecarPort: Number(sidecarPort) || Number(port) + 1,
  };
}

function stop() {
  if (abortController) {
    abortController.abort();
    abortController = null;
  }
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
}

function scheduleReconnect() {
  if (reconnectTimer) return;
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    connect();
  }, 3000);
}

async function connect() {
  stop();

  const config = await getConfig();
  if (!config) return; // sin configurar — no hacemos nada

  const { host, port, sidecarPort } = config;
  const origin = `http://${host}:${port}/*`;
  const hasPermission = await api.permissions.contains({ origins: [origin] });
  if (!hasPermission) return; // falta autorizar desde Opciones

  abortController = new AbortController();
  const url = `http://${host}:${sidecarPort}/events`;

  try {
    const response = await fetch(url, { signal: abortController.signal });
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      if (chunk.includes("data: reload")) {
        // No filtramos con tabs.query({url: origin}): en Firefox el match
        // pattern con puerto explícito no matchea vía filtro `url` de
        // tabs.query (aunque el mismo pattern sí es válido para
        // permissions.contains) — filtramos a mano en JS en su lugar.
        const prefix = `http://${host}:${port}/`;
        const tabs = await api.tabs.query({});
        for (const tab of tabs) {
          if (tab.url && tab.url.startsWith(prefix)) {
            api.tabs.reload(tab.id);
          }
        }
      }
    }
  } catch (err) {
    // conexión caída (sidecar no está corriendo, red, make dev reiniciado, etc.)
  }

  scheduleReconnect();
}

// Los service workers de MV3 se pueden suspender por inactividad — esto
// asegura que la conexión se reestablezca sola aunque Chrome lo mate.
api.alarms.create("livereload-heartbeat", { periodInMinutes: 0.5 });
api.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name !== "livereload-heartbeat") return;
  if (!abortController) connect();
});

api.runtime.onStartup.addListener(connect);
api.runtime.onInstalled.addListener(connect);
api.storage.onChanged.addListener((changes, area) => {
  if (area === "local") connect();
});

connect();