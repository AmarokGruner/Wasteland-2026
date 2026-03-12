import sqlite3
import os

DB_PATH = "verbrannte_zone.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("Running migrations...")

    # Migrations for players table
    migrations_players = [
        ("ALTER TABLE players ADD COLUMN time_credit REAL DEFAULT 240.0", "time_credit"),
        ("ALTER TABLE players ADD COLUMN tech_level INTEGER DEFAULT 0", "tech_level")
    ]

    for sql, col in migrations_players:
        try:
            cur.execute(sql)
            print(f"Added column {col} to players.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"Column {col} already exists in players.")
            else:
                print(f"Error adding {col} to players: {e}")

    # Migrations for provinzen table
    migrations_provinzen = [
        ("ALTER TABLE provinzen ADD COLUMN population INTEGER DEFAULT 10", "population"),
        ("ALTER TABLE provinzen ADD COLUMN mips INTEGER DEFAULT 0", "mips"),
        ("ALTER TABLE provinzen ADD COLUMN moral INTEGER DEFAULT 50", "moral"),
        ("ALTER TABLE provinzen ADD COLUMN gesundheit INTEGER DEFAULT 50", "gesundheit"),
        ("ALTER TABLE provinzen ADD COLUMN marktpunkte INTEGER DEFAULT 0", "marktpunkte"),
        ("ALTER TABLE provinzen ADD COLUMN strassennetz INTEGER DEFAULT 0", "strassennetz"),
        ("ALTER TABLE provinzen ADD COLUMN einheiten_count INTEGER DEFAULT 0", "einheiten_count")
    ]

    for sql, col in migrations_provinzen:
        try:
            cur.execute(sql)
            print(f"Added column {col} to provinzen.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"Column {col} already exists in provinzen.")
            else:
                print(f"Error adding {col} to provinzen: {e}")

    conn.commit()
    conn.close()
    print("Migrations complete.")

if __name__ == "__main__":
    migrate()
