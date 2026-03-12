import sqlite3
import os

DB_PATH = "verbrannte_zone.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("Running Tick Engine migrations...")

    # Create system_locks table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS system_locks (
        task_name TEXT PRIMARY KEY,
        is_running INTEGER DEFAULT 0,
        last_run TIMESTAMP,
        error_count INTEGER DEFAULT 0
    )
    """)
    print("Table system_locks checked/created.")

    # Create tick_logs table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tick_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        duration_ms INTEGER,
        status TEXT,
        provinces_processed INTEGER,
        details TEXT
    )
    """)
    print("Table tick_logs checked/created.")

    # Seed initial lock
    cur.execute("INSERT OR IGNORE INTO system_locks (task_name) VALUES ('server_tick')")
    
    conn.commit()
    conn.close()
    print("Migrations complete.")

if __name__ == "__main__":
    migrate()
