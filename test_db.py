# -*- coding: utf-8 -*-
import sys
import os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    import psycopg2
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="ledger_db",
        user="postgres",
        password="8a356f0b61c14507801c127769293b43"
    )
    print("PostgreSQL connection OK")
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    result = cursor.fetchone()
    print("PostgreSQL version:", result[0][:50] if result else "N/A")
    conn.close()
except Exception as e:
    print("PostgreSQL connection failed:", type(e).__name__)
    try:
        print("Error:", str(e))
    except:
        print("Error: (unable to display)")