#!/usr/bin/env python3
"""Robust parsing of scraped building data."""
import sqlite3, json, re

DB_PATH = "verbrannte_zone.db"

def parse_production_consumption(item, keys):
    """Parse production and consumption from scraped data."""
    produktion = []
    verbrauch = []
    
    # Find production
    prod_obj = item.get("Rohstoffproduktion im Betrieb")
    if prod_obj and isinstance(prod_obj, dict):
        prod_name = prod_obj.get("text", "")
        if prod_name:
            try:
                prod_idx = keys.index("Rohstoffproduktion im Betrieb")
                for j in range(prod_idx + 1, len(keys)):
                    k = keys[j]
                    if k.isdigit():
                        # Check if value contains "Beschreibung" or "Gebäudespezifische"
                        next_val = item.get(k, "")
                        if isinstance(next_val, str) and ("Beschreibung" in next_val or "Gebäudespezifische" in next_val):
                            produktion.append({"ressource": prod_name, "menge": int(k)})
                            break
                    elif isinstance(k, str) and ("Beschreibung" in k or "Gebäudespezifische" in k):
                        # Look back for the quantity
                        for jj in range(j - 1, prod_idx, -1):
                            kk = keys[jj]
                            if kk.isdigit():
                                val_before = item.get(kk, "")
                                if isinstance(val_before, str):
                                    try:
                                        qty = int(kk)
                                        if qty > 0:
                                            produktion.append({"ressource": prod_name, "menge": qty})
                                            break
                                    except:
                                        pass
                        break
            except (ValueError, IndexError):
                pass
    
    # Also try alternative: just get the first number after "Rohstoffproduktion"
    if not produktion:
        try:
            prod_idx = keys.index("Rohstoffproduktion im Betrieb")
            for j in range(prod_idx + 1, len(keys)):
                k = keys[j]
                if k.isdigit() and int(k) > 0:
                    prod_name = prod_obj.get("text", "")
                    if prod_name:
                        produktion.append({"ressource": prod_name, "menge": int(k)})
                        break
        except:
            pass
    
    # Find consumption
    cons_obj = item.get("Rohstoffverbrauch im Betrieb")
    if cons_obj and isinstance(cons_obj, dict):
        cons_name = cons_obj.get("text", "")
        if cons_name:
            try:
                cons_idx = keys.index("Rohstoffverbrauch im Betrieb")
                for j in range(cons_idx + 1, len(keys)):
                    k = keys[j]
                    if k.isdigit():
                        verbrauch.append({"ressource": cons_name, "menge": int(k)})
                        break
            except (ValueError, IndexError):
                pass
    
    # Check for direct key-value pairs (like Ziegen: "1", Milch: "10")
    # Only for specific resources that we know are stored this way
    for res_name in ["Ziegen", "Milch"]:
        if res_name in item:
            menge = parse_int(item[res_name])
            if menge > 0:
                if not any(p.get("ressource") == res_name for p in produktion):
                    produktion.append({"ressource": res_name, "menge": menge})
    
    return produktion, verbrauch


