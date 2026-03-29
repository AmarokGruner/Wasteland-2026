import sqlite3
import os

DB_PATH = 'verbrannte_zone.db'

def get_columns(table):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cur.fetchall()]
    conn.close()
    return cols

def add_column(table, col, col_type, default_val):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type} DEFAULT {default_val}")
        print(f"Added {col} to {table}")
    except sqlite3.OperationalError as e:
        print(f"Skipped {table}.{col}: {e}")
    conn.commit()
    conn.close()

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database {DB_PATH} not found.")
        return

    # Einheiten typen
    e_cols = get_columns('einheiten_typen')
    if 'spezies' not in e_cols: add_column('einheiten_typen', 'spezies', 'VARCHAR', "'Menschen'")
    if 'einheitenklasse' not in e_cols: add_column('einheiten_typen', 'einheitenklasse', 'VARCHAR', "'Infanterie'")
    if 'zugsgeschwindigkeit' not in e_cols: add_column('einheiten_typen', 'zugsgeschwindigkeit', 'FLOAT', '1.0')
    if 'transport_kapazitaet' not in e_cols: add_column('einheiten_typen', 'transport_kapazitaet', 'INTEGER', '0')
    if 'einheitengroesse' not in e_cols: add_column('einheiten_typen', 'einheitengroesse', 'INTEGER', '1')
    if 'module' not in e_cols: add_column('einheiten_typen', 'module', 'TEXT', "'[]'")
    if 'kategorie' not in e_cols: add_column('einheiten_typen', 'kategorie', 'VARCHAR', "'Infanterie'")
    if 'kosten_mips' not in e_cols: add_column('einheiten_typen', 'kosten_mips', 'INTEGER', '0')
    if 'kosten_muenzen' not in e_cols: add_column('einheiten_typen', 'kosten_muenzen', 'INTEGER', '0')

    # Artikel
    a_cols = get_columns('artikel')
    if 'kategorie' not in a_cols: add_column('artikel', 'kategorie', 'VARCHAR', "'Allgemein'")
    if 'preis_mips' not in a_cols: add_column('artikel', 'preis_mips', 'INTEGER', '0')
    if 'preis_muenzen' not in a_cols: add_column('artikel', 'preis_muenzen', 'INTEGER', '0')
    if 'rohstoffbedarf' not in a_cols: add_column('artikel', 'rohstoffbedarf', 'TEXT', "'[]'")
    if 'auswirkung_einheitenwerte' not in a_cols: add_column('artikel', 'auswirkung_einheitenwerte', 'TEXT', "'{}'")
    if 'transportkapazitaet' not in a_cols: add_column('artikel', 'transportkapazitaet', 'TEXT', "'{}'")
    if 'platzbedarf' not in a_cols: add_column('artikel', 'platzbedarf', 'TEXT', "'{}'")

    print("Migration finished.")

if __name__ == "__main__":
    migrate()
