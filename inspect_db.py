import sqlite3
import os

DB_PATH = "verbrannte_zone.db"

def inspect_db():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # List tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cur.fetchall()]
    print("Tables:", tables)
    
    # Inspect each table schema
    for table in tables:
        print(f"\nSchema for {table}:")
        cur.execute(f"PRAGMA table_info({table});")
        for col in cur.fetchall():
            print(col)
            
    conn.close()

if __name__ == "__main__":
    inspect_db()
