from db_config import get_connection, save_entity

LEBEWESEN_DATA = [
    {"name": "Rote Scorpione", "typ": "Mutant", "staerke": 5, "gesundheit": 20, "bevoelkerung_kosten": 0, "beschreibung": "Gefährliche Jäger des Ödlands."},
    {"name": "Bukhts", "typ": "Tier", "staerke": 2, "gesundheit": 50, "bevoelkerung_kosten": 0, "beschreibung": "Widerstandsfähige Lasttiere."}
]

def seed():
    conn = get_connection()
    c = conn.cursor()
    ins = upd = 0
    print("\n🔹 Lebewesen:")
    for l in LEBEWESEN_DATA:
        if save_entity(c, "lebewesen", l, id_field="name"):
            print(f"  ✅  Lebewesen: {l['name']} – neu")
            ins += 1
        else:
            upd += 1
    conn.commit()
    conn.close()
    return ins, upd

if __name__ == "__main__":
    seed()
