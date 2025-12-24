# -*- coding: utf-8 -*-
from pathlib import Path
from dotenv import load_dotenv
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv(Path("backend/.env"))

from backend.app.models.coupang_account import decrypt_value
import sqlite3

conn = sqlite3.connect(r'backend\database\coupang_cs.db')
cursor = conn.cursor()

cursor.execute('SELECT access_key_encrypted, secret_key_encrypted FROM coupang_accounts WHERE is_active = 1 LIMIT 1')
result = cursor.fetchone()

if result:
    access_key = decrypt_value(result[0])
    secret_key = decrypt_value(result[1])

    print(f'Access key length: {len(access_key)}')
    print(f'Secret key length: {len(secret_key)}')
    print(f'Access key (first 5 chars): {access_key[:5] if access_key else "EMPTY"}')
    print(f'Secret key (first 5 chars): {secret_key[:5] if secret_key else "EMPTY"}')
else:
    print('No active account')

conn.close()
