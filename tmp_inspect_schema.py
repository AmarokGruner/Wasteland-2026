import sqlite3
import json

DB_PATH = 'verbrannte_zone.db'

def inspect_schema():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    tables = [
        'users',
        'players',
        'provinzen',
        'provinz_gebaeude',
        'provinz_lager',
        'gebaeude_typen',
        'ressourcen',
        'terrain_typen',
        'world_map_cells'
    ]
    
    with open('tmp_schema_results.txt', 'w', encoding='utf-8') as f:
        for table in tables:
            f.write(f"\n=== Table: {table} ===\n")
            try:
                cur.execute(f"PRAGMA table_info({table})")
                columns = cur.fetchall()
                for col in columns:
                    f.write(f"  {col['name']} ({col['type']})\n")
                    
                cur.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
                create_sql = cur.fetchone()
                if create_sql:
                    f.write(f"\n  SQL:\n  {create_sql['sql']}\n")
            except Exception as e:
                f.write(f"  Error: {e}\n")
            
    conn.close()

if __name__ == "__main__":
    inspect_schema()
