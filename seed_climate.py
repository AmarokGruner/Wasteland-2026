import sqlite3

DB_PATH = "verbrannte_zone.db"

def seed_terrain_configs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    terrains = [
        ("Wüste", 0.05, 2, 5.0),
        ("Ödland", 0.15, 5, 15.0),
        ("Steppe", 0.25, 8, 35.0),
        ("Grasland", 0.35, 10, 50.0),
        ("Wald", 0.45, 12, 65.0),
        ("Sumpf", 0.60, 15, 85.0),
    ]
    
    cursor.executemany("""
        INSERT OR IGNORE INTO terrain_configs (name, rain_probability, rain_amount, average_moisture)
        VALUES (?, ?, ?, ?)
    """, terrains)
    
    conn.commit()
    print(f"Seeded {len(terrains)} terrain configs")
    conn.close()

def seed_resource_deposits():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    from app.models import SessionLocal, Resource
    db = SessionLocal()
    
    resources = db.query(Resource).all()
    resource_map = {r.name: r.id for r in resources}
    
    db.close()
    
    deposits = [
        ("Ton", "Sumpf", 0, 100),
        ("Lehm", "Steppe", 0, 80),
        ("Kohle", "Wald", 2, 200),
        ("Eisenerz", "Ödland", 1, 150),
        ("Kupfererz", "Steppe", 2, 180),
        ("Gold", "Wüste", 3, 500),
        ("Wasser", None, 0, 50),
    ]
    
    for res_name, terrain, tech_level, cost in deposits:
        if res_name not in resource_map:
            continue
        res_id = resource_map[res_name]
        
        terrain_id = None
        if terrain:
            cursor.execute("SELECT terrain_id FROM terrain_configs WHERE name=?", (terrain,))
            row = cursor.fetchone()
            if row:
                terrain_id = row[0]
        
        cursor.execute("""
            INSERT OR IGNORE INTO ressourcen_reserven 
            (resource_id, terrain_id, tech_level_required, search_cost_mips)
            VALUES (?, ?, ?, ?)
        """, (res_id, terrain_id, tech_level, cost))
    
    conn.commit()
    print(f"Seeded {len(deposits)} resource deposits")
    conn.close()

if __name__ == "__main__":
    seed_terrain_configs()
    seed_resource_deposits()