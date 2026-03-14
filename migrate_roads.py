import sqlite3
import os

DB_PATH = "verbrannte_zone.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Datenbank nicht gefunden: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Check if table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='provinz_strassen'")
    if cur.fetchone():
        print("Tabelle 'provinz_strassen' existiert bereits")
    else:
        # Create RoadInstance table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS provinz_strassen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provinz_id INTEGER NOT NULL,
                gebaeude_typ_id INTEGER NOT NULL,
                x INTEGER NOT NULL,
                y INTEGER NOT NULL,
                FOREIGN KEY (provinz_id) REFERENCES provinzen(id),
                FOREIGN KEY (gebaeude_typ_id) REFERENCES gebaeude_typen(id)
            )
        """)
        print("Tabelle 'provinz_strassen' erstellt")
    
    # Add unique constraint for road positions
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_road_position ON provinz_strassen (provinz_id, x, y)")
    
    conn.commit()
    conn.close()
    print("Migration abgeschlossen")

if __name__ == "__main__":
    migrate()