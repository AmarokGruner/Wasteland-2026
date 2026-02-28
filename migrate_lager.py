#!/usr/bin/env python3
"""
migrate_lager.py
Legt die fehlenden Tabellen 'provinzen' und 'provinz_lager' an
und ergaenzt 'ressourcen' um eine 'icon'-Spalte (falls nicht vorhanden).
Idempotent – kann beliebig oft ausgefuehrt werden.
"""
import sqlite3, os, sys

DB_PATH = os.environ.get(
    "VZ_DB_PATH",
    "/home/fabian/verbrannte_zone_project/verbrannte_zone.db"
)

if not os.path.exists(DB_PATH):
    print(f"X DB nicht gefunden: {DB_PATH}")
    sys.exit(1)

conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()

# ── 1. Tabelle: provinzen ────────────────────────────────────────────────────
cur.execute("""
    CREATE TABLE IF NOT EXISTS provinzen (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id       INTEGER NOT NULL,
        world_x         INTEGER NOT NULL,
        world_y         INTEGER NOT NULL,
        name            TEXT,
        lagerkapazitaet INTEGER DEFAULT 1000,
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(world_x, world_y)
    )
""")
print("✅ Tabelle 'provinzen' sichergestellt")

# ── 2. Tabelle: provinz_lager ────────────────────────────────────────────────
cur.execute("""
    CREATE TABLE IF NOT EXISTS provinz_lager (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        provinz_id   INTEGER NOT NULL REFERENCES provinzen(id),
        ressource_id INTEGER NOT NULL REFERENCES ressourcen(id),
        menge        INTEGER NOT NULL DEFAULT 0,
        created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(provinz_id, ressource_id)
    )
""")
print("✅ Tabelle 'provinz_lager' sichergestellt")

# ── 3. Spalte 'icon' in ressourcen (falls fehlt) ─────────────────────────────
cur.execute("PRAGMA table_info(ressourcen)")
cols = [row[1] for row in cur.fetchall()]
if "icon" not in cols:
    cur.execute("ALTER TABLE ressourcen ADD COLUMN icon TEXT")
    print("✅ Spalte 'icon' zu 'ressourcen' hinzugefuegt")

    # Standard-Icons nach typ oder name setzen
    icon_map = [
        ("%Holz%",    "🪵"),
        ("%Stein%",   "🪨"),
        ("%Wasser%",  "💧"),
        ("%Nahrung%", "🌾"),
        ("%Metall%",  "⚙️"),
        ("%Erz%",     "⛏️"),
        ("%Energie%", "⚡"),
        ("%Kohle%",   "🖤"),
        ("%Eisen%",   "🔩"),
        ("%Stahl%",   "🔧"),
        ("%Öl%",      "🛢️"),
        ("%Brennstoff%", "⛽"),
    ]
    for pattern, emoji in icon_map:
        cur.execute(
            "UPDATE ressourcen SET icon=? WHERE name LIKE ? AND icon IS NULL",
            (emoji, pattern)
        )
    # Rest: generisches Symbol
    cur.execute("UPDATE ressourcen SET icon='📦' WHERE icon IS NULL")
    print("   Icons nach Name/Typ vorbelegt (änderbar per UPDATE)")
else:
    print("✅ Spalte 'icon' bereits vorhanden")

conn.commit()
conn.close()
print("\n✅ Migration abgeschlossen. Jetzt seed_lager_provinz_12_20.py ausfuehren.")
