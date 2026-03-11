import sqlite3
import json

DB_PATH = "verbrannte_zone.db"

JSON_FIELDS = {"rohstoffbedarf_bau", "rohstoffgrundbedarf_ausbau", "rohstoffverbrauch",
               "produktion", "terrain_effektivitaet", "vorkommen_effektivitaet",
               "spezial_eigenschaften", "schlachtfeld", "findwahrscheinlichkeit", 
               "gebaeude_effektivitaet", "module", "aufwertungen", "abwertungen",
               "boni", "voraussetzungen", "bonus_malus", "rohstoffbedarf", 
               "auswirkung_einheitenwerte", "transportkapazitaet", "platzbedarf"}
BOOL_FIELDS = {"baubar", "ausbaubar", "unique_gebaeude", "nur_kueste", "ist_feld", "startgebiet"}

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_tables(conn):
    c = conn.cursor()
    # Gebäude-Typen
    c.execute("""CREATE TABLE IF NOT EXISTS gebaeude_typen (
        id INTEGER PRIMARY KEY, name TEXT NOT NULL,
        symbol_emoji TEXT DEFAULT '', symbol_url TEXT DEFAULT '', bild_url TEXT DEFAULT '',
        kategorie TEXT DEFAULT '', bautyp TEXT DEFAULT 'Land',
        baubar INTEGER DEFAULT 1, ausbaubar INTEGER DEFAULT 0,
        unique_gebaeude INTEGER DEFAULT 0, nur_kueste INTEGER DEFAULT 0, ist_feld INTEGER DEFAULT 0,
        tech_level INTEGER DEFAULT 0, baukosten_mips INTEGER DEFAULT 0,
        ausbaukosten_mips INTEGER DEFAULT 0, energiebedarf INTEGER DEFAULT 0,
        arbeiter INTEGER DEFAULT 0, zusatzarbeiter_pro_stufe INTEGER DEFAULT 0,
        wohnraum INTEGER DEFAULT 0, zusatzwohnraum_pro_stufe INTEGER DEFAULT 0,
        lagerkapazitaet INTEGER DEFAULT 0, beschreibung TEXT DEFAULT '',
        rohstoffbedarf_bau TEXT DEFAULT '[]', rohstoffgrundbedarf_ausbau TEXT DEFAULT '[]',
        rohstoffverbrauch TEXT DEFAULT '[]', produktion TEXT DEFAULT '[]',
        terrain_effektivitaet TEXT DEFAULT '{}', vorkommen_effektivitaet TEXT DEFAULT '{}',
        spezial_eigenschaften TEXT DEFAULT '{}', schlachtfeld TEXT DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    
    # Ressourcen
    c.execute("""CREATE TABLE IF NOT EXISTS ressourcen (
        id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, typ TEXT NOT NULL,
        wert INTEGER DEFAULT 0, verbrauch INTEGER DEFAULT 0, platzbedarf INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    
    # Vorkommen
    c.execute("""CREATE TABLE IF NOT EXISTS vorkommen (
        id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE,
        typ TEXT NOT NULL, tech INTEGER DEFAULT 0, suchkosten INTEGER DEFAULT 0,
        beschreibung TEXT DEFAULT '', findwahrscheinlichkeit TEXT DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    
    # Terrain-Typen
    c.execute("""CREATE TABLE IF NOT EXISTS terrain_typen (
        id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE,
        startgebiet INTEGER DEFAULT 0,
        regen_pct INTEGER DEFAULT 0,
        aufwertungen TEXT DEFAULT '[]',
        abwertungen TEXT DEFAULT '[]',
        beschreibung TEXT DEFAULT '',
        bild_url TEXT DEFAULT '',
        gebaeude_effektivitaet TEXT DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    
    # Einheiten-Typen
    c.execute("""CREATE TABLE IF NOT EXISTS einheiten_typen (
        id INTEGER PRIMARY KEY, name TEXT NOT NULL,
        spezies TEXT DEFAULT '', einheitenklasse TEXT DEFAULT '',
        zugehoerig TEXT DEFAULT '', fortbewegung TEXT DEFAULT 'Boden',
        erstellbedingung TEXT DEFAULT 'keine',
        max_reichweite TEXT DEFAULT 'Nahkampf',
        geschwindigkeit REAL DEFAULT 1,
        nahkampf_staerke INTEGER DEFAULT 0,
        nahkampf_panzerung INTEGER DEFAULT 0,
        fernkampf_panzerung INTEGER DEFAULT 0,
        einheitengroesse INTEGER DEFAULT 1,
        transport_land INTEGER DEFAULT 0,
        platzbedarf_see INTEGER DEFAULT 0,
        platzbedarf_untersee INTEGER DEFAULT 0,
        platzbedarf_luft INTEGER DEFAULT 0,
        module TEXT DEFAULT '[]',
        beschreibung TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        
    # Artikel (Neu)
    c.execute("""CREATE TABLE IF NOT EXISTS artikel (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        name TEXT NOT NULL, 
        spezies TEXT DEFAULT 'Menschen',
        einheittext TEXT DEFAULT '',
        modultyp TEXT DEFAULT '',
        zugehoerig TEXT DEFAULT '',
        bautyp TEXT DEFAULT '',
        produktionspunkte INTEGER DEFAULT 0,
        rohstoffbedarf TEXT DEFAULT '[]',
        modulgroesse INTEGER DEFAULT 1,
        auswirkung_einheitenwerte TEXT DEFAULT '{}',
        transportkapazitaet TEXT DEFAULT '{}',
        platzbedarf TEXT DEFAULT '{}',
        beschreibung TEXT, 
        kategorie TEXT, 
        preis_mips INTEGER DEFAULT 0, 
        preis_muenzen INTEGER DEFAULT 0, 
        gewicht INTEGER DEFAULT 0, 
        haltbarkeit INTEGER DEFAULT 0, 
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        
    # Lebewesen (Neu)
    c.execute("""CREATE TABLE IF NOT EXISTS lebewesen (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        name TEXT NOT NULL, 
        typ TEXT, 
        staerke INTEGER DEFAULT 0, 
        gesundheit INTEGER DEFAULT 0, 
        bevoelkerung_kosten INTEGER DEFAULT 0, 
        beschreibung TEXT, 
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        
    # Regierungsformen (Erweitert)
    c.execute("""CREATE TABLE IF NOT EXISTS regierungsformen (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        name TEXT NOT NULL UNIQUE, 
        formtyp TEXT DEFAULT '',
        techlevel INTEGER DEFAULT 0,
        ausbauwert_regierungssitz INTEGER DEFAULT 0,
        kulturverbreitung REAL DEFAULT 1.0,
        grundmoral INTEGER DEFAULT 50,
        forschungsfortschritt REAL DEFAULT 1.0,
        produktivitaet REAL DEFAULT 1.0,
        wachstum REAL DEFAULT 1.0,
        finanzen REAL DEFAULT 1.0,
        sicherheit REAL DEFAULT 1.0,
        moralmalus_armee_aussen INTEGER DEFAULT 10,
        entfernungsmalus REAL DEFAULT 1.0,
        lebensmittelbedarf REAL DEFAULT 1.0,
        verbrauchsgutbedarf REAL DEFAULT 1.0,
        streikbereitschaft REAL DEFAULT 0.0,
        auswanderbereitschaft REAL DEFAULT 0.0,
        milizen REAL DEFAULT 0.0,
        fremdkultur_verlust INTEGER DEFAULT 0,
        aufstand INTEGER DEFAULT 0,
        krieg_moeglich INTEGER DEFAULT 0,
        provinzanzahl_bis_malus INTEGER DEFAULT 0,
        malus_beschreibung TEXT DEFAULT '',
        beschreibung TEXT, 
        boni TEXT DEFAULT '{}',
        voraussetzungen TEXT DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

    # Provinzausbau/Feldtypen
    c.execute("""CREATE TABLE IF NOT EXISTS provinz_feldtypen (
        id TEXT PRIMARY KEY, name TEXT NOT NULL, beschreibung TEXT DEFAULT '',
        groesse_px INTEGER DEFAULT 30, ist_baubar INTEGER DEFAULT 1,
        bautypen TEXT DEFAULT '[]', farbe_leer TEXT DEFAULT '#444',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

    # Weltkarte Zellen
    c.execute("""CREATE TABLE IF NOT EXISTS world_map_cells (
        x INTEGER,
        y INTEGER,
        terrain_id INTEGER,
        owner_id INTEGER,
        is_ruin_province INTEGER DEFAULT 0,
        preset_buildings TEXT DEFAULT '[]',
        has_ocean_border INTEGER DEFAULT 0,
        PRIMARY KEY (x, y),
        FOREIGN KEY (terrain_id) REFERENCES terrain_typen(id),
        FOREIGN KEY (owner_id) REFERENCES players(id)
    )""")

    # Admin Logs
    c.execute("""CREATE TABLE IF NOT EXISTS admin_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER,
        action TEXT NOT NULL,
        target_type TEXT,
        target_id TEXT,
        payload TEXT DEFAULT '{}',
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (admin_id) REFERENCES users(id)
    )""")

    # Migrationen für bestehende Tabellen
    for col, defn in [
        ("vorkommen_effektivitaet", "TEXT DEFAULT '{}'"),
        ("ausbaukosten_mips",       "INTEGER DEFAULT 0"),
        ("rohstoffgrundbedarf_ausbau", "TEXT DEFAULT '[]'"),
        ("zusatzarbeiter_pro_stufe","INTEGER DEFAULT 0"),
        ("zusatzwohnraum_pro_stufe","INTEGER DEFAULT 0"),
    ]:
        try: c.execute(f"ALTER TABLE gebaeude_typen ADD COLUMN {col} {defn}")
        except: pass

    try: c.execute("ALTER TABLE players ADD COLUMN last_reset_at TIMESTAMP")
    except: pass

    try: c.execute("ALTER TABLE world_map_cells ADD COLUMN preset_buildings TEXT DEFAULT '[]'")
    except: pass

    # Migrationen für Regierungsformen
    for col, defn in [
        ("formtyp", "TEXT DEFAULT ''"),
        ("techlevel", "INTEGER DEFAULT 0"),
        ("ausbauwert_regierungssitz", "INTEGER DEFAULT 0"),
        ("kulturverbreitung", "REAL DEFAULT 1.0"),
        ("grundmoral", "INTEGER DEFAULT 50"),
        ("forschungsfortschritt", "REAL DEFAULT 1.0"),
        ("produktivitaet", "REAL DEFAULT 1.0"),
        ("wachstum", "REAL DEFAULT 1.0"),
        ("finanzen", "REAL DEFAULT 1.0"),
        ("sicherheit", "REAL DEFAULT 1.0"),
        ("moralmalus_armee_aussen", "INTEGER DEFAULT 10"),
        ("entfernungsmalus", "REAL DEFAULT 1.0"),
        ("lebensmittelbedarf", "REAL DEFAULT 1.0"),
        ("verbrauchsgutbedarf", "REAL DEFAULT 1.0"),
        ("streikbereitschaft", "REAL DEFAULT 0.0"),
        ("auswanderbereitschaft", "REAL DEFAULT 0.0"),
        ("milizen", "REAL DEFAULT 0.0"),
        ("fremdkultur_verlust", "INTEGER DEFAULT 0"),
        ("aufstand", "INTEGER DEFAULT 0"),
        ("krieg_moeglich", "INTEGER DEFAULT 0"),
        ("provinzanzahl_bis_malus", "INTEGER DEFAULT 0"),
        ("malus_beschreibung", "TEXT DEFAULT ''"),
    ]:
        try: c.execute(f"ALTER TABLE regierungsformen ADD COLUMN {col} {defn}")
        except: pass

    # Migrationen für terrain_typen
    for col, defn in [
        ("color", "TEXT DEFAULT ''"),
        ("icon", "TEXT DEFAULT ''"),
        ("playable", "INTEGER DEFAULT 1"),
    ]:
        try: c.execute(f"ALTER TABLE terrain_typen ADD COLUMN {col} {defn}")
        except: pass
        
    for ft in [
        ("gebaeude",    "Gebäudefeld",    "Landfeld",      30, 1, '["Land"]',         "#5a7a3a"),
        ("stadt",       "Stadtfeld",      "Stadtfeld",     30, 1, '["Stadt"]',         "#6a6a8a"),
        ("stadtausbau", "Stadtausbau",    "Provinzausbau", 30, 1, '["Stadtausbau"]',   "#4a4a7a"),
        ("weg",         "Wegfeld",        "Wegfeld",       10, 1, '["Weg"]',           "#8b7355"),
        ("kreuzung",    "Kreuzungsfeld",  "Kreuzung",      10, 1, '["Wegkreuzung"]',   "#7a6345"),
        ("vorgabe",     "Vorgabefeld",    "Vorgabe",       30, 0, '["Vorgabe"]',       "#3a3a5a"),
    ]:
        c.execute("INSERT OR IGNORE INTO provinz_feldtypen "
                  "(id,name,beschreibung,groesse_px,ist_baubar,bautypen,farbe_leer) VALUES (?,?,?,?,?,?,?)", ft)
    conn.commit()

def save_entity(c, table, data, id_field="id"):
    """Universelle Hilfsfunktion zum Speichern (INSERT/UPDATE)."""
    if id_field in data:
        c.execute(f"SELECT {id_field} FROM {table} WHERE {id_field}=?", (data[id_field],))
        exists = c.fetchone()
    else:
        # Falls keine ID da ist (z.B. bei name als Unique Key)
        # Hier gehen wir davon aus, dass wir eine ID haben
        exists = None

    vals = {k: (json.dumps(v, ensure_ascii=False) if k in JSON_FIELDS and isinstance(v, (dict, list))
               else (int(v) if k in BOOL_FIELDS else v))
           for k, v in data.items()}

    if exists:
        sp = [f"{k}=?" for k in vals if k != id_field]
        c.execute(f"UPDATE {table} SET {','.join(sp)}, updated_at=CURRENT_TIMESTAMP WHERE {id_field}=?",
                  [vals[k] for k in vals if k != id_field] + [data[id_field]])
        return False # Updated
    else:
        cols = list(vals.keys())
        c.execute(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})",
                  [vals[k] for k in cols])
        return True # Inserted
