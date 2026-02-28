#!/usr/bin/env python3
"""
seed_lager_provinz_12_20.py
Befuellt das Lager der Spieler-Provinz (world_x=12, world_y=20).

Voraussetzung: migrate_lager.py wurde bereits ausgefuehrt.
"""
import sqlite3, os, sys

DB_PATH = os.environ.get(
    "VZ_DB_PATH",
    "/home/fabian/verbrannte_zone_project/verbrannte_zone.db"
)
PLAYER_ID = 1
WORLD_X   = 12
WORLD_Y   = 20

# Ziel-Lagerbestand
LAGER_DATEN = [
    ("Bauholz", 120),   # ← korrigiert: war "Holz"
    ("Stein",    50),
    ("Wasser",  200),
]

if not os.path.exists(DB_PATH):
    print(f"X DB nicht gefunden: {DB_PATH}")
    sys.exit(1)

conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()

# ── Sicherheitscheck: provinzen-Tabelle vorhanden? ───────────────────────────
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='provinzen'")
if not cur.fetchone():
    print("❌ Tabelle 'provinzen' fehlt. Erst ausfuehren: python migrate_lager.py")
    conn.close()
    sys.exit(1)

# ── Provinz suchen oder anlegen ──────────────────────────────────────────────
cur.execute(
    "SELECT id, lagerkapazitaet FROM provinzen WHERE player_id=? AND world_x=? AND world_y=?",
    (PLAYER_ID, WORLD_X, WORLD_Y)
)
row = cur.fetchone()

if row:
    provinz_id, kapazitaet = row
    print(f"✅ Provinz gefunden: ID={provinz_id} | Kapazitaet={kapazitaet}")
else:
    print(f"⚠️  Provinz ({WORLD_X},{WORLD_Y}) nicht gefunden → wird angelegt")
    cur.execute(
        """INSERT INTO provinzen (player_id, world_x, world_y, name, lagerkapazitaet)
           VALUES (?, ?, ?, ?, ?)""",
        (PLAYER_ID, WORLD_X, WORLD_Y, f"Provinz {WORLD_X}/{WORLD_Y}", 1000)
    )
    provinz_id = cur.lastrowid
    print(f"✅ Provinz angelegt: ID={provinz_id}")

# ── Verfuegbare Ressourcen (Debugging) ──────────────────────────────────────
cur.execute("SELECT id, name, typ FROM ressourcen ORDER BY name")
alle_res  = cur.fetchall()
res_namen = {r[1]: r[0] for r in alle_res}

print(f"\n📦 Setze {len(LAGER_DATEN)} Lagereintraege:")

# ── Lagerbestand setzen ──────────────────────────────────────────────────────
gefunden = []
nicht_da = []

for name, menge in LAGER_DATEN:
    if name not in res_namen:
        nicht_da.append(name)
        continue
    rid = res_namen[name]
    cur.execute(
        """INSERT INTO provinz_lager (provinz_id, ressource_id, menge)
           VALUES (?, ?, ?)
           ON CONFLICT(provinz_id, ressource_id) DO UPDATE SET menge=excluded.menge""",
        (provinz_id, rid, menge)
    )
    print(f"   ✅ {name:12s}: {menge:>5}  (ressource_id={rid})")
    gefunden.append(name)

if nicht_da:
    print(f"\n⚠️  Nicht in 'ressourcen' gefunden: {nicht_da}")
    print("   Vorhandene Namen (Auswahl):")
    for rid, rname, rtyp in sorted(alle_res, key=lambda x: x[1])[:20]:
        print(f"     {rname:30s}  (typ: {rtyp})")
    print("   → Passe LAGER_DATEN im Script an die echten Namen an.")

conn.commit()
conn.close()

print(f"\n✅ Seed abgeschlossen. {len(gefunden)}/{len(LAGER_DATEN)} Ressourcen gesetzt.")
print("   Browser-Cache leeren: Ctrl+Shift+R")
