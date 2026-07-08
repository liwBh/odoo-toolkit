#!/usr/bin/env python3
"""
Uso:
  python scripts/manage_users.py create-user  --name "Juan" --login "juan@test.com" --password "pass"
  python scripts/manage_users.py create-admin  --name "Admin" --login "admin2@test.com" --password "pass"
  python scripts/manage_users.py change-password --login "admin" --password "nuevo"
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import odoo
from odoo.tools import config

config.parse_config(['-c', 'odoo.conf'])

import odoo.modules.registry
from odoo import SUPERUSER_ID, api
import odoo.service.db

DB = config['db_name']
if isinstance(DB, list):
    DB = DB[0]


def create_user(name, login, password, is_admin=False):
    odoo.service.db._create_empty_database  # ensure db module loaded
    reg = odoo.modules.registry.Registry.new(DB)
    with reg.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        if env['res.users'].search_count([('login', '=', login)]):
            print(f"Error: ya existe un usuario con login '{login}'")
            sys.exit(1)
        user = env['res.users'].create({
            'name': name,
            'login': login,
            'password': password,
        })
        if is_admin:
            group = env.ref('base.group_system')
            group.user_ids = [(4, user.id)]
        cr.commit()
        print(f"Usuario creado: {login} (ID: {user.id})")


def change_password(login, password):
    reg = odoo.modules.registry.Registry.new(DB)
    with reg.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        user = env['res.users'].search([('login', '=', login)], limit=1)
        if not user:
            print(f"Error: usuario '{login}' no encontrado")
            sys.exit(1)
        user.password = password
        cr.commit()
        print(f"Password actualizado: {login}")


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')

    for cmd in ['create-user', 'create-admin']:
        p = subparsers.add_parser(cmd)
        p.add_argument('--name', required=True)
        p.add_argument('--login', required=True)
        p.add_argument('--password', required=True)

    p = subparsers.add_parser('change-password')
    p.add_argument('--login', required=True)
    p.add_argument('--password', required=True)

    args = parser.parse_args()

    if args.command == 'create-user':
        create_user(args.name, args.login, args.password, is_admin=False)
    elif args.command == 'create-admin':
        create_user(args.name, args.login, args.password, is_admin=True)
    elif args.command == 'change-password':
        change_password(args.login, args.password)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()