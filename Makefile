SHELL = /bin/bash
PYTHON = .venv/bin/python
ODOO = $(PYTHON) odoo-bin
CONF = -c odoo.conf
DB = $(shell grep -E '^\s*db_name' odoo.conf 2>/dev/null | tail -1 | cut -d'=' -f2 | tr -d ' ')
CUSTOM_MODULES = $(shell grep -v '^\s*#' modules.txt | grep -v '^\s*$$' | tr '\n' ',' | sed 's/,$$//')
CUSTOM_MODULES_SPACED = $(shell grep -v '^\s*#' modules.txt | grep -v '^\s*$$' | tr '\n' ' ')

# ── Setup inicial ─────────────────────────────────────────────────────────────

# make init-config db_name=curso_odoo db_user=odoo_user db_password=pass admin_passwd=Admin1234 [force=1] [http_port=8069]
init-config:
	@bash scripts/init_config.sh "$(admin_passwd)" "$(db_host)" "$(db_port)" "$(db_user)" "$(db_password)" "$(db_name)" "$(force)" "$(http_port)"

setup:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt
	.venv/bin/pip install watchdog
	mkdir -p extra_addons
	@echo ""
	@echo "Entorno listo. Continúa con: make init-db && make install"

# ── Servidor ──────────────────────────────────────────────────────────────────

run:
	@PORT=$$(grep -E '^\s*http_port' odoo.conf 2>/dev/null | tail -1 | cut -d'=' -f2 | tr -d ' '); \
	echo "[run] servidor en http://localhost:$${PORT:-8069}"
	$(ODOO) $(CONF) --dev=all

stop:
	pkill -f "[o]doo-bin" || true
	@while pgrep -f "[o]doo-bin" >/dev/null; do sleep 0.5; done

restart: stop run

# Auto-aplica -u + restart en cada cambio de extra_addons/**/*.{py,xml,csv,po,css,scss,js}
dev: stop
	$(PYTHON) scripts/dev_watch.py

# ── Base de datos ─────────────────────────────────────────────────────────────

init-db:
	$(ODOO) $(CONF) -i base --stop-after-init

reset-db: stop
	dropdb -U user_odoo $(DB) || true
	createdb -U user_odoo $(DB)
	$(MAKE) init-db

# ── Módulos ───────────────────────────────────────────────────────────────────

# make new-module name=students description="Estudiantes" category="Students" author="Solvosoft"
new-module:
	@bash scripts/new_module.sh "$(name)" "$(description)" "$(category)" "$(author)"

# make new-view model=courses.students module=students [editable=1]
# Crea (o actualiza de forma aditiva) list+form para un modelo ya existente
# y lo cuelga de menu_<module> (debe existir). Requiere DB con el módulo instalado.
new-view:
	@$(PYTHON) scripts/new_view.py --model "$(model)" --module "$(module)" $(if $(editable),--editable,)

# make remove-view model=courses.students module=students
# Borra la(s) vista(s) generadas para ese modelo + referencias en manifest/csv/menú.
# No toca la DB — corré update-module después.
remove-view:
	@$(PYTHON) scripts/remove_view.py --model "$(model)" --module "$(module)"

# make remove-module name=students [yes=1]
# DESTRUCTIVO: desinstala el módulo de la DB (limpia tablas/registros) y borra
# extra_addons/<name>/ completo. Pide confirmación salvo yes=1.
remove-module:
	@$(PYTHON) scripts/remove_module.py --name "$(name)" $(if $(yes),--yes,)

install:
	$(ODOO) $(CONF) -i $(CUSTOM_MODULES) --stop-after-init

update:
	$(ODOO) $(CONF) -u $(CUSTOM_MODULES) --stop-after-init

install-module:
	$(ODOO) $(CONF) -i $(module) --stop-after-init

update-module:
	$(ODOO) $(CONF) -u $(module) --stop-after-init

# ── Traducciones ──────────────────────────────────────────────────────────────

# make trans-loadlang [lang="es_419 en_US"]   — sin lang, instala en_US y es_419 (default de este proyecto)
trans-loadlang:
	$(PYTHON) odoo-bin i18n loadlang $(CONF) -d $(DB) -l $(if $(lang),$(lang),en_US es_419)

# make trans-export [lang=es_419]   — sin lang, genera solo el .pot (template)
# OJO: pisa el .po/.pot existente con lo que haya en la DB — no usar si tenés
# ediciones a mano sin importar todavía (make trans-import antes de re-exportar).
# Para actualizar un .po de idioma sin perder lo ya traducido, usar trans-sync.
trans-export:
	$(PYTHON) odoo-bin i18n export $(CONF) -d $(DB) $(CUSTOM_MODULES_SPACED) -l $(if $(lang),$(lang),pot)

