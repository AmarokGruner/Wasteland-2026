#!/usr/bin/env python3
"""
Database Migration Script - Add Webcrawler Fields

This script adds new columns to existing database tables for webcrawler data:
- Building images/icons (gebaeude_typen)
- Terrain images and new fields (terrain_typen)  
- Unit images (einheiten_typen)
- Article images (artikel)
- Deposit images (vorkommen)
- Government form images (regierungsformen)
- Animal template images (tier_vorlagen)

Run this script to update an existing database with the new webcrawler fields.

Usage:
    python webcrawler/migrations/001_webcrawler_fields.py
"""

import sqlite3
import sys
from pathlib import Path

# Database path - adjust if needed
PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "verbrannte_zone.db"


def migrate():
    """Add new columns to existing tables"""
    
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        return False
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    migrations = [
        # gebaeude_typen - building images
        ("gebaeude_typen", "ALTER TABLE gebaeude_typen ADD COLUMN icon_url VARCHAR(255) DEFAULT ''"),
        ("gebaeude_typen", "ALTER TABLE gebaeude_typen ADD COLUMN bild_url VARCHAR(255) DEFAULT ''"),
        
        # terrain_typen - terrain images and new fields
        ("terrain_typen", "ALTER TABLE terrain_typen ADD COLUMN bild_url VARCHAR(255) DEFAULT ''"),
        ("terrain_typen", "ALTER TABLE terrain_typen ADD COLUMN grundwasserspiegel REAL DEFAULT 50.0"),
        ("terrain_typen", "ALTER TABLE terrain_typen ADD COLUMN durchschnittliche_feuchtigkeit REAL DEFAULT 50.0"),
        
        # einheiten_typen - unit images
        ("einheiten_typen", "ALTER TABLE einheiten_typen ADD COLUMN bild_url VARCHAR(255) DEFAULT ''"),
        
        # artikel - article images
        ("artikel", "ALTER TABLE artikel ADD COLUMN bild_url VARCHAR(255) DEFAULT ''"),
        
        # vorkommen - deposit images
        ("vorkommen", "ALTER TABLE vorkommen ADD COLUMN bild_url VARCHAR(255) DEFAULT ''"),
        
        # regierungsformen - government form images
        ("regierungsformen", "ALTER TABLE regierungsformen ADD COLUMN bild_url VARCHAR(255) DEFAULT ''"),
        
        # tier_vorlagen - animal template images
        ("tier_vorlagen", "ALTER TABLE tier_vorlagen ADD COLUMN bild_url VARCHAR(255) DEFAULT ''"),
    ]
    
    for table_name, sql in migrations:
        try:
            cursor.execute(sql)
            print(f"OK: Added column to {table_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"SKIP: Column already exists in {table_name}")
            else:
                print(f"ERROR: {table_name}: {e}")
        except Exception as e:
            print(f"ERROR: {table_name}: {e}")
    
    conn.commit()
    conn.close()
    
    print("\nMigration complete!")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Webcrawler Fields Migration")
    print(f"Database: {DB_PATH}")
    print("=" * 60)
    
    success = migrate()
    sys.exit(0 if success else 1)
