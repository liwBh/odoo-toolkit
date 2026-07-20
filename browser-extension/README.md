# Odoo Dev Livereload (extensión Chromium / Firefox)

Refresca sola la pestaña de Odoo cuando `make dev` termina de aplicar un cambio (`-u` + restart) — sin recargar a mano después de cada guardado.

**100% opcional.** Quien no la instale no nota ninguna diferencia: `make dev`/`make run` funcionan exactamente igual con o sin ella. No modifica el HTML que sirve Odoo, no depende de ningún módulo instalado en la DB.

## Qué es cada archivo

| Archivo | Rol |
|---|---|
| `manifest.json` | Manifest V3, mismo archivo para **Chromium y Firefox**. El background declara `scripts` y `service_worker` a la vez — Chrome usa `service_worker` e ignora `scripts`; Firefox (121+) usa `scripts` e ignora `service_worker`. Además declara la página de Opciones y los permisos (`storage`, `tabs`, `alarms` fijos; `http://*/*` y `https://*/*` como *optional*, no se piden hasta que configurás un target). |
| `background.js` | Script de background. Lee el stream SSE del sidecar de `dev_watch.py` a mano con `fetch()` + `ReadableStream` (**no** `EventSource` — los service workers de MV3 no lo tienen disponible en su global scope, ver nota abajo) y, al recibir el evento `reload`, refresca (`chrome.tabs.reload` / `browser.tabs.reload`) las pestañas que coincidan con el host/puerto configurado. No inyecta ningún content script — todo corre en background. |
| `options.html` / `options.js` | Página de configuración (host, puerto Odoo, puerto sidecar). Al guardar, pide permiso (`chrome.permissions.request`) solo para ese host/puerto puntual — no para todo internet — y persiste en `chrome.storage.local`. |
| `image/` | Íconos de la extensión (`favicon-96x96.png`, `web-app-manifest-192x192.png`, etc.), referenciados desde `manifest.json` → `icons`. |
| `README.md` | Este archivo. |

## Cómo funciona (arquitectura)

```
make dev (scripts/dev_watch.py)
  ├─ odoo-bin en el puerto real (http_port de odoo.conf) — se reinicia en cada -u
  └─ sidecar SSE en http_port + 1 — vive en el mismo proceso que dev_watch.py,
     NO se reinicia junto con odoo-bin, así que la conexión no se corta durante el update

extensión (background.js)
  └─ fetch() streaming abierto contra el sidecar → al terminar un update OK,
     dev_watch.py hace broadcast_reload() → la extensión lee la línea "reload"
     → chrome.tabs.reload() en las pestañas del host/puerto configurado
```

- El sidecar solo emite el evento **después** de confirmar que el server nuevo ya responde (`wait_server_ready` en `dev_watch.py`) — no refresca contra un Odoo que todavía está arrancando.
- Si nadie tiene la extensión instalada, nadie conecta al sidecar — el puerto extra queda abierto sin efecto sobre nada más.
- Sin content script: el refresh se dispara desde `chrome.tabs.reload(tabId)` en el background, así que no hace falta tocar/inyectar nada en las páginas de Odoo.
- **Por qué `fetch()` + `ReadableStream` y no `EventSource`:** un service worker de Manifest V3 corre en `ServiceWorkerGlobalScope`, que **no expone `EventSource`** (tampoco `XMLHttpRequest` ni APIs de DOM) — solo `fetch`, `caches`, `indexedDB`, etc. `new EventSource(...)` ahí explota con `ReferenceError`. `background.js` lee el mismo stream SSE del sidecar a mano: `fetch(url)` → `response.body.getReader()` → decodifica los chunks y busca la línea `data: reload`. Funciona igual en Firefox (ahí el background no es un SW real, sí tendría `EventSource`, pero se dejó el mismo código para no duplicar lógica entre navegadores).

## Instalación (una sola vez por navegador/perfil)

1. Abrir `chrome://extensions` (Edge/Brave/otros Chromium: `edge://extensions`, etc.).
2. Activar el toggle **"Modo de desarrollador"** (arriba a la derecha).
3. Click en **"Cargar descomprimida"** ("Load unpacked") → seleccionar esta carpeta completa (`browser-extension/`, la que contiene `manifest.json`).
4. La extensión queda instalada y activa — sin ícono visible por default (no tiene `action`/popup), se administra desde `chrome://extensions`.

Para reinstalar tras editar el código de la extensión: en `chrome://extensions`, botón de recarga (↻) sobre la tarjeta de la extensión.

### Instalación en Firefox

Firefox no permite instalar un `.xpi` sin firmar de forma permanente en la versión release — la vía de desarrollo es cargarla como **complemento temporal** (dura hasta que cerrás el navegador; hay que recargarla en cada sesión).

