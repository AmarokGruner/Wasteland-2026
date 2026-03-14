import sqlite3
import json

DB_PATH = "verbrannte_zone.db"

def seed_vorkommen():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    vorkommen_data = [
        {
            "name": "Ton",
            "typ": "geologisch",
            "tech_level": 0,
            "suchkosten_mips": 80,
            "findwahrscheinlichkeit": {
                "Sumpf": 60,
                "Wald": 30,
                "Ödland": 20
            }
        },
        {
            "name": "Lehm",
            "typ": "geologisch", 
            "tech_level": 0,
            "suchkosten_mips": 60,
            "findwahrscheinlichkeit": {
                "Steppe": 50,
                "Ödland": 40,
                "Grasland": 20
            }
        },
        {
            "name": "Kohle",
            "typ": "geologisch",
            "tech_level": 2,
            "suchkosten_mips": 200,
            "findwahrscheinlichkeit": {
                "Wald": 35,
                "Grasland": 25,
                "Steppe": 20
            }
        },
        {
            "name": "Eisenerz",
            "typ": "geologisch",
            "tech_level": 1,
            "suchkosten_mips": 150,
            "findwahrscheinlichkeit": {
                "Ödland": 40,
                "Steppe": 25,
                "Wald": 15
            }
        },
        {
            "name": "Kupfererz",
            "typ": "geologisch",
            "tech_level": 2,
            "suchkosten_mips": 180,
            "findwahrscheinlichkeit": {
                "Steppe": 30,
                "Ödland": 25
            }
        },
        {
            "name": "Gold",
            "typ": "geologisch",
            "tech_level": 3,
            "suchkosten_mips": 500,
            "findwahrscheinlichkeit": {
                "Wüste": 20,
                "Ödland": 10
            }
        },
        {
            "name": "Wasser",
            "typ": "Oberfläche",
            "tech_level": 0,
            "suchkosten_mips": 50,
            "findwahrscheinlichkeit": {
                "Sumpf": 80,
                "Wald": 50,
                "Grasland": 40,
                "Steppe": 30,
                "Ödland": 20
            }
        },
        {
            "name": "Öl",
            "typ": "unt.Seen",
            "tech_level": 4,
            "suchkosten_mips": 800,
            "findwahrscheinlichkeit": {
                "Wüste": 25,
                "Ödland": 15
            }
        },
        {
            "name": "Uran",
            "typ": "unt.Seen",
            "tech_level": 5,
            "suchkosten_mips": 1200,
            "findwahrscheinlichkeit": {
                "Wald": 10,
                "Steppe": 5
            }
        },
    ]
    
    for v in vorkommen_data:
        prob_json = json.dumps(v["findwahrscheinlichkeit"])
        
        cursor.execute("""
            INSERT OR IGNORE INTO vorkommen (name, typ, tech, suchkosten, findwahrscheinlichkeit)
            VALUES (?, ?, ?, ?, ?)
        """, (v["name"], v["typ"], v["tech_level"], v["suchkosten_mips"], prob_json))
    
    conn.commit()
    print(f"Seeded {len(vorkommen_data)} vorkommen types")
    
    conn.close()

if __name__ == "__main__":
    seed_vorkommen()