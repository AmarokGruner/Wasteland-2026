#!/usr/bin/env python3
"""Add missing columns to provinzen table"""
import sqlite3

DB_PATH = "verbrannte_zone.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Get existing columns
    cur.execute("PRAGMA table_info(provinzen)")
    existing_cols = {row[1] for row in cur.fetchall()}

    # Define new columns to add
    new_columns = [
        ("kultureinfluss_total", "REAL DEFAULT 0.0"),
        ("kultureinfluss_owner_id", "INTEGER"),
        ("tech_production", "INTEGER DEFAULT 0"),
        ("terrain_yield_malus", "REAL DEFAULT 0.0"),
        ("provinzkonto", "REAL DEFAULT 0.0"),
        ("volkskonto", "REAL DEFAULT 0.0"),
        ("handelskonto", "REAL DEFAULT 0.0"),
        ("sea_access", "TEXT"),
        ("min_soldiers", "INTEGER DEFAULT 20"),
        ("security_bonus", "INTEGER DEFAULT 0"),
        ("current_city_level", "INTEGER DEFAULT 0"),
        ("next_required_building_id", "INTEGER"),
        ("has_bunker", "INTEGER DEFAULT 0"),
        ("is_bunker_province", "INTEGER DEFAULT 0"),
        ("bunker_defense_bonus", "REAL DEFAULT 1.3"),
    ]

    added = []
    for col_name, col_type in new_columns:
        if col_name not in existing_cols:
            try:
                cur.execute(f"ALTER TABLE provinzen ADD COLUMN {col_name} {col_type}")
                added.append(col_name)
                print(f"  [OK] Added column: {col_name}")
            except Exception as e:
                print(f"  [FAIL] Failed to add {col_name}: {e}")

    if added:
        conn.commit()
        print(f"\n[SUCCESS] Added {len(added)} columns to provinzen table")
    else:
        print("\n[SUCCESS] All columns already exist")

    conn.close()

if __name__ == "__main__":
    print("Migrating provinzen table...")
    migrate()
    print("Done!")
