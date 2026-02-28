import asyncio
import os
from main import produce_resources, get_lager, get_db

async def run_test():
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT id, world_x, world_y FROM provinzen WHERE player_id=1 LIMIT 1")
    prov = cur.fetchone()
    if not prov:
        print("Keine Provinz!")
        return
        
    p_id = prov["id"]
    wx = prov["world_x"]
    wy = prov["world_y"]
    
    cur.execute("DELETE FROM buildings WHERE player_id=1")
    cur.execute("INSERT INTO buildings (player_id, world_x, world_y, building_x, building_y, building_type) VALUES (1, ?, ?, 5, 5, 'Holzfäller')", (wx, wy))
    cur.execute("INSERT INTO buildings (player_id, world_x, world_y, building_x, building_y, building_type) VALUES (1, ?, ?, 6, 6, 'Sägegrube')", (wx, wy))
    
    cur.execute("INSERT OR REPLACE INTO provinz_lager (provinz_id, ressource_id, menge) SELECT ?, id, 5 FROM ressourcen WHERE name='Bauholz'", (p_id,))
    
    conn.commit()
    conn.close()

    print("--- LAGER VOR PRODUKTION ---")
    lager_vor = await get_lager(1, p_id)
    print(lager_vor)

    print("\n--- PRODUKTION ---")
    res = await produce_resources(1)
    print(res)

    print("\n--- LAGER NACH PRODUKTION ---")
    lager_nach = await get_lager(1, p_id)
    print(lager_nach)

if __name__ == "__main__":
    asyncio.run(run_test())
