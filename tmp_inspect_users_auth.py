import sqlite3
import json

DB_PATH = "verbrannte_zone.db"

def inspect_users():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    print("=== Users in DB ===")
    cur.execute("SELECT id, username, password_hash, role, player_id, tutorial_step FROM users")
    for row in cur.fetchall():
        print(dict(row))
    
    print("\n=== Players in DB ===")
    cur.execute("SELECT id, name, spawn_count FROM players")
    for row in cur.fetchall():
        print(dict(row))
        
    conn.close()

if __name__ == "__main__":
    inspect_users()
