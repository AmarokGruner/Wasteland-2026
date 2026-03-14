import sqlite3

DB_PATH = "verbrannte_zone.db"

def seed_animal_templates():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Example animal templates (based on existing resources)
    templates = [
        {
            "resource_name": "Huhn",
            "feed_resource_name": "Getreide",
            "feed_amount_per_24h": 1.0,
            "breed_output_resource_name": "Eier",
            "breed_rate": 0.2,
            "is_pflanzenfresser": 1
        },
        {
            "resource_name": "Nuggrets",
            "feed_resource_name": "Getreide",
            "feed_amount_per_24h": 1.5,
            "breed_output_resource_name": "Fleisch",
            "breed_rate": 0.15,
            "is_pflanzenfresser": 1
        },
        {
            "resource_name": "Pferde",
            "feed_resource_name": "Gras",
            "feed_amount_per_24h": 2.0,
            "breed_output_resource_name": None,
            "breed_rate": 0.05,
            "is_pflanzenfresser": 1
        },
        {
            "resource_name": "Schafe",
            "feed_resource_name": "Gras",
            "feed_amount_per_24h": 1.2,
            "breed_output_resource_name": "Wolle",
            "breed_rate": 0.1,
            "is_pflanzenfresser": 1
        },
    ]
    
    # Get resource IDs
    cursor.execute("SELECT id, name FROM ressourcen")
    resources = {name: rid for rid, name in cursor.fetchall()}
    
    for tpl in templates:
        res_id = resources.get(tpl["resource_name"])
        feed_id = resources.get(tpl["feed_resource_name"])
        out_id = resources.get(tpl["breed_output_resource_name"]) if tpl["breed_output_resource_name"] else None
        if not res_id or not feed_id:
            continue
        
        cursor.execute("""
            INSERT OR IGNORE INTO tier_vorlagen (resource_id, feed_resource_id, feed_amount_per_24h, breed_output_resource_id, breed_rate, is_pflanzenfresser)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            res_id,
            feed_id,
            tpl["feed_amount_per_24h"],
            out_id,
            tpl["breed_rate"],
            tpl["is_pflanzenfresser"]
        ))
    
    conn.commit()
    print("Seeded animal templates")
    conn.close()

if __name__ == "__main__":
    seed_animal_templates()