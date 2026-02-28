#!/usr/bin/env python3
"""
db_inspect.py – Listet alle Tabellen und Spalten der Datenbank auf.
"""
import sqlite3, os, sys

DB_PATH = os.environ.get(
    "VZ_DB_PATH",
    "/home/fabian/verbrannte_zone_project/verbrannte_zone.db"
)

if not os.path.exists(DB_PATH):
    print(f"❌ DB nicht gefunden: {DB_PATH}")
    sys.exit(1)

conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()

# Alle Tabellen
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cur.fetchall()]
print(f"\n📂 Datenbank: {DB_PATH}")
print(f"📋 Tabellen ({len(tables)}):\n")

for table in tables:
    cur.execute(f"PRAGMA table_info(\"{table}\")")
    cols = cur.fetchall()
    cur.execute(f"SELECT COUNT(*) FROM \"{table}\"")
    count = cur.fetchone()[0]
    print(f"  🗄️  {table}  ({count} Zeilen)")
    for col in cols:
        pk = " 🔑 PK" if col[5] else ""
        nn = " NOT NULL" if col[3] else ""
        print(f"      {col[1]:30s}  {col[2]}{pk}{nn}")
    print()

conn.close()
