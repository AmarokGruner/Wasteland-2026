import sys
import os

# UTF-8 encoding fix for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Pfad zum aktuellen Ordner hinzufügen, damit die Module gefunden werden
sys.path.append(os.path.dirname(__file__))

from db_config import get_connection, init_tables
import seed_terrains
import seed_gebaeude
import seed_ressourcen
import seed_vorkommen
import seed_einheiten
import seed_lebewesen
import seed_artikel
import seed_regierungsformen

def seed_all():
    print("🌱 Starte umfassenden Datenbank-Seed...")
    conn = get_connection()
    init_tables(conn)
    conn.close()

    seed_terrains.seed()
    seed_gebaeude.seed()
    seed_ressourcen.seed()
    seed_vorkommen.seed()
    seed_einheiten.seed()
    seed_lebewesen.seed()
    seed_artikel.seed()
    seed_regierungsformen.seed()

    print("\n🏁 Alle Seeds erfolgreich ausgeführt.")

if __name__ == "__main__":
    seed_all()
