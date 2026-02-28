#!/usr/bin/env python3
"""seed_patch_bunker_v1.py – Bunker (ID=1) vollständige Daten
Idempotent – kann beliebig oft ausgeführt werden.
Voraussetzung: seed_buildings.py oder main.py muss mindestens einmal gelaufen sein.
"""
import sqlite3, json, sys

DB_PATH = "verbrannte_zone.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur  = conn.cursor()

# ── Voraussetzungs-Check ─────────────────────────────
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
vorhandene = {r["name"] for r in cur.fetchall()}
if "gebaeude_typen" not in vorhandene:
    print("\n❌ Tabelle gebaeude_typen fehlt!")
    print("   Bitte zuerst ausführen: python seed_buildings.py")
    print("   oder: python main.py  (einmal starten → Ctrl+C)")
    conn.close(); sys.exit(1)

ALLE_TERRAINS = ['Brachfelsland', 'Brachgebirge', 'Brachhügel', 'Brachland', 'Dschungel', 'Eiswüste', 'Felsgebirge', 'Grasfelsland', 'Grasgebirge', 'Grashügel', 'Grasland', 'Grünfelsland', 'Grüngebirge', 'Grünhügel', 'Grünland', 'Hochnebelwald', 'Pampa', 'Pampafelsland', 'Pampagebirge', 'Plateau', 'Regenwald', 'Sanddünen', 'Savanne', 'Savannenfelsland', 'Savannengebirge', 'Savannenhügel', 'Steppe', 'Steppfelsland', 'Steppgebirge', 'Stepphügel', 'Sumpfland', 'Tropensumpf', 'Wald', 'Weidefelsland', 'Weideland', 'Wüste', 'Ödfelsland', 'Ödgebirge', 'Ödhügel', 'Ödland']

# ════════════ BUNKER (ID=1) ════════════
B_TERRAIN  = json.dumps({"100": ALLE_TERRAINS})
B_ROHBAU   = json.dumps([{"name": "Stein",  "menge": 200}])
B_PROD     = json.dumps([{"name": "Wasser", "menge": 50}])
B_SPEZ     = json.dumps({"bunkerbonus": 250, "techproduktion": 2, "kulturpunkte": 4})
B_SCHLACHT = json.dumps({"Bunker": 1})
B_BESCHR   = (
    "Der Bunker ist dein erstes Gebäude in VZ. In diesem versuchst du die neue Welt zu besiedeln. "
    "Er bietet dir 20000 Lagerraum, einen Bonus auf feindliche Übergriffe und den ersten Wohnraum. "
    "Außerdem sind in ihm 2 Labore integriert. "
    "Du solltest dir also genau überlegen ob du ihn abreißen willst \u2013 "
    "denn es ist der einzige, den du je bekommst."
)

SQL_BUNKER = """
    INSERT INTO gebaeude_typen
        (id, name, kategorie, bautyp, baubar, ausbaubar, unique_gebaeude,
         nur_kueste, ist_feld, tech_level, baukosten_mips, energiebedarf,
         arbeiter, wohnraum, lagerkapazitaet, beschreibung,
         rohstoffbedarf_bau, produktion, terrain_effektivitaet,
         spezial_eigenschaften, schlachtfeld)
    VALUES (1,'Bunker','Start','Vorgabe',0,0,1,0,0,0,0,0,
            10,100,20000,?,?,?,?,?,?)
    ON CONFLICT(id) DO UPDATE SET
        name                  = 'Bunker',
        kategorie             = 'Start',
        bautyp                = 'Vorgabe',
        baubar                = 0,
        ausbaubar             = 0,
        unique_gebaeude       = 1,
        nur_kueste            = 0,
        ist_feld              = 0,
        tech_level            = 0,
        baukosten_mips        = 0,
        energiebedarf         = 0,
        arbeiter              = 10,
        wohnraum              = 100,
        lagerkapazitaet       = 20000,
        beschreibung          = excluded.beschreibung,
        rohstoffbedarf_bau    = excluded.rohstoffbedarf_bau,
        produktion            = excluded.produktion,
        terrain_effektivitaet = excluded.terrain_effektivitaet,
        spezial_eigenschaften = excluded.spezial_eigenschaften,
        schlachtfeld          = excluded.schlachtfeld,
        updated_at            = CURRENT_TIMESTAMP
"""
cur.execute(SQL_BUNKER,
    (B_BESCHR, B_ROHBAU, B_PROD, B_TERRAIN, B_SPEZ, B_SCHLACHT))
conn.commit()

# ── Verifizierung ──────────────────────────────────────
cur.execute("""
    SELECT id, name, kategorie, bautyp, baubar, unique_gebaeude,
           arbeiter, wohnraum, lagerkapazitaet,
           rohstoffbedarf_bau, produktion,
           spezial_eigenschaften, schlachtfeld
    FROM gebaeude_typen WHERE id=1""" )
row = cur.fetchone()
if row:
    print("\n✅ Bunker (ID=1) erfolgreich gesetzt:")
    print(f"   name            : {row['name']}")
    print(f"   kategorie       : {row['kategorie']}")
    print(f"   bautyp          : {row['bautyp']}")
    print(f"   baubar          : {row['baubar']}  |  unique: {row['unique_gebaeude']}")
    print(f"   arbeiter        : {row['arbeiter']}  |  wohnraum: {row['wohnraum']}")
    print(f"   lagerkapazitaet : {row['lagerkapazitaet']}")
    rb = json.loads(row["rohstoffbedarf_bau"] or "[]")
    pr = json.loads(row["produktion"]         or "[]")
    sp = json.loads(row["spezial_eigenschaften"] or "{}")
    sf = json.loads(row["schlachtfeld"]          or "{}")
    print(f"   rohstoffbedarf  : {rb}")
    print(f"   produktion      : {pr}")
    print(f"   spezial         : {sp}")
    print(f"   schlachtfeld    : {sf}")
else:
    print("\n❌ Bunker nicht in DB – prüfe seed_buildings.py")

conn.close()
print("\n✅ seed_patch_bunker_v1.py abgeschlossen")