#!/usr/bin/env python3
"""
Script to clear Odoo action cache and force reload
Run: python clear_cache.py
"""

import xmlrpc.client

# Odoo connection settings
url = 'http://localhost:8070'
db = 'test8'
username = 'admin'  # Change this
password = 'admin'  # Change this

# Connect
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

if not uid:
    print("Authentication failed!")
    exit(1)

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Clear action cache
print("Clearing action cache...")
action_ids = models.execute_kw(db, uid, password,
    'ir.actions.act_window', 'search',
    [[('res_model', '=', 'product.creation.wizard')]])

if action_ids:
    print(f"Found {len(action_ids)} actions to refresh")
    for action_id in action_ids:
        action = models.execute_kw(db, uid, password,
            'ir.actions.act_window', 'read',
            [action_id], {'fields': ['name', 'context']})
        print(f"  - {action[0]['name']}: {action[0].get('context', 'N/A')}")

# Clear view cache
print("\nClearing view cache...")
models.execute_kw(db, uid, password,
    'ir.ui.view', 'clear_caches', [[]])

print("\nCache cleared! Please refresh your browser (Ctrl+Shift+R)")
