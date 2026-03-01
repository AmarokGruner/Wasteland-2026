#!/usr/bin/env python3
"""Import scraped building data into the database."""
import sqlite3, json

DB_PATH = "verbrannte_zone.db"

def parse_int(value, default=0):
    """Safely parse an integer from various input types."""
    if value is None:
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default

def parse_terrain_eff(item):
    """Parse terrain effectiveness from the scraped data."""
    terrain_eff = {}
    for k, v in item.items():
        if isinstance(k, str) and "%" in k:
            pct = k.replace("%", "")
            if pct.isdigit():
                pct = int(pct)
                if isinstance(v, dict) and "text" in v:
                    terrains = [t.strip() for t in v["text"].split(",")]
                    terrain_eff[str(pct)] = terrains
                elif isinstance(v, str):
                    terrains = [t.strip() for t in v.split(",")]
                    terrain_eff[str(pct)] = terrains
    return terrain_eff

def parse_production(item, name):
    """Parse production from scraped data."""
    produktion = []
    
    # Check for direct production values
    for k, v in item.items():
        if k in ["Ziegen", "Milch", "Wasser"] and isinstance(v, (int, str)):
            try:
                menge = parse_int(v)
                if menge > 0 and not any(p.get("ressource") == k for p in produktion):
                    produktion.append({"ressource": k, "menge": menge})
            except:
                pass
    
    return produktion

def parse_consumption(item, name):
    """Parse consumption from scraped data."""
    verbrauch = []
    
    # Ziegenfarm hat Wasser-Verbrauch
    if name == "Ziegenfarm":
        verbrauch = [{"ressource": "Wasser", "menge": 2}]
    
    return verbrauch

def parse_scraped_data():
    with open("data/scraped/gebaeude.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    buildings = []
    
    for key, item in data.items():
        name = item.get("Name", "")
        if not name:
            continue
        
        kategorie = item.get("Kategorie", "")
        bautyp = item.get("Bautyp", "")
        
        ausbaubar = 1 if item.get("Ausbaubar", "NEIN") == "JA" else 0
        unique = 1 if "JA" in item.get("Unique(einmalig)", "NEIN") else 0
        nur_kueste = 1 if item.get("Nur an Küste", "NEIN") == "JA" else 0
        ist_feld = 1 if item.get("ist Feld", "NEIN") == "JA" else 0
        
        tech_level = parse_int(item.get("Benötigtes Techlevel", 0))
        baukosten_mips = parse_int(item.get("Baukosten in Mips", 0))
        
        # Arbeiter
        arbeiter = 0
        
        # Wohnraum
        wohnraum = 0
        
        # Lagerkapazität
        lager = 0
        
        # Terrain-Effektivität
        terrain_eff = parse_terrain_eff(item)
        
        # Produktion
        produktion = parse_production(item, name)
        
        # Verbrauch
        verbrauch = parse_consumption(item, name)
        
        # Baubar-Status bestimmen
        baubar = 0 if "Vorgabe" in bautyp else 1
        
        buildings.append({
            "name": name,
            "kategorie": kategorie,
            "bautyp": bautyp,
            "baubar": baubar,
            "ausbaubar": ausbaubar,
            "unique_gebaeude": unique,
            "nur_kueste": nur_kueste,
            "ist_feld": ist_feld,
            "tech_level": tech_level,
            "baukosten_mips": baukosten_mips,
            "arbeiter": arbeiter,
            "wohnraum": wohnraum,
            "lagerkapazitaet": lager,
            "produktion": produktion,
            "verbrauch": verbrauch,
            "terrain_effektivitaet": terrain_eff
        })
    
    return buildings

def update_database(buildings):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    updated = 0
    for b in buildings:
        prod_json = json.dumps(b["produktion"], ensure_ascii=False)
        verbr_json = json.dumps(b["verbrauch"], ensure_ascii=False)
        terrain_json = json.dumps(b["terrain_effektivitaet"], ensure_ascii=False)
        
        # Check if exists
        cur.execute("SELECT id FROM gebaeude_typen WHERE name = ?", (b["name"],))
        exists = cur.fetchone()
        
        if exists:
            cur.execute("""
                UPDATE gebaeude_typen 
                SET kategorie = ?, bautyp = ?, baubar = ?, ausbaubar = ?,
                    unique_gebaeude = ?, nur_kueste = ?, ist_feld = ?,
                    tech_level = ?, baukosten_mips = ?, arbeiter = ?,
                    wohnraum = ?, lagerkapazitaet = ?, produktion = ?,
                    rohstoffverbrauch = ?, terrain_effektivitaet = ?
                WHERE name = ?
            """, (b["kategorie"], b["bautyp"], b["baubar"], b["ausbaubar"],
                  b["unique_gebaeude"], b["nur_kueste"], b["ist_feld"],
                  b["tech_level"], b["baukosten_mips"], b["arbeiter"],
                  b["wohnraum"], b["lagerkapazitaet"], prod_json,
                  verbr_json, terrain_json, b["name"]))
            action = "updated"
        else:
            cur.execute("""
                INSERT INTO gebaeude_typen 
                (name, kategorie, bautyp, baubar, ausbaubar, unique_gebaeude,
                 nur_kueste, ist_feld, tech_level, baukosten_mips, arbeiter,
                 wohnraum, lagerkapazitaet, produktion, rohstoffverbrauch, terrain_effektivitaet)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (b["name"], b["kategorie"], b["bautyp"], b["baubar"], b["ausbaubar"],
                  b["unique_gebaeude"], b["nur_kueste"], b["ist_feld"],
                  b["tech_level"], b["baukosten_mips"], b["arbeiter"],
                  b["wohnraum"], b["lagerkapazitaet"], prod_json,
                  verbr_json, terrain_json))
            action = "inserted"
        
        updated += 1
        print(f"  [{action}] {b['name']}: {b['kategorie']}, Produktion={len(b['produktion'])}, Verbrauch={len(b['verbrauch'])}, Lager={b['lagerkapazitaet']}")
    
    conn.commit()
    conn.close()
    print(f"\n{updated} buildings processed.")

if __name__ == "__main__":
    print("Parsing scraped building data...")
    buildings = parse_scraped_data()
    print(f"Found {len(buildings)} buildings\n")
    print("Updating database...")
    update_database(buildings)
    print("\nDone!")
