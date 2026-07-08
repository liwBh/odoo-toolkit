# Apuntes Odoo 19 — Desarrollo de Módulos

## 1. Instalación inicial

### Clonar repositorio
```bash
git clone https://github.com/odoo/odoo.git --branch 19.0 --depth 1 odoo-19.0
cd odoo-19.0
```

### Crear entorno virtual e instalar dependencias
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 2. Configuración — odoo.conf

```ini
[options]
admin_passwd = Admin1234
db_host = localhost
db_port = 5432
db_user = user_odoo
db_password = <password>
db_name = odoocurso_db
addons_path = ./addons,./extra_addons
```

- `addons_path` incluye carpeta `extra_addons` para módulos custom.

Crear carpeta si no existe:
```bash
mkdir -p extra_addons
```

### Crear odoo.conf con Makefile

```bash
make init-config db_name=curso_odoo db_user=odoo_user db_password=Admin1234 admin_passwd=Admin1234
```

- Todos los parámetros son opcionales (defaults: `admin_passwd=Admin1234`, `db_host=localhost`, `db_port=5432`, `db_user=odoo_user`, `db_password=<db_user>`, `db_name=odoo_db`).
- `addons_path` siempre queda `./addons,./extra_addons` y crea la carpeta `extra_addons` si no existe.
- Si `odoo.conf` ya existe, rechaza sobreescribir — usar `force=1` para forzar:
```bash
make init-config db_name=curso_odoo force=1
```

> Script: `scripts/init_config.sh`.

---

## 3. Inicializar base de datos

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

---

## 4. Estructura de un módulo

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

---

## 5. __manifest__.py

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

## 6. Modelos

### Modelo básico
```python
from odoo import fields, models

class MiModelo(models.Model):
    _name = 'mi.modelo'          # nombre técnico — define tabla en DB

    name = fields.Char(string='Nombre', required=True)
    descripcion = fields.Text(string='Descripción')
    activo = fields.Boolean(default=True)
```

### Herencia — tres casos de `_inherit`

**Regla rápida:**

| `_name` | `_inherit` | Resultado |
|---------|-----------|-----------|
| No | Sí | Modifica modelo existente (misma tabla) |
| Sí | Sí | Crea modelo nuevo con campos heredados (tabla nueva) |

---

**Caso 1 — Extender modelo de OTRO módulo (agregar campos)**
```python
# En students_managments — agrega campo a courses.info que vive en subjects_managments
class CourseExtended(models.Model):
    _inherit = 'courses.info'    # sin _name → modifica el modelo existente

    enrollment_ids = fields.One2many('courses.students', 'course_id', string='Matrículas')
```
No crea tabla nueva. Agrega columna a `courses_info` existente.
Útil para evitar dependencias circulares entre módulos.

---

**Caso 2 — Crear modelo nuevo con campos heredados**
```python
# professors.info hereda campos de persons.info
class Professor(models.Model):
    _name = 'professors.info'    # con _name → modelo nuevo
    _inherit = ['persons.info']  # copia campos de persons.info

    campo_extra = fields.Char(string='Extra')
```
Crea tabla nueva `professors_info` con los campos copiados de `persons_info`.

---

**Caso 3 — Extender modelos nativos de Odoo**
```python
# Agregar campo a res.partner (contactos nativos de Odoo)
class ResPartner(models.Model):
    _inherit = 'res.partner'

    mi_campo = fields.Char(string='Mi Campo')
```

### display_name personalizado
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

---

## 7. Tipos de campos relacionales

### Many2one — muchos a uno
```python
# Muchos cursos → un profesor
professor_id = fields.Many2one('professors.info', string='Profesor')
```

### One2many — uno a muchos (inverso de Many2one)
```python
# Un curso → muchas matrículas
enrollment_ids = fields.One2many('courses.students', 'course_id', string='Matrículas')
```
> Requiere que el modelo destino tenga el `Many2one` correspondiente (`course_id`).

### Many2many — muchos a muchos
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

### Modelo intermedio con datos extra (matrícula con nota)
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

## 8. Vistas

### Lista (view_list.xml)
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

### Formulario con One2many embebido (view_form.xml)
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

---

### Anatomía completa de `<form>`

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

### Elementos de `<form>` — referencia rápida

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

### Atributos de `<field>`

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

### Atributos de `<button>`

| Atributo | Descripción | Ejemplo |
|----------|-------------|---------|
| `name` | Método Python a llamar | `name="action_confirm"` |
| `type="object"` | Llama método en el modelo | tipo más común |
| `type="action"` | Abre una `ir.actions.act_window` | para navegación |
| `string` | Texto visible del botón | `string="Confirmar"` |
| `class` | Estilo Bootstrap | `class="btn-primary"` |
| `invisible` | Ocultar según condición | `invisible="state != 'draft'"` |
| `confirm` | Muestra diálogo de confirmación | `confirm="¿Está seguro?"` |

### Widgets comunes

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

---

## 9. Menús y acciones (view_menu.xml)

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

