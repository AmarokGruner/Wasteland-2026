import sqlite3
import json

DB_PATH = "verbrannte_zone.db"

JSON_FIELDS = {"rohstoffbedarf_bau", "rohstoffgrundbedarf_ausbau", "rohstoffverbrauch",
               "produktion", "terrain_effektivitaet", "vorkommen_effektivitaet",
               "spezial_eigenschaften", "schlachtfeld", "findwahrscheinlichkeit", 
               "gebaeude_effektivitaet", "module", "aufwertungen", "abwertungen",
               "boni", "voraussetzungen", "bonus_malus", "rohstoffbedarf", 
               "auswirkung_einheitenwerte", "transportkapazitaet", "platzbedarf"}
BOOL_FIELDS = {"baubar", "ausbaubar", "unique_gebaeude", "nur_kueste", "ist_feld", "startgebiet"}

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_tables(conn):
    """Initialisiert Tabellen basierend auf models.py (SQLAlchemy)"""
    import sys
    import os
    
    # Pfad zum Projekt-Root hinzufügen
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    from app.models import Base
    from app.database import engine as sa_engine
    
    # Erstelle alle Tabellen basierend auf den Model-Klassen
    Base.metadata.create_all(bind=sa_engine)
    
    print("✅ Tabellen aus models.py erstellt")

def save_entity(c, table, data, id_field="id"):
    """Universelle Hilfsfunktion zum Speichern (INSERT/UPDATE)."""
    if id_field in data:
        c.execute(f"SELECT {id_field} FROM {table} WHERE {id_field}=?", (data[id_field],))
        exists = c.fetchone()
    else:
        # Falls keine ID da ist (z.B. bei name als Unique Key)
        # Hier gehen wir davon aus, dass wir eine ID haben
        exists = None

    vals = {k: (json.dumps(v, ensure_ascii=False) if k in JSON_FIELDS and isinstance(v, (dict, list))
               else (int(v) if k in BOOL_FIELDS else v))
           for k, v in data.items()}

    if exists:
        sp = [f"{k}=? " for k in vals if k != id_field]
        c.execute(f"UPDATE {table} SET {','.join(sp)}, updated_at=CURRENT_TIMESTAMP WHERE {id_field}=?",
                  [vals[k] for k in vals if k != id_field] + [data[id_field]])
        return False # Updated
    else:
        cols = list(vals.keys())
        c.execute(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})",
                  [vals[k] for k in cols])
        return True # Inserted

if __name__ == "__main__":
    conn = get_connection()
    init_tables(conn)
    conn.close()
    print("Database initialization/migration complete.")
