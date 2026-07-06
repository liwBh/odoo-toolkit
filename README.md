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

## Uso en un proyecto Odoo

Los scripts y el `Makefile` asumen que corren desde la raíz de un checkout de Odoo (usan rutas relativas: `./addons`, `./extra_addons`, `.venv/bin/python`, `odoo.conf`).

Conectar por symlink (mismo filesystem, sin git submodule):

```bash
cd /ruta/al/proyecto-odoo
ln -s ../odoo-toolkit/Makefile Makefile
ln -s ../odoo-toolkit/Apuntes.md Apuntes.md
ln -s ../odoo-toolkit/scripts scripts
```

Ajustar la ruta relativa (`../odoo-toolkit`) según dónde esté el proyecto respecto a este repo.

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