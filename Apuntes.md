# Apuntes Odoo 19 — Desarrollo de Módulos

## Índice

1. [Instalación y Setup](#1-instalación-y-setup)
   - 1.1 [Clonar repositorio](#11-clonar-repositorio)
   - 1.2 [Entorno virtual e instalar dependencias (manual)](#12-entorno-virtual-e-instalar-dependencias-manual)
   - 1.3 [Setup automático — `make setup`](#13-setup-automático--make-setup)
   - 1.4 [Configuración — odoo.conf](#14-configuración--odooconf)
2. [Base de Datos](#2-base-de-datos)
   - 2.1 [Inicializar (manual)](#21-inicializar-manual)
   - 2.2 [Comandos Makefile](#22-comandos-makefile)
3. [Servidor — Flujo de Desarrollo](#3-servidor--flujo-de-desarrollo)
   - 3.1 [Iniciar la app con Makefile](#31-iniciar-la-app-con-makefile)
   - 3.2 [make run / stop / restart](#32-make-run--stop--restart)
   - 3.3 [make dev — auto `-u` + restart al guardar](#33-make-dev--auto--u--restart-al-guardar)
   - 3.4 [Modo Desarrollador (Developer Mode)](#34-modo-desarrollador-developer-mode)
4. [Estructura y Anatomía de un Módulo](#4-estructura-y-anatomía-de-un-módulo)
   - 4.1 [Estructura de carpetas](#41-estructura-de-carpetas)
   - 4.2 [`__manifest__.py`](#42-__manifest__py)
5. [Modelos](#5-modelos)
   - 5.1 [Modelo básico](#51-modelo-básico)
   - 5.2 [Herencia — tres casos de `_inherit`](#52-herencia--tres-casos-de-_inherit)
   - 5.3 [display_name personalizado](#53-display_name-personalizado)
   - 5.4 [El campo `name` — por qué es especial](#54-el-campo-name--por-qué-es-especial)
   - 5.5 [Campos calculados (compute)](#55-campos-calculados-compute)
   - 5.6 [Campos relacionales](#56-campos-relacionales)
6. [Vistas](#6-vistas)
   - 6.1 [Lista (view_list.xml)](#61-lista-view_listxml)
   - 6.2 [Formulario con One2many embebido](#62-formulario-con-one2many-embebido)
   - 6.3 [Anatomía completa de `<form>`](#63-anatomía-completa-de-form)
   - 6.4 [Referencia rápida — elementos, atributos, widgets](#64-referencia-rápida--elementos-atributos-widgets)
   - 6.5 [Interfaz (UI) — patrones de layout](#65-interfaz-ui--patrones-de-layout)
7. [Menús y Acciones (view_menu.xml)](#7-menús-y-acciones-view_menuxml)
8. [Seguridad — ir.model.access.csv](#8-seguridad--irmodelaccesscsv)
9. [Scaffold — Crear módulo nuevo](#9-scaffold--crear-módulo-nuevo)
   - 9.1 [make new-module — módulo completo desde cero](#91-make-new-module--módulo-completo-desde-cero)
   - 9.2 [make new-view — list+form para un modelo ya escrito a mano](#92-make-new-view--listform-para-un-modelo-ya-escrito-a-mano)
   - 9.3 [make remove-view — inverso de 9.2](#93-make-remove-view--inverso-de-92)
   - 9.4 [make remove-module — borrar un módulo completo (destructivo)](#94-make-remove-module--borrar-un-módulo-completo-destructivo)
10. [Usuarios y Contraseñas](#10-usuarios-y-contraseñas)
    - 10.1 [Comandos Makefile de usuarios](#101-comandos-makefile-de-usuarios)
    - 10.2 [Contraseñas — dos conceptos distintos](#102-contraseñas--dos-conceptos-distintos)
    - 10.3 [Cambiar password del usuario admin](#103-cambiar-password-del-usuario-admin)
    - 10.4 [Crear DB con credenciales personalizadas](#104-crear-db-con-credenciales-personalizadas)
11. [Herramientas y Referencia](#11-herramientas-y-referencia)
    - 11.1 [Comandos útiles (manual)](#111-comandos-útiles-manual)
    - 11.2 [Errores comunes](#112-errores-comunes)
    - 11.3 [Plugins recomendados](#113-plugins-recomendados)

---

## 1. Instalación y Setup

### 1.1 Clonar repositorio
```bash
git clone https://github.com/odoo/odoo.git --branch 19.0 --depth 1 odoo-19.0
cd odoo-19.0
```

### 1.2 Entorno virtual e instalar dependencias (manual)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 1.3 Setup automático — `make setup`
```bash
make setup
```
Hace lo mismo que 1.2 más dependencias del toolkit:
- Crea `.venv`, actualiza `pip`, instala `requirements.txt`.
- Instala `watchdog` (usado por `make dev`, ver 3.3).
- Crea `extra_addons/` si no existe.

> Script inline en `Makefile`, target `setup`.

### 1.4 Configuración — odoo.conf

```ini
[options]
admin_passwd = Admin1234
db_host = localhost
db_port = 5432
db_user = user_odoo
db_password = <password>
db_name = odoocurso_db
addons_path = ./addons,./extra_addons
xmlrpc_port = 8069
```

- `addons_path` incluye carpeta `extra_addons` para módulos custom.
- `xmlrpc_port` es el puerto HTTP donde escucha Odoo (`make run` / `make dev`). Default `8069` — se escribe siempre explícito en el conf generado para que quede visible y sea fácil de cambiar si hay conflicto de puerto (ej. varios proyectos corriendo en paralelo).

Crear carpeta si no existe:
```bash
mkdir -p extra_addons
```

**Crear odoo.conf con Makefile:**
```bash
make init-config db_name=curso_odoo db_user=odoo_user db_password=Admin1234 admin_passwd=Admin1234 http_port=8069
```

- Todos los parámetros son opcionales (defaults: `admin_passwd=Admin1234`, `db_host=localhost`, `db_port=5432`, `db_user=odoo_user`, `db_password=<db_user>`, `db_name=odoo_db`, `http_port=8069`).
- `addons_path` siempre queda `./addons,./extra_addons` y crea la carpeta `extra_addons` si no existe.
- Si `odoo.conf` ya existe, rechaza sobreescribir — usar `force=1` para forzar:
```bash
make init-config db_name=curso_odoo force=1
```

> Script: `scripts/init_config.sh`.

---

## 2. Base de Datos

### 2.1 Inicializar (manual)

Primera vez (DB vacía):
```bash
.venv/bin/python odoo-bin -c odoo.conf -i base
```

Instalar módulos custom:
```bash
.venv/bin/python odoo-bin -c odoo.conf -i nombre_modulo1,nombre_modulo2
```

Actualizar módulos (después de cambios en código):
```bash
.venv/bin/python odoo-bin -c odoo.conf -u nombre_modulo1,nombre_modulo2
```

Iniciar servidor normal:
```bash
.venv/bin/python odoo-bin -c odoo.conf --dev=all
```

### 2.2 Comandos Makefile

```bash
make init-db      # -i base --stop-after-init (una sola vez, DB vacía)
make reset-db     # dropdb + createdb + init-db
make install      # -i <módulos de modules.txt> --stop-after-init
make update       # -u <módulos de modules.txt> --stop-after-init
make install-module module=nombre
make update-module module=nombre
```

> `CUSTOM_MODULES` (usado por `install`/`update`) se arma leyendo `modules.txt` — ver sección 9 sobre cómo se registran los módulos ahí.

---

## 3. Servidor — Flujo de Desarrollo

### 3.1 Iniciar la app con Makefile

Pasos en orden:

1. Crear archivo de configuración `odoo.conf` (ver 1.4).
2. Inicializar DB:
   ```bash
   make init-db
   ```
3. Levantar servidor:
   ```bash
   make run
   ```

**URL de acceso:** `http://localhost:8069`

**Credenciales por defecto:**
- Login: `admin`
- Password: `admin`

Ver todos los comandos disponibles:
```bash
make help
```

### 3.2 make run / stop / restart

```bash
make run       # $(ODOO) $(CONF) --dev=all, foreground
make stop      # mata odoo-bin y espera a que muera antes de devolver el control
make restart   # stop + run
```

> `stop` usa `pkill -f "[o]doo-bin"` (bracket-trick) para no auto-matarse — `pkill -f odoo-bin` a secas mata su propio proceso porque su propio cmdline contiene el substring `odoo-bin`.

### 3.3 make dev — auto `-u` + restart al guardar

```bash
make dev
```

Automatiza el ciclo manual de "edito código → paro server → `-u` → levanto server otra vez". Watchea `extra_addons/**/*.{py,xml,csv}` (vía `watchdog`, instalado por `make setup`) y en cada cambio real:

1. Debounce ~1.5s (coalesce guardados múltiples de un mismo save).
2. Detiene el server.
3. Corre `-u <módulos de modules.txt> --stop-after-init`.
4. Si falla (código roto, exit ≠ 0) — **no levanta el server**, deja el traceback visible y espera el próximo guardado.
5. Si OK — levanta el server de nuevo con `--dev=access,qweb,xml` (sin `reload`, para no competir con el autoreload nativo de Odoo que se activa solo por tener `watchdog` instalado).

Cubre lo que un restart simple no cubre: cambios de vistas XML, security CSV y campos de modelo (todos requieren `-u`, no solo restart). Cambios de lógica Python pura también entran por este mismo camino (no hay hot-reload sin `-u`/restart en este setup).

> **No instala módulos nuevos.** `-u` solo actualiza módulos ya instalados — un módulo recién creado con `make new-module` (ver 9.1) necesita un `make install-module module=<nombre>` manual una vez; recién ahí `make dev` lo toma en cada guardado subsecuente.

**Para detenerlo del todo: `Ctrl+C` en su propia terminal**, no `make stop` desde otra. `make stop` solo mata el proceso `odoo-bin` (el server) — el watcher (`dev_watch.py`) sigue vivo esperando cambios, y si guardás algo después lo vuelve a levantar solo, sin que se lo hayas pedido. `Ctrl+C` sí dispara el handler que frena el server limpio y corta el watcher entero.

> Script: `scripts/dev_watch.py`. Corré en su propia terminal — necesitás ver los tracebacks cuando algo rompe.

### 3.4 Modo Desarrollador (Developer Mode)

**Activar:**

- **Opción 1 — URL (más rápido):**
  ```
  http://localhost:8069/web?debug=1
  ```
  Agrega `?debug=1` a cualquier URL de Odoo. Se mantiene activo mientras navegas.

- **Opción 2 — Debug de assets (JS/CSS sin minificar):**
  ```
  http://localhost:8069/web?debug=assets
  ```
  Útil para depurar JavaScript o CSS en el navegador.

- **Opción 3 — Desde la UI:**
  `Settings → General Settings → (scroll al fondo) → Developer Tools → Activate the developer mode`

- **Opción 4 — Desactivar:**
  ```
  http://localhost:8069/web?debug=0
  ```

**Qué habilita:**

| Función | Descripción |
|---------|-------------|
| Menú **Technical** en Settings | Acceso a ir.model, ir.fields, ir.ui.view, acciones, menús, secuencias, etc. |
| Info de campos al hacer hover | Al pasar el mouse sobre una etiqueta de campo muestra nombre técnico, tipo, módulo |
| Inspector de vistas | Botón "Edit View" en cada formulario/lista para ver y editar el XML directamente |
| **Debug** en menú de engranaje | Opciones extra en el menú ⚙ de cada registro |
| Campos técnicos visibles | Muestra campos como `id`, `create_date`, `write_uid` en los formularios |
| Regenerar assets | Fuerza recompilación de JS/CSS |

**Accesos directos con modo desarrollador activo:**
- **Settings → Technical → User Interface → Views** — listar/editar todas las vistas XML
- **Settings → Technical → Database Structure → Models** — ver todos los modelos y sus campos
- **Settings → Technical → Actions → Window Actions** — ver acciones registradas
- **Settings → Technical → User Interface → Menus** — ver árbol de menús

**Flags `--dev` al iniciar servidor:**
```bash
# --dev=all activa auto-reload de vistas XML y Python sin reiniciar
.venv/bin/python odoo-bin -c odoo.conf --dev=all
```

| Flag `--dev` | Efecto |
|-------------|--------|
| `all` | Todo: `access,qweb,reload,xml` |
| `xml` | Recarga vistas XML desde disco sin reiniciar |
| `reload` | Reinicia el proceso al detectar cambios en `.py` (requiere `watchdog` o `inotify` instalado — ver 3.3 sobre por qué `make dev` lo excluye) |
| `qweb` | No cachea templates QWeb |
| `access` | Páginas de error con detalle técnico |

---

## 4. Estructura y Anatomía de un Módulo

### 4.1 Estructura de carpetas

```
mi_modulo/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── mi_modelo.py
├── views/
│   ├── view_list.xml
│   ├── view_form.xml
│   └── view_menu.xml
└── security/
    └── ir.model.access.csv
```

### 4.2 `__manifest__.py`

```python
{
    "name": "Nombre Módulo",
    "category": "categoria",
    "author": "Autor",
    "version": "19.0.0",
    "application": True,          # True = aparece en menú Aplicaciones
    "depends": ["base", "otro_modulo"],
    "data": [
        "views/view_list.xml",
        "views/view_form.xml",
        "views/view_menu.xml",
        "security/ir.model.access.csv",
    ]
}
```

> **Orden importa:** `security` debe ir antes o después de views según dependencias.

---

## 5. Modelos

### 5.1 Modelo básico
```python
from odoo import fields, models

class MiModelo(models.Model):
    _name = 'mi.modelo'          # nombre técnico — define tabla en DB

    name = fields.Char(string='Nombre', required=True)
    descripcion = fields.Text(string='Descripción')
    activo = fields.Boolean(default=True)
```

### 5.2 Herencia — tres casos de `_inherit`

**Regla rápida:**

| `_name` | `_inherit` | Resultado |
|---------|-----------|-----------|
| No | Sí | Modifica modelo existente (misma tabla) |
| Sí | Sí | Crea modelo nuevo con campos heredados (tabla nueva) |

**Caso 1 — Extender modelo de OTRO módulo (agregar campos)**
```python
# En students_managments — agrega campo a courses.info que vive en subjects_managments
class CourseExtended(models.Model):
    _inherit = 'courses.info'    # sin _name → modifica el modelo existente

    enrollment_ids = fields.One2many('courses.students', 'course_id', string='Matrículas')
```
No crea tabla nueva. Agrega columna a `courses_info` existente.
Útil para evitar dependencias circulares entre módulos.

**Caso 2 — Crear modelo nuevo con campos heredados**
```python
# professors.info hereda campos de persons.info
class Professor(models.Model):
    _name = 'professors.info'    # con _name → modelo nuevo
    _inherit = ['persons.info']  # copia campos de persons.info

    campo_extra = fields.Char(string='Extra')
```
Crea tabla nueva `professors_info` con los campos copiados de `persons_info`.

**Caso 3 — Extender modelos nativos de Odoo**
```python
# Agregar campo a res.partner (contactos nativos de Odoo)
class ResPartner(models.Model):
    _inherit = 'res.partner'

    mi_campo = fields.Char(string='Mi Campo')
```

### 5.3 display_name personalizado
Requiere `@api.depends` para recalcular cuando cambian los campos dependientes:
```python
from odoo import api, fields, models

class Persona(models.Model):
    _name = 'persons.info'

    first_name = fields.Char(string='Nombre')
    last_name = fields.Char(string='Apellido')

    @api.depends('first_name', 'last_name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.first_name or ''} {rec.last_name or ''}".strip()
```

> Sin `@api.depends` el campo no se recalcula al editar.

### 5.4 El campo `name` — por qué es especial

Todo modelo de Odoo tiene un campo "rec_name" que se usa como texto por defecto en:
- Selectores Many2one/Many2many (lo que ve el usuario al buscar/elegir un registro relacionado).
- Breadcrumbs, títulos de formulario, resultados de búsqueda global.
- `record.display_name` (a menos que se override, ver 5.3).

Por convención ese campo se llama `name` — si el modelo define un campo `name`, Odoo lo usa automáticamente como `_rec_name` sin configuración extra. Si no existe, hay que declarar `_rec_name = 'otro_campo'` explícitamente o el registro se muestra como `ID` pelado.

**No hace falta que `name` sea editable a mano** — puede ser un campo `compute` (ver 5.5). Ejemplo real (`students.info`): `name` es el nombre completo, calculado a partir de `first_name` + `last_name`:
```python
name = fields.Char(string="Nombre Completo", compute="_compute_name", store=True)
first_name = fields.Char(string="Nombre", required=True)
last_name = fields.Char(string="Apellidos", required=True)

@api.depends("first_name", "last_name")
def _compute_name(self):
    for rec in self:
        rec.name = f"{rec.first_name or ''} {rec.last_name or ''}".strip()
```
Así el selector Many2one hacia `students.info` muestra el nombre completo sin tener que exponer un campo `name` editable en el form.

### 5.5 Campos calculados (compute)

Un campo `compute` se recalcula solo cuando cambian sus dependencias — no se llena a mano.

```python
compute="_compute_metodo"   # nombre del método que calcula el valor
store=True                  # True = se guarda en DB (permite filtrar/ordenar por el campo)
                             # False = se recalcula al vuelo, no ocupa columna en DB
```

**Ejemplo real** (`students.info`): `age` se calcula solo a partir de `birth_date`, nunca se edita a mano:
```python
from datetime import date

birth_date = fields.Date(string="Fecha de Nacimiento", required=True)
age = fields.Integer(string="Edad", compute="_compute_age", store=True)

@api.depends("birth_date")
def _compute_age(self):
    today = date.today()
    for rec in self:
        if not rec.birth_date:
            rec.age = 0
            continue
        born = rec.birth_date
        rec.age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
```

Reglas clave:
- `@api.depends(...)` lista los campos que, al cambiar, disparan el recálculo. Sin esto el campo se queda con el valor viejo (mismo problema que en 5.3).
- El método recibe `self` como un **recordset** — siempre iterar con `for rec in self:` y asignar `rec.campo = valor` dentro del loop (nunca `self.campo = valor` fuera del loop).
- Con `store=True` el campo aparece en vistas `<list>` con `sum`/`group_by`, se puede buscar/filtrar y ordenar — sin `store` no.
- Un campo compute+store queda **readonly en la UI por defecto** (no se puede tipear encima) — coherente con que "se calcula solo".

### 5.6 Campos relacionales

**Many2one — muchos a uno**
```python
# Muchos cursos → un profesor
professor_id = fields.Many2one('professors.info', string='Profesor')
```

**One2many — uno a muchos (inverso de Many2one)**
```python
# Un curso → muchas matrículas
enrollment_ids = fields.One2many('courses.students', 'course_id', string='Matrículas')
```
> Requiere que el modelo destino tenga el `Many2one` correspondiente (`course_id`).

**Many2many — muchos a muchos**
```python
# Cuando es bidireccional (dos modelos se referencian mutuamente)
# Ambos lados deben compartir la misma tabla con columnas invertidas

# En courses.info:
students_id = fields.Many2many(
    'students.info',
    'course_student_rel',  # nombre tabla relación — MISMO en ambos lados
    'course_id',           # columna de ESTE modelo
    'student_id',          # columna del OTRO modelo
)

# En students.info:
course_ids = fields.Many2many(
    'courses.info',
    'course_student_rel',  # mismo nombre
    'student_id',          # invertido
    'course_id',
)
```

> Sin los parámetros explícitos Odoo crea 2 tablas separadas — los datos no se sincronizan.

**Modelo intermedio con datos extra (matrícula con nota)**

Cuando la relación necesita campos propios (ej: nota), usar modelo intermedio + One2many:

```python
# Modelo intermedio
class Matricula(models.Model):
    _name = 'courses.students'

    student_id = fields.Many2one('students.info', required=True)
    course_id = fields.Many2one('courses.info', required=True)
    grade = fields.Float(string='Nota', digits=(4, 2))

# En courses.info → acceder matrículas
enrollment_ids = fields.One2many('courses.students', 'course_id', string='Matrículas')

# En students.info → acceder matrículas
enrollment_ids = fields.One2many('courses.students', 'student_id', string='Matrículas')
```

---

## 6. Vistas

### 6.1 Lista (view_list.xml)
```xml
<?xml version="1.0" encoding="UTF-8" ?>
<odoo>
    <record id="view_list_mi_modelo" model="ir.ui.view">
        <field name="name">Mi Modelo - Lista</field>
        <field name="model">mi.modelo</field>
        <field name="arch" type="xml">
            <list>
                <field name="id"/>
                <field name="name"/>
                <field name="campo_relacion"/>
            </list>
        </field>
    </record>
</odoo>
```

### 6.2 Formulario con One2many embebido (view_form.xml)
```xml
<?xml version="1.0" encoding="UTF-8" ?>
<odoo>
    <record id="view_form_courses" model="ir.ui.view">
        <field name="name">Cursos - Form</field>
        <field name="model">courses.info</field>
        <field name="arch" type="xml">
            <form>
                <sheet>
                    <group>
                        <field name="branch_id"/>
                        <field name="subject_id"/>
                        <field name="professor_id"/>
                    </group>
                    <notebook>
                        <page string="Estudiantes Matriculados">
                            <field name="enrollment_ids">
                                <list editable="bottom">
                                    <field name="student_id"/>
                                    <field name="grade"/>
                                </list>
                            </field>
                        </page>
                    </notebook>
                </sheet>
            </form>
        </field>
    </record>
</odoo>
```

> `editable="bottom"` — editar directamente en la lista sin popup.

**One2many de solo lectura (no permitir crear/editar/borrar desde acá)**

Cuando el O2M embebido es solo para *ver* datos relacionados (el alta/edición real pasa por otro form, u otro rol es dueño de esos datos), sacar `editable` y bloquear las acciones de la lista:

```xml
<field name="grade_ids" nolabel="1">
    <list create="false" edit="false" delete="false">
        <field name="course_id"/>
        <field name="note"/>
        <field name="status_grade"/>
    </list>
</field>
```

- `create="false"` — sin botón "Agregar línea".
- `edit="false"` — las filas no abren para editar (ni inline ni popup).
- `delete="false"` — sin ícono de borrar por fila.
- Ejemplo real (`students.info`): el estudiante ve sus notas por curso (`grade_ids` → `grades.students`) pero no las puede tocar desde su propio form — esos datos se cargan desde otro lado.

> Sin estos tres atributos, un O2M sin `editable` igual deja abrir cada línea en popup y borrar filas — hay que apagar los tres explícitamente para que sea 100% solo-lectura.

### 6.3 Anatomía completa de `<form>`

```xml
<form>
    <!-- header: botones de acción + barra de estado -->
    <header>
        <button name="action_confirm" type="object"
                string="Confirmar" class="btn-primary"/>
        <button name="action_cancel" type="object"
                string="Cancelar"/>
        <field name="state" widget="statusbar"
               statusbar_visible="draft,confirmed,done"/>
    </header>

    <sheet>
        <!-- Imagen o avatar (opcional) -->
        <field name="image" widget="image" class="oe_avatar"/>

        <!-- group: 2 columnas por defecto -->
        <group>
            <field name="name"/>
            <field name="date"/>
        </group>

        <!-- group con título y columnas explícitas -->
        <group string="Información Académica" col="4">
            <field name="branch_id" colspan="2"/>
            <field name="subject_id"/>
            <field name="professor_id"/>
        </group>

        <!-- separator: línea divisora con título -->
        <separator string="Notas internas"/>

        <!-- div: layout libre -->
        <div class="oe_chatter"/>

        <!-- notebook: pestañas -->
        <notebook>
            <page string="Estudiantes">
                <field name="enrollment_ids">
                    <list editable="bottom">
                        <field name="student_id"/>
                        <field name="grade"/>
                    </list>
                </field>
            </page>
            <page string="Notas">
                <field name="description"/>
            </page>
        </notebook>
    </sheet>
</form>
```

### 6.4 Referencia rápida — elementos, atributos, widgets

**Elementos de `<form>`**

| Elemento | Uso |
|----------|-----|
| `<header>` | Botones de flujo + `statusbar`. Va antes de `<sheet>` |
| `<sheet>` | Contenedor principal del formulario |
| `<group>` | 2 columnas por defecto. `col="N"` cambia columnas. `string="..."` agrega título |
| `<notebook>` | Contenedor de pestañas |
| `<page string="...">` | Pestaña individual dentro de `<notebook>` |
| `<separator string="...">` | Línea divisora con título opcional |
| `<div>` | Bloque libre, útil para CSS personalizado |
| `<button>` | Botón de acción |
| `<field>` | Campo del modelo |

**Atributos de `<field>`**

| Atributo | Descripción | Ejemplo |
|----------|-------------|---------|
| `name` | Nombre del campo en el modelo | `name="state"` |
| `string` | Etiqueta visible (sobreescribe la del campo) | `string="Estado"` |
| `widget` | Cambia la forma de renderizar | `widget="many2many_tags"` |
| `invisible` | Oculta el campo (dominio o `True/False`) | `invisible="state == 'done'"` |
| `readonly` | Solo lectura condicional | `readonly="state != 'draft'"` |
| `required` | Requerido condicional | `required="is_active"` |
| `nolabel` | Oculta la etiqueta | `nolabel="1"` |
| `colspan` | Cuántas columnas ocupa dentro de `<group>` | `colspan="2"` |
| `options` | Opciones extra del widget (JSON) | `options="{'no_create': True}"` |
| `help` | Tooltip "?" junto a la etiqueta al hacer hover — sobreescribe el `help` del campo Python si se pone acá | `help="Ver detalle en pestaña Notas"` |

> El lugar recomendado para `help` es el campo en **Python** (`fields.Char(..., help="...")`), no la vista — así el tooltip aplica en todas las vistas que usan ese campo sin repetirlo. Sin `help` en ninguno de los dos lados, no aparece el ícono "?".

**`Integer` con separador de miles no deseado (ej: campo `year`)**

Por defecto, cualquier `fields.Integer` se muestra formateado según el locale — separador de miles incluido. Un año (`2026`) sale como `2,026`, lo cual no tiene sentido. Se apaga con la opción `enable_formatting` en `options`:

```xml
<field name="year" options="{'enable_formatting': false}"/>
```

> Aplica en form y list por separado — hay que ponerlo en cada `<field name="year"/>` que aparezca.

**Atributos de `<button>`**

| Atributo | Descripción | Ejemplo |
|----------|-------------|---------|
| `name` | Método Python a llamar | `name="action_confirm"` |
| `type="object"` | Llama método en el modelo | tipo más común |
| `type="action"` | Abre una `ir.actions.act_window` | para navegación |
| `string` | Texto visible del botón | `string="Confirmar"` |
| `class` | Estilo Bootstrap | `class="btn-primary"` |
| `invisible` | Ocultar según condición | `invisible="state != 'draft'"` |
| `confirm` | Muestra diálogo de confirmación | `confirm="¿Está seguro?"` |

**Widgets comunes**

| Widget | Campo | Resultado |
|--------|-------|-----------|
| `statusbar` | Selection/Many2one | Barra de progreso de estados |
| `many2many_tags` | Many2many | Etiquetas (chips) |
| `image` | Binary | Imagen con preview |
| `monetary` | Float | Muestra símbolo de moneda |
| `html` | Html | Editor rich text |
| `priority` | Selection | Estrellas de prioridad |
| `boolean_toggle` | Boolean | Toggle switch |
| `char_emojis` | Char | Input con emojis |

### 6.5 Interfaz (UI) — patrones de layout

**`<group>` es para pares cortos `label: valor`, no para texto largo.**

`<group>` arma una grilla de 2 columnas fija y comprime cualquier campo a una fila angosta, aunque el campo sea `Text` o `Html` — el widget se renderiza pero visualmente queda como un input de una línea, no como caja de texto.

**Regla práctica:**

| Tipo de campo | Dónde ponerlo | Por qué |
|---|---|---|
| `Char`, `Many2one`, `Date`, `Selection`, `Boolean` (valores cortos) | Dentro de `<group>` | Layout compacto, 2 columnas, es lo que `<group>` está diseñado para mostrar |
| `Text`, `Html`, campos con contenido extenso | **Fuera** de `<group>`, directo en `<sheet>` (o dentro de `<notebook><page>` si hay varios) | Necesitan ancho completo y altura variable — `<group>` los aprieta |

**Fix real** (`students.info` — campo `reports`, tipo `Html`):

```xml
<!-- Mal: adentro de group, sale como input de una línea -->
<group>
    ...
    <field name="reports"/>
</group>

<!-- Bien: fuera del group, ancho completo, editor rich text real -->
<group>
    ...
</group>
<separator string="Reportes del estudiante"/>
<field name="reports" nolabel="1"/>
```

- `nolabel="1"` — sin esto, al estar fuera de `<group>` el campo se muestra con su etiqueta arriba ocupando una fila propia igual; usar `nolabel` cuando el `<separator>` ya cumple el rol de título.
- `<separator string="...">` — línea divisora con título, sirve de header visual para la sección de texto largo.
- Mismo patrón aplica a `Text` (textarea simple) y a `One2many` con lista embebida grande (ver 6.2) — cualquier contenido que necesite más que una línea sale mejor fuera del `<group>`.

---

## 7. Menús y Acciones (view_menu.xml)

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<odoo>
    <!-- Acción: qué modelo abrir y en qué vistas -->
    <record id="action_mi_modelo" model="ir.actions.act_window">
        <field name="name">Mi Modelo</field>
        <field name="res_model">mi.modelo</field>
        <field name="view_mode">list,form</field>
    </record>

    <!-- Menú raíz -->
    <menuitem id="menu_raiz"
              action="action_mi_modelo"
              name="Mi Módulo"
    />

    <!-- Submenú -->
    <menuitem id="menu_hijo"
              parent="menu_raiz"
              action="action_otro"
              name="Submenu"
    />
</odoo>
```

---

## 8. Seguridad — ir.model.access.csv

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access.mi.modelo,access_mi_modelo,model_mi_modelo,base.group_user,1,1,1,1
```

- `model_id:id` → `model_` + nombre del modelo con `.` reemplazado por `_`
- Ejemplo: modelo `courses.info` → `model_courses_info`
- Permisos: `1` = sí, `0` = no (read, write, create, delete)

---

## 9. Scaffold — Crear módulo nuevo

### 9.1 make new-module — módulo completo desde cero

```bash
make new-module name=students description="Estudiantes" category="Students" author="Solvosoft"
```

- `name` — snake_case, se usa como nombre de carpeta en `extra_addons/` y como base del nombre técnico del modelo. Si `name` es una sola palabra (sin `_`), se agrega sufijo `.info` (ej: `students` → `students.info`). Si trae `_`, solo se convierte a `.` sin agregar sufijo (ej: `students_xd` → `students.xd`, `courses_info` → `courses.info`).
- `description` — opcional, texto legible para `__manifest__.py` y menú. Si se omite, usa `name`.
- `category` — opcional, categoría del módulo en `__manifest__.py`. Si se omite, usa `Uncategorized`.
- `author` — opcional, autor en `__manifest__.py`. Si se omite, queda vacío.

Genera:
```
extra_addons/students/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── students.py             # class Students(models.Model), _name = "students.info"
├── views/
│   ├── view_list.xml
│   ├── view_form.xml
│   └── view_menu.xml
└── security/
    └── ir.model.access.csv
```

También agrega el módulo a `modules.txt` (usado por `make install` / `make update`, ver sección 2.2).

Siguiente paso:
```bash
make install-module module=students
```

> Script: `scripts/new_module.sh`. Falla si el módulo ya existe o si `name` no es snake_case válido.

### 9.2 make new-view — list+form para un modelo ya escrito a mano

Para cuando ya armaste el modelo Python a mano (ej. `courses.students` en `models/courses.py`) y solo querés generar sus vistas + colgarlo del menú, sin repetir a mano el `<list>`/`<form>`/`<menuitem>`/fila de `ir.model.access.csv`.

```bash
make new-view model=courses.students module=students
make new-view model=courses.students module=students editable=1   # O2M embebidos editables en vez de solo-lectura
```

- `model` — nombre técnico del modelo (`_name`), ya tiene que existir en el registry (o sea, el módulo instalado con ese modelo cargado — corré `-u` antes si acabás de crear el modelo).
- `module` — carpeta del módulo en `extra_addons/`. Tiene que existir `menu_<module>` en `views/view_menu.xml` — si no existe, el comando falla en vez de inventar un menú nuevo.
- `editable` — opcional. Sin esto, los `One2many` embebidos en el form salen solo-lectura (`create="false" edit="false" delete="false"`, mismo patrón que 6.2).

**Qué genera para cada tipo de campo:**

| Tipo de campo | List | Form |
|---|---|---|
| `Char`, `Integer`, `Float`, `Boolean`, `Date`, `Selection`, `Many2one` | `<field name="x"/>` | igual |
| `Many2many` | `<field name="x_ids" widget="many2many_tags"/>` | igual |
| `One2many` | (se omite — no va en list) | embebido, con `<list>` solo mostrando el `_rec_name` del modelo relacionado |

**Si las vistas YA existen — modo update aditivo:** el comando busca entre los XML de `views/` cuál ya declara ese modelo (no asume ningún nombre de archivo), y agrega **solo** los campos del modelo que todavía no aparecen ahí — nunca borra, reordena ni toca `options`/`readonly`/separators que hayas puesto a mano. Si no falta ningún campo, no toca el archivo.

También agrega, si faltan: la fila del modelo en `ir.model.access.csv`, las líneas de los archivos nuevos en `__manifest__.py`, y el `<record ir.actions.act_window>` + `<menuitem parent="menu_<module>">` en `view_menu.xml`.

> Script: `scripts/new_view.py`. Necesita DB corriendo (usa el registry de Odoo para leer los campos reales del modelo, no parsea el `.py`).

### 9.3 make remove-view — inverso de 9.2

```bash
make remove-view model=courses.students module=students
```

Busca la(s) vista(s) de ese modelo (mismo criterio que 9.2 — por contenido, no por nombre asumido), las borra, y saca las referencias en `__manifest__.py`, `ir.model.access.csv` y `view_menu.xml` (el `<record ir.actions.act_window>` y el `<menuitem>` de ese modelo).

No toca la DB directamente — corré `make update-module module=<app>` (o dejá que `make dev` lo agarre) para que Odoo borre los registros (`ir.ui.view`, `ir.model.access`, `ir.actions.act_window`, `ir.ui.menu`) asociados a esos xmlids. Bajo riesgo: solo borra lo que el propio patrón de archivos de vista generó, no toca el modelo Python ni otras vistas.

> Script: `scripts/remove_view.py`.

### 9.4 make remove-module — borrar un módulo completo (destructivo)

```bash
make remove-module name=students
# o sin confirmación interactiva:
make remove-module name=students yes=1
```

**Irreversible.** A diferencia de 9.3, esto:
1. Desinstala el módulo desde Odoo (`button_immediate_uninstall`) — limpia tablas, `ir.model.data`, accesos, vistas y menús asociados en la DB.
2. Borra `extra_addons/<name>/` completo.
3. Lo saca de `modules.txt`.

Pide confirmación escribiendo el nombre del módulo (salvo `yes=1`). El orden importa: desinstala en DB **antes** de borrar la carpeta — al revés queda basura huérfana (tablas/registros sin módulo dueño), que es justo lo que pasó una vez en este proyecto por borrar la carpeta a mano sin desinstalar primero.

> Script: `scripts/remove_module.py`. Recomendado correrlo con `make dev` parado para evitar que el watcher intente recargar a mitad de la desinstalación.

---

## 10. Usuarios y Contraseñas

### 10.1 Comandos Makefile de usuarios

```bash
make create-user name="Juan Perez" login="juan@test.com" password="pass123"
make create-admin name="Admin User" login="admin2@test.com" password="pass123"
make change-password login="admin" password="nuevo123"
```

> Script: `scripts/manage_users.py`.

### 10.2 Contraseñas — dos conceptos distintos

| | Dónde se define | Para qué sirve |
|--|----------------|----------------|
| `admin_passwd` en `odoo.conf` | Archivo de configuración | Protege `/web/database/manager` (crear, borrar, backup DBs) |
| Usuario `admin` de la app | Se crea al inicializar DB | Login de la aplicación Odoo |

**URL de acceso:** `http://localhost:8069/web/database/manager`

Al inicializar DB nueva (via comando o auto), el usuario admin siempre inicia con:
- **Login:** `admin`
- **Password:** `admin`

No hay opción en `odoo.conf` para pre-definir el password del usuario admin.

### 10.3 Cambiar password del usuario admin

**Desde UI** (requiere modo developer activo):
`Settings → Users & Companies → Users → Administrator → ⚙ → Change Password`
> Pide el password actual → ingresar `admin`

**Desde terminal (shell):**
```bash
.venv/bin/python odoo-bin -c odoo.conf shell -d odoocurso_db
# o por Makefile:
make shell
```
```python
user = env['res.users'].browse(2)   # ID 2 = admin (ID 1 = OdooBot)
user.password = 'NuevoPassword123'
env.cr.commit()
exit()
```

O directo por Makefile (ver 10.1): `make change-password login="admin" password="nuevo123"`.

### 10.4 Crear DB con credenciales personalizadas

Usar el database manager en `/web/database/manager` — pide email y password al crear, evita el `admin`/`admin` por defecto.

---

## 11. Herramientas y Referencia

### 11.1 Comandos útiles (manual)

```bash
# Ver qué proceso usa el puerto 8069
lsof -i :8069

# Matar proceso Odoo
pkill -f odoo-bin
kill -9 <PID>

# Recrear DB desde cero
dropdb -U user_odoo odoocurso_db
createdb -U user_odoo odoocurso_db
python odoo-bin -c odoo.conf -i base
```

> Equivalentes por Makefile: `make port`, `make stop`, `make reset-db` (ver secciones 2.2 y 3.2).

### 11.2 Errores comunes

| Error | Causa | Fix |
|-------|-------|-----|
| `unknown comodel_name 'x.y'` | Nombre de modelo incorrecto en relación | Verificar `_name` del modelo destino |
| `KeyError: 'ir.http'` | DB no inicializada | `python odoo-bin -c odoo.conf -i base` |
| `OSError: [Errno 98]` | Puerto 8069 ocupado | `pkill -f odoo-bin` o `kill -9 <PID>` |
| Menús duplicados tras renombrar | Registros viejos en DB | Recrear DB o borrar desde Settings > Technical |
| `_compute_display_name` no actualiza | Falta `@api.depends` | Agregar decorator con campos dependientes |
| Many2many no sincroniza entre modelos | Falta tabla/columnas explícitas | Definir `relation`, `column1`, `column2` iguales en ambos lados |
| `No matching record found for external id 'model_x_y'` en `ir.model.access.csv` | El `model_id:id` del CSV no coincide con el modelo real reflejado (mismatch entre `_name` y lo que referencia el CSV), o estado de módulo corrupto por instalaciones parciales previas | Verificar que `model_id:id` = `model_` + `_name` con `.`→`_`; si persiste, chequear `ir_module_module.state` en DB y reinstalar limpio |

### 11.3 Plugins recomendados

**Para VS Code — extensión oficial Odoo**

**Nombre:** `Odoo` (publicada por Odoo SA)
**ID:** `Odoo.odoo`

```
Extensions (Ctrl+Shift+X) → buscar "Odoo" → instalar la de Odoo SA
```

**Qué incluye:**

| Característica | Detalle |
|---------------|---------|
| Snippets XML | `oform`, `olist`, `omenu`, `ofield`, `obutton`, etc. — genera estructura base |
| Snippets Python | `omodel`, `ochar`, `om2o`, `o2m`, `om2m` — genera campos y modelos |
| Autocompletado | Sugiere nombres de campos y modelos al escribir XML |
| Navegación | Ctrl+Click en `model="x.y"` abre el archivo Python del modelo |
| Resaltado | Colorea sintaxis de archivos XML de Odoo y decorators Python |

**Snippets más útiles en XML:**

| Snippet | Genera |
|---------|--------|
| `oform` | Estructura base de `<form>` con `<sheet>`, `<group>` |
| `olist` | Estructura base de `<list>` |
| `omenu` | `<menuitem>` con acción |
| `oaction` | `<record>` de `ir.actions.act_window` |
| `ofield` | `<field name=""/>` |
| `obutton` | `<button type="object"/>` |
| `onotebook` | `<notebook>` con `<page>` |

**Snippets más útiles en Python:**

| Snippet | Genera |
|---------|--------|
| `omodel` | Clase completa con `_name`, `_description`, campo `name` |
| `ochar` | `fields.Char(...)` |
| `om2o` | `fields.Many2one(...)` |
| `o2m` | `fields.One2many(...)` |
| `om2m` | `fields.Many2many(...)` |
| `ocompute` | Campo compute + método con `@api.depends` |

**Para el navegador — Odoo Debug**

**Nombre:** `Odoo Debug` (Chrome/Chromium)

Agrega botón en la barra del navegador para activar/desactivar `?debug=1` sin editar la URL manualmente. También muestra indicador visual cuando el modo está activo.