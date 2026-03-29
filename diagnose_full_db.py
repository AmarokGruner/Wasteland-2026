import sqlite3
import os

DB_PATH = "verbrannte_zone.db"

def diagnose():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database file {DB_PATH} not found.")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"--- FULL TABLE LIST FOR {DB_PATH} ---")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for t in tables:
        print(f"Found table: {t[0]}")
        # Get schema
        cursor.execute(f"PRAGMA table_info({t[0]})")
        columns = cursor.fetchall()
        print(f"  Columns: {[c[1] for c in columns]}")

    conn.close()

if __name__ == "__main__":
    diagnose()
