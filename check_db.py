import sqlite3

DB_PATH = 'verbrannte_zone.db'

def check():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Check terrain_typen
    try:
        cur.execute("SELECT count(*) FROM terrain_typen")
        typen_count = cur.fetchone()[0]
        print(f"terrain_typen count: {typen_count}")
        
        cur.execute("SELECT id, name FROM terrain_typen LIMIT 10")
        print("terrain_typen samples:")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]}")
    except Exception as e:
        print(f"Error reading terrain_typen: {e}")

    # Check world_terrain
    try:
        cur.execute("SELECT count(*) FROM world_terrain")
        world_count = cur.fetchone()[0]
        print(f"world_terrain count: {world_count}")
        
        cur.execute("SELECT id, name FROM world_terrain LIMIT 10")
        print("world_terrain samples:")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]}")
    except Exception as e:
        print(f"Error reading world_terrain: {e}")

    conn.close()

if __name__ == "__main__":
    check()
