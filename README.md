# odoo-toolkit

Kit reusable para gestionar proyectos de desarrollo Odoo: notas, `Makefile` y scripts de automatización (crear módulos, generar `odoo.conf`, etc).

## Contenido

```
odoo-toolkit/
├── Apuntes.md          # notas de desarrollo Odoo (modelos, vistas, seguridad, comandos)
├── Makefile            # comandos make (setup, run, init-db, new-module, init-config, ...)
└── scripts/
    ├── init_config.sh  # genera odoo.conf
    └── new_module.sh   # scaffold de módulo nuevo
```

## Instalación

Clonar como directorio hermano de tus proyectos Odoo:

```bash
git clone git@github.com:liwBh/odoo-toolkit.git
```

## Uso en un proyecto Odoo

Los scripts y el `Makefile` asumen que corren desde la raíz de un checkout de Odoo (usan rutas relativas: `./addons`, `./extra_addons`, `.venv/bin/python`, `odoo.conf`).

Conectar por symlink (mismo filesystem, sin git submodule) — usando `link.sh`:

```bash
odoo-toolkit/link.sh /ruta/al/proyecto-odoo
```

Esto crea `Apuntes.md`, `Makefile` y `scripts` como symlinks hacia `odoo-toolkit/` dentro del proyecto. Falla si alguno de esos ya existe como archivo real (para no pisar trabajo existente sin querer).

Alternativa manual (mismo resultado):

```bash
cd /ruta/al/proyecto-odoo
ln -s ../odoo-toolkit/Makefile Makefile
ln -s ../odoo-toolkit/Apuntes.md Apuntes.md
ln -s ../odoo-toolkit/scripts scripts
```

Ajustar la ruta relativa (`../odoo-toolkit`) según dónde esté el proyecto respecto a este repo.

### Alternativa: copia manual (recomendada para equipo)

El symlink asume que ambos repos están clonados en la misma ruta relativa — se rompe si otro dev clona en otra ubicación, o en Windows/CI/Docker. Para distribuir a un equipo, es más simple copiar los archivos (sin symlink):

```bash
git clone git@github.com:liwBh/odoo-toolkit.git
cp odoo-toolkit/Makefile /ruta/al/proyecto-odoo/Makefile
cp odoo-toolkit/Apuntes.md /ruta/al/proyecto-odoo/Apuntes.md
cp -r odoo-toolkit/scripts /ruta/al/proyecto-odoo/scripts
```

Cada proyecto queda autocontenido — no depende de que `odoo-toolkit` siga existiendo en esa ruta. A cambio, mejoras futuras al toolkit no se propagan solas: hay que repetir el `cp` para actualizar.

## Comandos principales

```bash
make init-config db_name=mi_db db_user=mi_user db_password=pass admin_passwd=Admin1234
make setup
make init-db
make run
make new-module name=mi_modulo description="Mi Módulo" category="Categoria"
make help
```

Ver `Apuntes.md` para detalle de cada comando y conceptos de Odoo.