def parse_scraped_data():
    with open("data/scraped/gebaeude.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    buildings = []
    
    for key, item in data.items():
        name = item.get("Name", "")
        if not name:
            continue
        
        # Basic fields
        kategorie = item.get("Kategorie", "")
        bautyp = item.get("Bautyp", "")
        ausbaubar = 1 if item.get("Ausbaubar", "NEIN") == "JA" else 0
        unique = 1 if "JA" in item.get("Unique(einmalig)", "NEIN") else 0
        nur_kueste = 1 if item.get("Nur an Küste", "NEIN") == "JA" else 0
        ist_feld = 1 if item.get("ist Feld", "NEIN") == "JA" else 0
        tech_level = parse_int(item.get("Benötigtes Techlevel", 0))
        baukosten_mips = parse_int(item.get("Baukosten in Mips", 0))
        
        # Get all keys in order
        keys = list(item.keys())
        
        # Parse numeric fields (Arbeiter, Wohnraum, Lager)
        arbeiter = 0
        wohnraum = 0
        lager = 0
        
        for i, k in enumerate(keys):
            if k.isdigit():
                value = item.get(k)
                if isinstance(value, str):
                    if "Arbeiter" in value:
                        arbeiter = int(k)
                    elif "Wohnraum" in value:
                        wohnraum = int(k)
                    elif "Lager" in value:
                        lager = int(k)
                elif isinstance(value, list):
                    if "Arbeiter" in value:
                        arbeiter = int(k)
                    if "Lager" in value:
                        lager = int(k)
        
        # Apply manual corrections for known incorrect mappings
        # These are based on the actual game data
        corrections = {
            "Bunker": (10, 100),
            "Kartoffelfarm": (0, 10),
            "Sojafarm": (10, 0),
            "Imkerei": (2, 0),
            "Dattelnplantage": (4, 0),
            "Orangenplantage": (10, 0),
            "Apfelplantage": (6, 0),
            "Palmenplantage": (15, 0),
            "Holzfäller": (6, 0),
            "Steinmetz": (8, 0),
            "Tabakplantage": (15, 0),
            "Hanfplantage": (15, 0),
            "Kräutergarten": (5, 0),
            "Ziegenfarm": (4, 0),
            "Wollspinnenzucht": (4, 0),
            "kleine Getreidefarm": (1, 0),
            "Karrenbauer": (8, 0),
            "Feuerstelle": (0, 3),
            "Marktplatz": (0, 15),
            "Schlachthaus": (2, 0),
            "Kiesgrube": (12, 0),
            "Werkzeugmacher": (2, 0),
            "Münzerei": (2, 0),
            "Edelholzfäller": (6, 0),
            "Auffangbecken": (1, 0),
            "Tongrube": (8, 0),
            "Lehmgrube": (8, 0),
            "Töpferei": (0, 0),
            "Lehmziegelei": (0, 0),
            "Nuggretzucht": (3, 0),
            "Lehmhütte": (0, 0),
            "Lagerhütte": (0, 0),
            "Hühnerfarm": (3, 0),
            "Fischerhütte": (2, 0),
            "Kautschukplantage": (4, 0),
            "Jägerhütte": (4, 0),
            "Schilfbauer": (1, 0),
            "Teehain": (3, 0),
            "Perlentaucher": (3, 0),
            "Sägegrube": (3, 0),
            "Tropenholzfäller": (8, 0),
            "Weingarten": (1, 0),
            "Reisfarm": (2, 0),
        }
        
        if name in corrections:
            arbeiter, wohnraum = corrections[name]
        
        # Special case for Bunker: Lager = 20000
        if name == "Bunker":
            lager = 20000
        
        # Parse terrain effectiveness
        terrain_eff = {}
        for k, v in item.items():
            if isinstance(k, str) and "%" in k:
                pct = k.replace("%", "")
                if pct.isdigit():
                    terrains = []
                    if isinstance(v, dict) and "text" in v:
                        terrains = [t.strip() for t in v["text"].split(",")]
                    elif isinstance(v, str):
                        terrains = [t.strip() for t in v.split(",")]
                    terrain_eff[pct] = terrains
        
        # Parse production and consumption
        produktion, verbrauch = parse_production_consumption(item, keys)
        
        # Special cases
        if name == "Bunker":
            lager = 20000
            # Make sure we have correct water production
            if not any(p.get("ressource") == "Wasser" for p in produktion):
                produktion = [{"ressource": "Wasser", "menge": 50}]
        elif name == "Ziegenfarm":
            verbrauch = [{"ressource": "Wasser", "menge": 2}]
        
        # Baubar
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
                    wohnraum = ?, lagerkapazitaet = ?,
                    produktion = ?, rohstoffverbrauch = ?, terrain_effektivitaet = ?
                WHERE name = ?
            """, (b["kategorie"], b["bautyp"], b["baubar"], b["ausbaubar"],
                  b["unique_gebaeude"], b["nur_kueste"], b["ist_feld"],
                  b["tech_level"], b["baukosten_mips"], b["arbeiter"],
                  b["wohnraum"], b["lagerkapazitaet"],
                  prod_json, verbr_json, terrain_json, b["name"]))
            action = "updated"
        else:
            cur.execute("""
                INSERT INTO gebaeude_typen 
                (name, kategorie, bautyp, baubar, ausbaubar, unique_gebaeude,
                 nur_kueste, ist_feld, tech_level, baukosten_mips, arbeiter,
                 wohnraum, lagerkapazitaet, produktion, 
                 rohstoffverbrauch, terrain_effektivitaet)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (b["name"], b["kategorie"], b["bautyp"], b["baubar"], b["ausbaubar"],
                  b["unique_gebaeude"], b["nur_kueste"], b["ist_feld"],
                  b["tech_level"], b["baukosten_mips"], b["arbeiter"],
                  b["wohnraum"], b["lagerkapazitaet"],
                  prod_json, verbr_json, terrain_json))
            action = "inserted"
        
        updated += 1
        prod_str = ", ".join([f"{p['ressource']}:{p['menge']}" for p in b["produktion"]])
        verbr_str = ", ".join([f"{v['ressource']}:{v['menge']}" for v in b["verbrauch"]])
        print(f"  [{action}] {b['name']}:")
        print(f"       Prod: [{prod_str}], Verbr: [{verbr_str}], Lager:{b['lagerkapazitaet']}, Arbt:{b['arbeiter']}, Whnrm:{b['wohnraum']}")
    
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
