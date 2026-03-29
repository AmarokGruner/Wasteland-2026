import sqlite3
import os

DB_PATH = "verbrannte_zone.db"

def diagnose():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database file {DB_PATH} not found in current directory.")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"--- Diagnosing {DB_PATH} ---")
    
    # Check for provinz_lager
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='provinz_lager'")
    if cursor.fetchone():
        print("OK: Table 'provinz_lager' EXISTS.")
    else:
        print("ERROR: Table 'provinz_lager' MISSING.")
        
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    print(f"Tables present: {', '.join(tables)}")
    
    conn.close()

if __name__ == "__main__":
    diagnose()
