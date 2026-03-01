#!/usr/bin/env python3
"""seed_building_production.py
Ergänzt Produktion und Verbrauch für Gebäude-Typen.
WICHTIG: Werte sind pro Tag (24 Stunden), werden durch 24 geteilt für stündliche Berechnung.
"""
import sqlite3, json
DB_PATH = "verbrannte_zone.db"

# Werte pro Tag (werden durch 24 geteilt für stündliche Produktion)
HOURS_PER_DAY = 24

BUILDING_PRODUCTION = {
    "Bunker": {
        "produktion": [{"ressource": "Wasser", "menge": 50}],
        "verbrauch": [],
        "lagerkapazitaet": 20000,
        "arbeiter": 10,
        "wohnraum": 100,
        "terrain_effektivitaet": {"100": ["Grasland", "Wald", "Steppe", "Savanne", "Sumpfland"]}
    },
    "Kartoffelfarm": {
        "produktion": [{"ressource": "Kartoffeln", "menge": 40}],
        "verbrauch": [],
        "lagerkapazitaet": 0,
        "arbeiter": 10,
        "wohnraum": 0,
        "terrain_effektivitaet": {"100": ["Grasland", "Steppe"], "125": ["Grünland", "Weideland"]}
    },
    "Erdnussfarm": {
        "produktion": [{"ressource": "Erdnüsse", "menge": 30}],
        "verbrauch": [],
        "lagerkapazitaet": 0,
        "arbeiter": 4,
        "wohnraum": 0,
        "terrain_effektivitaet": {"100": ["Pampa", "Savanne"]}
    },
    "Sojafarm": {
        "produktion": [{"ressource": "Sojabohnen", "menge": 25}],
        "verbrauch": [],
        "lagerkapazitaet": 0,
        "arbeiter": 10,
        "wohnraum": 0,
        "terrain_effektivitaet": {"100": ["Sumpfland", "Tropensumpf"]}
    },
    "Imkerei": {
        "produktion": [{"ressource": "Honig", "menge": 8}, {"ressource": "Wachs", "menge": 2}],
        "verbrauch": [],
        "lagerkapazitaet": 0,
        "arbeiter": 2,
        "wohnraum": 0,
        "terrain_effektivitaet": {"100": ["Grasland", "Wald", "Grünland", "Weideland"]}
    },
    "Dattelnplantage": {
        "produktion": [{"ressource": "Datteln", "menge": 16}],
        "verbrauch": [],
        "lagerkapazitaet": 0,
        "arbeiter": 4,
        "wohnraum": 0,
        "terrain_effektivitaet": {"100": ["Wüste", "Sanddünen", "Pampa"]}
    },
    "Orangenplantage": {
        "produktion": [{"ressource": "Orangen", "menge": 40}],
        "verbrauch": [],
        "lagerkapazitaet": 0,
        "arbeiter": 10,
        "wohnraum": 0,
        "terrain_effektivitaet": {"100": ["Grünland", "Regenwald", "Weideland"]}
    },
    "Apfelplantage": {
        "produktion": [{"ressource": "Äpfel", "menge": 24}],
        "verbrauch": [],
        "lagerkapazitaet": 0,
        "arbeiter": 6,
        "wohnraum": 0,
        "terrain_effektivitaet": {"100": ["Grasland", "Wald", "Grünland"]}
    },
    "Palmenplantage": {
        "produktion": [{"ressource": "Kokosnuss", "menge": 32}],
        "verbrauch": [],
        "lagerkapazitaet": 0,
        "arbeiter": 15,
        "wohnraum": 0,
        "terrain_effektivitaet": {"100": ["Dschungel", "Regenwald", "Tropensumpf"]}
    },
    "Holzfäller": {
        "produktion": [{"ressource": "Bauholz", "menge": 12}],
        "verbrauch": [],
        "lagerkapazitaet": 0,
        "arbeiter": 6,
        "wohnraum": 0,
        "terrain_effektivitaet": {"100": ["Wald", "Sumpfland", "Regenwald"]}
    },
    "Steinmetz": {
        "produktion": [{"ressource": "Stein", "menge": 5}, {"ressource": "Kies", "menge": 2}],
        "verbrauch": [],
        "lagerkapazitaet": 0,
        "arbeiter": 8,
        "wohnraum": 0,
        "terrain_effektivitaet": {"100": ["Felsgebirge", "Grasfelsland", "Grasgebirge", "Brachfelsland"]}
    },
    "Lehmgrube": {
        "produktion": [{"ressource": "Lehm", "menge": 15}],
        "verbrauch": [],
        "lagerkapazitaet": 0,
        "arbeiter": 4,
        "wohnraum": 0,
        "terrain_effektivitaet": {"100": ["Grasland", "Ufer", "Sumpfland"]}
    },
    "Ziegelofen": {
        "produktion": [{"ressource": "Ziegel", "menge": 8}],
        "verbrauch": [{"ressource": "Lehm", "menge": 4}, {"ressource": "Brennholz", "menge": 2}],
        "lagerkapazitaet": 0,
        "arbeiter": 3,
        "wohnraum": 0,
        "terrain_effektivitaet": {"100": ["Grasland", "Steppe", "Ufer"]}
    },
    "Sägegrube": {
        "produktion": [{"ressource": "Bretter", "menge": 6}],
        "verbrauch": [{"ressource": "Bauholz", "menge": 4}],
        "lagerkapazitaet": 0,
        "arbeiter": 4,
        "wohnraum": 0,
        "terrain_effektivitaet": {"100": ["Wald", "Wald"]}
    },
    "Kohlebergwerk": {
        "produktion": [{"ressource": "Steinkohle", "menge": 4}],
        "verbrauch": [{"ressource": "Werkzeug", "menge": 1}],
        "lagerkapazitaet": 0,
        "arbeiter": 15,
        "wohnraum": 0,
        "terrain_effektivitaet": {"100": ["Felsgebirge", "Grasgebirge", "Ödgebirge"]}
    },
    "Eisenhütte": {
        "produktion": [{"ressource": "Eisen", "menge": 3}],
        "verbrauch": [{"ressource": "Eisenerz", "menge": 6}, {"ressource": "Steinkohle", "menge": 3}],
        "lagerkapazitaet": 0,
        "arbeiter": 12,
        "wohnraum": 0,
        "terrain_effektivitaet": {"100": ["Felsgebirge", "Grasgebirge"]}
    },
    "Steinbruch": {
        "produktion": [{"ressource": "Stein", "menge": 10}, {"ressource": "Kies", "menge": 5}],
        "verbrauch": [],
        "lagerkapazitaet": 0,
        "arbeiter": 10,
        "wohnraum": 0,
        "terrain_effektivitaet": {"100": ["Felsgebirge", "Grasfelsland", "Gebirge"]}
    },
    "Kraftwerk": {
        "produktion": [{"ressource": "Energie", "menge": 50}],
        "verbrauch": [{"ressource": "Steinkohle", "menge": 5}],
        "lagerkapazitaet": 0,
        "arbeiter": 5,
        "wohnraum": 0,
        "terrain_effektivitaet": {"100": ["Felsgebirge", "Ödgebirge"]}
    },
    "Tankstelle": {
        "produktion": [{"ressource": "Benzin", "menge": 20}],
        "verbrauch": [{"ressource": "Erdöl", "menge": 25}],
        "lagerkapazitaet": 0,
        "arbeiter": 3,
        "wohnraum": 0,
        "terrain_effektivitaet": {"100": ["Ödland", "Wüste"]}
    },
    "Raffinerie": {
        "produktion": [{"ressource": "Treibstoff", "menge": 15}],
        "verbrauch": [{"ressource": "Erdöl", "menge": 20}],
        "lagerkapazitaet": 0,
        "arbeiter": 8,
        "wohnraum": 0,
        "terrain_effektivitaet": {"100": ["Ödland", "Wüste"]}
    },
    "Lagerhütte": {
        "produktion": [],
        "verbrauch": [],
        "lagerkapazitaet": 1000,
        "arbeiter": 0,
        "wohnraum": 0,
        "terrain_effektivitaet": {}
    },
    "Wohnhaus": {
        "produktion": [],
        "verbrauch": [],
        "lagerkapazitaet": 0,
        "arbeiter": 0,
        "wohnraum": 50,
        "terrain_effektivitaet": {}
    },
    "Bauernhof": {
        "produktion": [{"ressource": "Getreide", "menge": 20}, {"ressource": "Stroh", "menge": 5}],
        "verbrauch": [],
        "lagerkapazitaet": 0,
        "arbeiter": 8,
        "wohnraum": 0,
        "terrain_effektivitaet": {"100": ["Grasland", "Steppe", "Grünland"]}
    },
    "Ziegenfarm": {
        "produktion": [{"ressource": "Ziegen", "menge": 1}, {"ressource": "Milch", "menge": 10}],
        "verbrauch": [{"ressource": "Getreide", "menge": 2}],
        "lagerkapazitaet": 0,
        "arbeiter": 4,
        "wohnraum": 0,
        "terrain_effektivitaet": {"100": ["Savanne", "Steppe", "Ödland"]}
    },
    "Tabakplantage": {
        "produktion": [{"ressource": "Tabak", "menge": 6}],
        "verbrauch": [],
        "lagerkapazitaet": 0,
        "arbeiter": 15,
        "wohnraum": 0,
        "terrain_effektivitaet": {"100": ["Grünland", "Grünhügel", "Weideland"]}
    },
    "Hanfplantage": {
        "produktion": [{"ressource": "Hanf", "menge": 8}],
        "verbrauch": [],
        "lagerkapazitaet": 0,
        "arbeiter": 15,
        "wohnraum": 0,
        "terrain_effektivitaet": {"100": ["Sumpfland", "Tropensumpf"]}
    },
    "Kräutergarten": {
        "produktion": [{"ressource": "Kräuter", "menge": 12}],
        "verbrauch": [],
        "lagerkapazitaet": 0,
        "arbeiter": 5,
        "wohnraum": 0,
        "terrain_effektivitaet": {"100": ["Grünland", "Wald", "Sumpfland"]}
    },
    "Fischerei": {
        "produktion": [{"ressource": "Fisch", "menge": 15}],
        "verbrauch": [],
        "lagerkapazitaet": 0,
        "arbeiter": 6,
        "wohnraum": 0,
        "terrain_effektivitaet": {"100": ["Küste", "Meer"]}
    },
    "Jagdhütte": {
        "produktion": [{"ressource": "Fleisch", "menge": 8}, {"ressource": "Fell", "menge": 2}],
        "verbrauch": [],
        "lagerkapazitaet": 0,
        "arbeiter": 3,
        "wohnraum": 0,
        "terrain_effektivitaet": {"100": ["Wald", "Sumpfland"]}
    },
    "Wassermühle": {
        "produktion": [{"ressource": "Mehl", "menge": 10}],
        "verbrauch": [{"ressource": "Getreide", "menge": 15}],
        "lagerkapazitaet": 0,
        "arbeiter": 4,
        "wohnraum": 0,
        "terrain_effektivitaet": {"100": ["Fluss", "Ufer"]}
    },
    "Weberei": {
        "produktion": [{"ressource": "Stoff", "menge": 5}],
        "verbrauch": [{"ressource": "Wolle", "menge": 8}, {"ressource": "Hanf", "menge": 4}],
        "lagerkapazitaet": 0,
        "arbeiter": 6,
        "wohnraum": 0,
        "terrain_effektivitaet": {"100": ["Grasland", "Weideland"]}
    },
    "Gerberei": {
        "produktion": [{"ressource": "Leder", "menge": 4}],
        "verbrauch": [{"ressource": "Häute", "menge": 6}],
        "lagerkapazitaet": 0,
        "arbeiter": 3,
        "wohnraum": 0,
        "terrain_effektivitaet": {"100": ["Grasland", "Steppe"]}
    },
    "Schmiede": {
        "produktion": [{"ressource": "Werkzeug", "menge": 2}, {"ressource": "Waffen", "menge": 1}],
        "verbrauch": [{"ressource": "Eisen", "menge": 5}, {"ressource": "Kohle", "menge": 3}],
        "lagerkapazitaet": 0,
        "arbeiter": 5,
        "wohnraum": 0,
        "terrain_effektivitaet": {"100": ["Grasland", "Dorf"]}
    },
}

