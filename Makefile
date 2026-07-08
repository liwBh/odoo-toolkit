SHELL = /bin/bash
PYTHON = .venv/bin/python
ODOO = $(PYTHON) odoo-bin
CONF = -c odoo.conf
DB = odoocurso_db
CUSTOM_MODULES = $(shell grep -v '^\s*#' modules.txt | grep -v '^\s*$$' | tr '\n' ',' | sed 's/,$$//')

# ── Setup inicial ─────────────────────────────────────────────────────────────

# make init-config db_name=curso_odoo db_user=odoo_user db_password=pass admin_passwd=Admin1234 [force=1]
init-config:
	@bash scripts/init_config.sh "$(admin_passwd)" "$(db_host)" "$(db_port)" "$(db_user)" "$(db_password)" "$(db_name)" "$(force)"

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
	$(ODOO) $(CONF) --dev=all

stop:
	pkill -f "[o]doo-bin" || true
	@while pgrep -f "[o]doo-bin" >/dev/null; do sleep 0.5; done

restart: stop run

# Auto-aplica -u + restart en cada cambio de extra_addons/**/*.{py,xml,csv}
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

install:
	$(ODOO) $(CONF) -i $(CUSTOM_MODULES) --stop-after-init

update:
	$(ODOO) $(CONF) -u $(CUSTOM_MODULES) --stop-after-init

install-module:
	$(ODOO) $(CONF) -i $(module) --stop-after-init

update-module:
	$(ODOO) $(CONF) -u $(module) --stop-after-init

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
	@echo "  make install                                      - Instalar módulos custom"
	@echo "  make update                                       - Actualizar módulos custom"
	@echo "  make install-module module=nombre                 - Instalar un módulo"
	@echo "  make update-module module=nombre                  - Actualizar un módulo"
	@echo "  make create-user name='' login='' password=''     - Crear usuario normal"
	@echo "  make create-admin name='' login='' password=''    - Crear usuario admin"
	@echo "  make change-password login='' password=''         - Cambiar password"
	@echo "  make shell                                        - Abrir shell interactivo"
	@echo "  make port                                         - Ver proceso en puerto 8069"
	@echo ""

.PHONY: init-config setup run stop restart dev init-db reset-db new-module install update \
        install-module update-module create-user create-admin change-password port shell help