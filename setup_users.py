#!/usr/bin/env python3
"""Create users table and add test users."""
import sqlite3, hashlib

DB_PATH = "verbrannte_zone.db"

def hash_password(password):
    """Simple password hashing."""
    return hashlib.sha256(password.encode()).hexdigest()

def setup_users():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Create users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'player',
            player_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES players(id)
        )
    """)
    
    # Check if users already exist
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        # Create test users
        users = [
            ("fabian", "123456", "player", 1),
            ("felix", "345678", "player", 2),
            ("admin", "admin", "admin", None),
        ]
        
        for username, password, role, player_id in users:
            pw_hash = hash_password(password)
            cur.execute("""
                INSERT INTO users (username, password_hash, role, player_id)
                VALUES (?, ?, ?, ?)
            """, (username, pw_hash, role, player_id))
            print(f"  Created user: {username} (role: {role})")
        
        conn.commit()
        print(f"\nCreated {len(users)} test users:")
        print("  - fabian / 123456 (player)")
        print("  - felix / 345678 (player)")
        print("  - admin / admin (admin)")
    else:
        print("Users table already exists, skipping creation.")
    
    conn.close()

if __name__ == "__main__":
    print("Setting up users table...")
    setup_users()
    print("Done!")