def update_buildings():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    updated = 0
    for name, data in BUILDING_PRODUCTION.items():
        # Werte sind pro Tag - direkt speichern
        prod_json = json.dumps(data["produktion"], ensure_ascii=False)
        verbr_json = json.dumps(data["verbrauch"], ensure_ascii=False)
        terrain_json = json.dumps(data["terrain_effektivitaet"], ensure_ascii=False)
        
        cur.execute("""
            UPDATE gebaeude_typen 
            SET produktion = ?, rohstoffverbrauch = ?, lagerkapazitaet = ?,
                arbeiter = ?, wohnraum = ?, terrain_effektivitaet = ?
            WHERE name = ?
        """, (prod_json, verbr_json, data["lagerkapazitaet"], 
              data["arbeiter"], data["wohnraum"], terrain_json, name))
        
        if cur.rowcount > 0:
            updated += 1
            total_prod = sum(p["menge"] for p in data["produktion"])
            total_verbr = sum(v["menge"] for v in data["verbrauch"])
            print(f"  [OK] {name}: Produktion={total_prod}/Tag, Verbrauch={total_verbr}/Tag, Lager={data['lagerkapazitaet']}")
    
    conn.commit()
    conn.close()
    print(f"\n{updated} Gebaeude-Typen aktualisiert (Werte pro Tag).")

if __name__ == "__main__":
    print("Aktualisiere Gebaeude-Produktionsdaten...")
    update_buildings()
