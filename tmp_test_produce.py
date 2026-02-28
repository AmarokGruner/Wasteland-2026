import asyncio
from fastapi.testclient import TestClient
from main import app, get_db

client = TestClient(app)

def setup_test_data():
    conn = get_db()
    cur = conn.cursor()
    # Ensure player 1 has a province
    cur.execute("INSERT OR IGNORE INTO provinzen (id, player_id, world_x, world_y, name) VALUES (1, 1, 12, 20, 'Test Provinz')")
    
    # Check if a building is there, if not insert "Holzfäller"
    cur.execute("SELECT id FROM buildings WHERE player_id=1 AND world_x=12 AND world_y=20 AND building_type='Holzfäller'")
    if not cur.fetchone():
        cur.execute("INSERT INTO buildings (player_id, world_x, world_y, building_x, building_y, building_type) VALUES (1, 12, 20, 5, 5, 'Holzfäller')")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_test_data()
    print("Test data setup complete.")
    
    # Fetch lager before
    r = client.get("/player/1/provinzen/1/lager")
    print("Lager BEFORE:", r.json())
    
    # Produce
    r = client.post("/player/1/resources/produce")
    print("Produce Status:", r.status_code)
    print("Produce Response:", r.json())
    
    # Fetch lager after
    r = client.get("/player/1/provinzen/1/lager")
    print("Lager AFTER:", r.json())