## 10. Seguridad — ir.model.access.csv

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access.mi.modelo,access_mi_modelo,model_mi_modelo,base.group_user,1,1,1,1
```

- `model_id:id` → `model_` + nombre del modelo con `.` reemplazado por `_`
- Ejemplo: modelo `courses.info` → `model_courses_info`
- Permisos: `1` = sí, `0` = no (read, write, create, delete)

---

## 11. Errores comunes

| Error | Causa | Fix |
|-------|-------|-----|
| `unknown comodel_name 'x.y'` | Nombre de modelo incorrecto en relación | Verificar `_name` del modelo destino |
| `KeyError: 'ir.http'` | DB no inicializada | `python odoo-bin -c odoo.conf -i base` |
| `OSError: [Errno 98]` | Puerto 8069 ocupado | `pkill -f odoo-bin` o `kill -9 <PID>` |
| Menús duplicados tras renombrar | Registros viejos en DB | Recrear DB o borrar desde Settings > Technical |
| `_compute_display_name` no actualiza | Falta `@api.depends` | Agregar decorator con campos dependientes |
| Many2many no sincroniza entre modelos | Falta tabla/columnas explícitas | Definir `relation`, `column1`, `column2` iguales en ambos lados |

---

## 12. Contraseñas — dos conceptos distintos

| | Dónde se define | Para qué sirve |
|--|----------------|----------------|
| `admin_passwd` en `odoo.conf` | Archivo de configuración | Protege `/web/database/manager` (crear, borrar, backup DBs) |
| Usuario `admin` de la app | Se crea al inicializar DB | Login de la aplicación Odoo |

**URL de acceso:** `http://localhost:8069/web/database/manager`

Al inicializar DB nueva (via comando o auto), el usuario admin siempre inicia con:
- **Login:** `admin`
- **Password:** `admin`

No hay opción en `odoo.conf` para pre-definir el password del usuario admin.

### Cambiar password del usuario admin

**Desde UI** (requiere modo developer activo):
`Settings → Users & Companies → Users → Administrator → ⚙ → Change Password`
> Pide el password actual → ingresar `admin`

**Desde terminal (shell):**
```bash
.venv/bin/python odoo-bin -c odoo.conf shell -d odoocurso_db
```
```python
user = env['res.users'].browse(2)   # ID 2 = admin (ID 1 = OdooBot)
user.password = 'NuevoPassword123'
env.cr.commit()
exit()
```

### Crear DB con credenciales personalizadas

Usar el database manager en `/web/database/manager` — pide email y password al crear, evita el `admin`/`admin` por defecto.

---

## 13. Comandos útiles

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

---

## 14. Modo Desarrollador (Developer Mode)

### Activar

**Opción 1 — URL (más rápido):**
```
http://localhost:8069/web?debug=1
```
> Agrega `?debug=1` a cualquier URL de Odoo. Se mantiene activo mientras navegas.

**Opción 2 — Debug de assets (JS/CSS sin minificar):**
```
http://localhost:8069/web?debug=assets
```
> Útil para depurar JavaScript o CSS en el navegador.

**Opción 3 — Desde la UI:**
`Settings → General Settings → (scroll al fondo) → Developer Tools → Activate the developer mode`

**Opción 4 — Desde menú debug en URL:**
```
http://localhost:8069/web?debug=0
```
> Desactiva el modo desarrollador.

### Qué habilita el modo desarrollador

| Función | Descripción |
|---------|-------------|
| Menú **Technical** en Settings | Acceso a ir.model, ir.fields, ir.ui.view, acciones, menús, secuencias, etc. |
| Info de campos al hacer hover | Al pasar el mouse sobre una etiqueta de campo muestra nombre técnico, tipo, módulo |
| Inspector de vistas | Botón "Edit View" en cada formulario/lista para ver y editar el XML directamente |
| **Debug** en menú de engranaje | Opciones extra en el menú ⚙ de cada registro |
| Campos técnicos visibles | Muestra campos como `id`, `create_date`, `write_uid` en los formularios |
| Regenerar assets | Fuerza recompilación de JS/CSS |

### Accesos directos con modo desarrollador activo

- **Settings → Technical → User Interface → Views** — listar/editar todas las vistas XML
- **Settings → Technical → Database Structure → Models** — ver todos los modelos y sus campos
- **Settings → Technical → Actions → Window Actions** — ver acciones registradas
- **Settings → Technical → User Interface → Menus** — ver árbol de menús

### Modo desarrollador al iniciar servidor

```bash
# --dev=all activa auto-reload de vistas XML y Python sin reiniciar
.venv/bin/python odoo-bin -c odoo.conf --dev=all
```

| Flag `--dev` | Efecto |
|-------------|--------|
| `all` | Todo: XML reload, Python reload, debug mode |
| `xml` | Solo recarga vistas XML sin reiniciar |
| `reload` | Recarga Python al detectar cambios |
| `qweb` | No cachea templates QWeb |

---

## 15. Plugin recomendado

### Para VS Code — extensión oficial Odoo

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

### Para el navegador — Odoo Debug

**Nombre:** `Odoo Debug` (Chrome/Chromium)

Agrega botón en la barra del navegador para activar/desactivar `?debug=1` sin editar la URL manualmente. También muestra indicador visual cuando el modo está activo.

---

## 16. Iniciar la app con Makefile

Pasos en orden:

1. Crear archivo de configuración `odoo.conf` (ver sección 2).

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

> `make init-db` corre `-i base --stop-after-init` (una sola vez, DB vacía). `make run` levanta con `--dev=all`.

Ver todos los comandos disponibles:
```bash
make help
```

---

## 17. Crear módulo nuevo (scaffold)

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

También agrega el módulo a `modules.txt` (usado por `make install` / `make update`).

Siguiente paso:
```bash
make install-module module=students
```

> Script: `scripts/new_module.sh`. Falla si el módulo ya existe o si `name` no es snake_case válido.