# make trans-sync lang=es_419   — regenera el .po de lang para cada módulo,
# preservando los msgstr que ya estaban traducidos (no los pisa como trans-export)
trans-sync:
	@if [ -z "$(lang)" ]; then echo "Uso: make trans-sync lang=es_419"; exit 1; fi
	$(PYTHON) scripts/trans_sync.py odoo.conf $(DB) $(lang) $(CUSTOM_MODULES_SPACED)

# make trans-scaffold lang=es_419   — crea el .po de lang SOLO para módulos que
# todavía no lo tienen (no pisa los existentes, a diferencia de trans-export)
trans-scaffold:
	@if [ -z "$(lang)" ]; then echo "Uso: make trans-scaffold lang=es_419"; exit 1; fi
	@for mod in $(CUSTOM_MODULES_SPACED); do \
		po="extra_addons/$$mod/i18n/$(lang).po"; \
		if [ -f "$$po" ]; then \
			echo "[trans-scaffold] $$po ya existe, no se toca"; \
		else \
			echo "[trans-scaffold] creando $$po"; \
			$(PYTHON) odoo-bin i18n export $(CONF) -d $(DB) $$mod -l $(lang); \
		fi; \
	done

# make trans-import lang=es_419 [overwrite=1]
trans-import:
	$(PYTHON) odoo-bin i18n import $(CONF) -d $(DB) extra_addons/students/i18n/$(lang).po -l $(lang) $(if $(overwrite),-w,)

# ── Usuarios ──────────────────────────────────────────────────────────────────

# make create-user name="Juan Perez" login="juan@test.com" password="pass123"
create-user:
	$(PYTHON) scripts/manage_users.py create-user --name "$(name)" --login "$(login)" --password "$(password)"

# make create-admin name="Admin User" login="admin2@test.com" password="pass123"
create-admin:
	$(PYTHON) scripts/manage_users.py create-admin --name "$(name)" --login "$(login)" --password "$(password)"

# make change-password login="admin" password="nuevo123"
change-password:
	$(PYTHON) scripts/manage_users.py change-password --login "$(login)" --password "$(password)"

# ── Info ──────────────────────────────────────────────────────────────────────

port:
	lsof -i :8069 || echo "Puerto 8069 libre"

shell:
	$(ODOO) $(CONF) shell -d $(DB)

help:
	@echo ""
	@echo "Comandos disponibles:"
	@echo "  make init-config db_name='' db_user='' ...        - Crear odoo.conf"
	@echo "  make setup                                        - Crear venv e instalar dependencias"
	@echo "  make run                                          - Iniciar Odoo"
	@echo "  make stop                                         - Detener Odoo"
	@echo "  make restart                                      - Reiniciar Odoo"
	@echo "  make dev                                          - Auto -u + restart al guardar cambios"
	@echo "  make init-db                                      - Inicializar DB con base"
	@echo "  make reset-db                                     - Borrar y recrear DB"
	@echo "  make new-module name='' description='' category=''- Crear módulo nuevo (scaffold)"
	@echo "  make new-view model='' module='' [editable=1]     - Crear/actualizar list+form para un modelo"
	@echo "  make remove-view model='' module=''               - Borrar vista(s) generadas de un modelo"
	@echo "  make remove-module name='' [yes=1]                - Desinstalar y borrar un módulo (destructivo)"
	@echo "  make install                                      - Instalar módulos custom"
	@echo "  make update                                       - Actualizar módulos custom"
	@echo "  make install-module module=nombre                 - Instalar un módulo"
	@echo "  make update-module module=nombre                  - Actualizar un módulo"
	@echo "  make trans-loadlang [lang='']                      - Instalar idioma(s) en la DB (default: en_US es_419)"
	@echo "  make trans-export [lang='']                       - Exportar .pot (o .po de lang) a i18n/ (pisa lo existente)"
	@echo "  make trans-sync lang=''                            - Actualizar .po de lang preservando lo ya traducido"
	@echo "  make trans-scaffold lang=''                        - Crear .po de lang solo donde no existe (no pisa)"
	@echo "  make trans-import lang='' [overwrite=1]            - Importar .po de lang a la DB"
	@echo "  make create-user name='' login='' password=''     - Crear usuario normal"
	@echo "  make create-admin name='' login='' password=''    - Crear usuario admin"
	@echo "  make change-password login='' password=''         - Cambiar password"
	@echo "  make shell                                        - Abrir shell interactivo"
	@echo "  make port                                         - Ver proceso en puerto 8069"
	@echo ""

.PHONY: init-config setup run stop restart dev init-db reset-db new-module new-view remove-view remove-module \
        install update install-module update-module trans-loadlang trans-export trans-sync trans-scaffold \
        trans-import create-user create-admin \
        change-password port shell help