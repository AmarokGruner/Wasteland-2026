import sqlite3
import json

DB_PATH = "verbrannte_zone.db"

def seed_jagd_loot():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    jagd_loot_data = [
        {
            "terrain": "Wald",
            "resource": "Hirsch",
            "base_amount": 0.3,
            "random_min": 0.2,
            "random_max": 0.8,
            "is_animal": 1,
            "capture_chance": 0.15
        },
        {
            "terrain": "Wald",
            "resource": "Wildschwein",
            "base_amount": 0.4,
            "random_min": 0.3,
            "random_max": 1.0,
            "is_animal": 1,
            "capture_chance": 0.10
        },
        {
            "terrain": "Wald",
            "resource": "Kaninchen",
            "base_amount": 0.5,
            "random_min": 0.3,
            "random_max": 1.2,
            "is_animal": 1,
            "capture_chance": 0.25
        },
        {
            "terrain": "Wald",
            "resource": "Häute",  # Will be mapped to existing Fell resource
            "base_amount": 0.3,
            "random_min": 0.1,
            "random_max": 0.6,
            "is_animal": 0,
            "capture_chance": 0
        },
        {
            "terrain": "Steppe",
            "resource": "Murmeltier",
            "base_amount": 0.3,
            "random_min": 0.2,
            "random_max": 0.7,
            "is_animal": 1,
            "capture_chance": 0.20
        },
        {
            "terrain": "Steppe",
            "resource": "Hasen",
            "base_amount": 0.6,
            "random_min": 0.4,
            "random_max": 1.0,
            "is_animal": 1,
            "capture_chance": 0.30
        },
        {
            "terrain": "Steppe",
            "resource": "Fuchs",
            "base_amount": 0.2,
            "random_min": 0.1,
            "random_max": 0.5,
            "is_animal": 1,
            "capture_chance": 0.10
        },
        {
            "terrain": "Grasland",
            "resource": "Hasen",
            "base_amount": 0.7,
            "random_min": 0.5,
            "random_max": 1.2,
            "is_animal": 1,
            "capture_chance": 0.35
        },
        {
            "terrain": "Grasland",
            "resource": "Feldhase",
            "base_amount": 0.5,
            "random_min": 0.3,
            "random_max": 1.0,
            "is_animal": 1,
            "capture_chance": 0.30
        },
        {
            "terrain": "Sumpf",
            "resource": "Enten",
            "base_amount": 0.8,
            "random_min": 0.5,
            "random_max": 1.5,
            "is_animal": 1,
            "capture_chance": 0.40
        },
        {
            "terrain": "Sumpf",
            "resource": "Schlammschnecken",
            "base_amount": 0.4,
            "random_min": 0.2,
            "random_max": 0.8,
            "is_animal": 0,
            "capture_chance": 0
        },
        {
            "terrain": "Ödland",
            "resource": "Schlangen",
            "base_amount": 0.3,
            "random_min": 0.1,
            "random_max": 0.5,
            "is_animal": 1,
            "capture_chance": 0.15
        },
    ]
    
    # First ensure resources exist or add them
    resource_map = {}
    cursor.execute("SELECT id, name FROM ressourcen")
    for row in cursor.fetchall():
        resource_map[row[1]] = row[0]
    
    # Add missing resources
    for loot in jagd_loot_data:
        res_name = loot["resource"]
        if res_name not in resource_map:
            cursor.execute("""
                INSERT OR IGNORE INTO ressourcen (name, typ)
                VALUES (?, ?)
            """, (res_name, "Nahrung"))
    
    conn.commit()
    
    # Refresh resource map
    cursor.execute("SELECT id, name FROM ressourcen")
    for row in cursor.fetchall():
        resource_map[row[1]] = row[0]
    
    # Insert JagdLoot entries
    for loot in jagd_loot_data:
        res_id = resource_map.get(loot["resource"])
        if not res_id:
            continue
        
        cursor.execute("""
            INSERT OR IGNORE INTO jagd_loot 
            (terrain_id, resource_id, base_amount, random_min, random_max, is_animal, capture_chance)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            loot["terrain"],
            res_id,
            loot["base_amount"],
            loot["random_min"],
            loot["random_max"],
            loot["is_animal"],
            loot["capture_chance"]
        ))
    
    conn.commit()
    print(f"Seeded {len(jagd_loot_data)} jagd loot entries")
    
    conn.close()

if __name__ == "__main__":
    seed_jagd_loot()