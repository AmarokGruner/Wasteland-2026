# Seed city tiles coordinates for provinces (Stage 1-4)
import json
import sqlite3
DB_PATH = "verbrannte_zone.db"

def seed():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS provinzen_stadt_tile_coords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        provinzen_id INTEGER NOT NULL,
        stadtausbau_id INTEGER NOT NULL,
        stage INTEGER NOT NULL,
        coords TEXT NOT NULL,
        UNIQUE(provinzen_id, stadtausbau_id, stage)
    )
    """
    )
    # Stage 1: Camp-Kreuz (5 Felder)
    coords1 = [[7,7], [6,7], [7,6], [7,8], [8,7]]
    cur.execute("INSERT OR REPLACE INTO provinzen_stadt_tile_coords (provinzen_id, stadtausbau_id, stage, coords) VALUES (?,?,?,?)",
                (1, 1, 1, json.dumps(coords1)))
    # Stage 2: Dorf (4 diag-Felder)
    coords2 = [[6,6], [6,8], [8,6], [8,8]]
    cur.execute("INSERT OR REPLACE INTO provinzen_stadt_tile_coords (provinzen_id, stadtausbau_id, stage, coords) VALUES (?,?,?,?)",
                (1, 2, 2, json.dumps(coords2)))
    # Stage 3: Ort (Fortsetzung des Startkreuzes) – 4 Felder
    coords3 = [[7,5], [5,7], [7,9], [9,7]]
    cur.execute("INSERT OR REPLACE INTO provinzen_stadt_tile_coords (provinzen_id, stadtausbau_id, stage, coords) VALUES (?,?,?,?)",
                (1, 3, 3, json.dumps(coords3)))
    # Stage 4: Stadt – 8 Felder Erweiterung (Kreuz-Verstärkung)
    coords4 = [[7,4], [7,10], [4,7], [10,7], [4,4], [4,10], [10,4], [10,10]]
    cur.execute("INSERT OR REPLACE INTO provinzen_stadt_tile_coords (provinzen_id, stadtausbau_id, stage, coords) VALUES (?,?,?,?)",
                (1, 4, 4, json.dumps(coords4)))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    seed()