1. Abrir `about:debugging#/runtime/this-firefox` en la barra de direcciones.
2. Click en **"Cargar complemento temporal…"**.
3. Seleccionar el archivo `manifest.json` dentro de esta carpeta (`browser-extension/manifest.json`) — no la carpeta, el archivo. Requiere Firefox 121+ (antes de esa versión, la sola presencia de `service_worker` en el manifest rompía el background aunque `scripts` también estuviera declarado — bug ya resuelto en Firefox).
4. Queda listada bajo "Extensiones temporales", con "Secuencia de comandos en segundo plano: En ejecución" si cargó bien.

Para recargar tras editar código: mismo panel `about:debugging`, botón **"Recargar"** sobre la tarjeta de la extensión (no hace falta repetir "Cargar complemento temporal").

**Instalación permanente (opcional, no recomendado para dev diario):** requiere firmar el `.xpi` en [addons.mozilla.org](https://addons.mozilla.org) (self-distribution) o usar Firefox Developer Edition/Nightly con `xpinstall.signatures.required = false` en `about:config`.

## Configuración

1. Abrir la página de Opciones:
   - **Chromium**: en `chrome://extensions`, click en **"Detalles"** de la extensión → **"Opciones de la extensión"** (o click derecho sobre su entrada si el navegador lo ofrece ahí).
   - **Firefox**: en `about:addons` → "Extensiones", click en **"…"** junto a la extensión → **"Opciones"**.
2. Completar:
   - **Host o IP** — `localhost` para desarrollo local; una IP de LAN si `odoo.conf` escucha en `0.0.0.0` y accedés desde otra máquina.
   - **Puerto Odoo** — el `http_port` real de tu `odoo.conf` (el que usás en el navegador para entrar a Odoo).
   - **Puerto sidecar** (opcional) — si lo dejás vacío, asume `puerto Odoo + 1`. `make dev` imprime el valor real al arrancar: `[dev] livereload sidecar en http://localhost:<puerto>/events` — usar ese si no coincide con el default.
3. Click **"Guardar y autorizar"** → el navegador va a pedir confirmar el permiso de acceso a ese host/puerto puntual (no a todo internet) — aceptar.
4. El status de la página muestra confirmación: `Guardado — escuchando <host>:<sidecarPort>, refrescando pestañas de <host>:<port>`.

**Cambiar de proyecto** (otro puerto/otra IP): volver a Opciones, actualizar los campos, guardar de nuevo — no hace falta reinstalar ni recargar la extensión.

## Troubleshooting

| Síntoma | Causa probable |
|---|---|
| No refresca nunca | ¿`make dev` está corriendo? ¿Guardaste la config en Opciones y aceptaste el permiso? Revisar que el puerto sidecar de Opciones coincida con el que imprime `make dev` al arrancar. |
| Dejó de refrescar después de un rato | En Chromium, Manifest V3 puede suspender el service worker por inactividad, cortando la conexión `fetch()` abierta. La extensión ya tiene un `chrome.alarms`/`browser.alarms` cada 30s que lo revive solo — si tarda en reconectar, esperar ese intervalo o recargar la extensión manualmente (`chrome://extensions` o `about:debugging` → "Recargar"). |
| Refresca antes de que Odoo termine de levantar (error de conexión en la pestaña) | No debería pasar — `dev_watch.py` espera un `200` real en `/web/login` antes de emitir el evento. Si ocurre, revisar que el `http_port` configurado en Opciones sea el correcto. |
| El navegador no pide permiso al guardar | Ya estaba concedido de una configuración anterior con el mismo host/puerto — no hace falta volver a pedirlo. |
| Firefox: error "background.service_worker is currently disabled. Add background.scripts." al cargar | Firefox < 121. Confirmar versión en `about:support` (buscar "Versión de Firefox"); actualizar el navegador o, si no es posible, quitar `service_worker` del manifest dejando solo `scripts` (rompe la carga en Chrome MV3, usar solo para ese caso). |
| Firefox: la extensión "desaparece" tras reiniciar el navegador | Es esperado con "Cargar complemento temporal…" — no es instalación permanente. Volver a cargarla desde `about:debugging` cada sesión, o firmar el `.xpi` (ver instalación permanente arriba). |
| Config y permiso OK (`chrome.storage.local.get` y `permissions.contains` confirman todo bien), sidecar conecta, pero nunca refresca la pestaña | Bug de Firefox: `tabs.query({url: "http://host:puerto/*"})` con puerto explícito en el pattern no matchea ninguna pestaña vía el filtro `url`, aunque ese mismo pattern sea válido para `permissions.contains`. Se puede reproducir a mano en la consola del background (`about:debugging` → "Inspeccionar"): `browser.tabs.query({url: "http://localhost:8069/*"})` da `[]` mientras `browser.tabs.query({})` sí lista la pestaña. Ya solucionado en `background.js`: en vez de filtrar con `tabs.query({url})`, se pide `tabs.query({})` y se filtra a mano con `tab.url.startsWith(prefix)`. |