"""
Seed data for Lebewesen (Creatures/Animals) in Wasteland.

Covers mutant creatures, domesticated animals, and wild fauna of the wasteland.
"""

from db_config import get_connection, save_entity

LEBEWESEN_DATA = [
    # === Mutanten (Mutants) ===
    {
        "name": "Rote Scorpione",
        "typ": "Mutant",
        "staerke": 5,
        "gesundheit": 20,
        "bevoelkerung_kosten": 0,
        "beschreibung": "Gefährliche Jäger des Ödlands. Ihre rote Färbung ist ein Warnsignal für Siedler."
    },
    
    # === Haussiere (Domesticated Animals) ===
    {
        "name": "Bukhts",
        "typ": "Tier",
        "staerke": 2,
        "gesundheit": 50,
        "bevoelkerung_kosten": 0,
        "beschreibung": "Widerstandsfähige Lasttiere. Werden zum Transport schwerer Güter in den öden Landen eingesetzt."
    },
    {
        "name": "Pferd",
        "typ": "Domestiziert",
        "staerke": 3,
        "gesundheit": 40,
        "bevoelkerung_kosten": 1,
        "beschreibung": "Domestiziertes Reittier. Schneller Transport über Land, erhöht die Bewegungsgeschwindigkeit von Einheiten."
    },
    {
        "name": "Huhn",
        "typ": "Haustier",
        "staerke": 1,
        "gesundheit": 10,
        "bevoelkerung_kosten": 0,
        "beschreibung": "Kleine Geflügeltiere. Liefern Eier als Nahrungsmittel und sind einfach zu halten."
    },
    {
        "name": "Schaf",
        "typ": "Haustier",
        "staerke": 1,
        "gesundheit": 20,
        "bevoelkerung_kosten": 0,
        "beschreibung": "Widderartige Tiere der öden Lande. Liefern Wolle für Stoffproduktion und Fleisch als Nahrung."
    },
    
    # === Wilde Tiere (Wild Animals) ===
    {
        "name": "Ödlandwolf",
        "typ": "Wildtier",
        "staerke": 4,
        "gesundheit": 30,
        "bevoelkerung_kosten": 0,
        "beschreibung": "Angepasste Wölfe der öden Lande. Jagdbar für Fleisch und Fell, aber gefährlich in Rudeln."
    },
    {
        "name": "Riesenechse",
        "typ": "Mutant",
        "staerke": 7,
        "gesundheit": 60,
        "bevoelkerung_kosten": 0,
        "beschreibung": "Vergrößerte Echsen durch Strahlenmutation. Langsam aber mit hoher Panzerung."
    },
    {
        "name": "Käferkolonie",
        "typ": "Insekt",
        "staerke": 2,
        "gesundheit": 15,
        "bevoelkerung_kosten": 0,
        "beschreibung": "Sich schnell vermehrende Käfer. Einzelne Exemplare schwach, in Kolonien gefährlich."
    }
]

def seed():
    conn = get_connection()
    c = conn.cursor()
    ins = upd = 0
    print("\n🔹 Lebewesen:")
    for l in LEBEWESEN_DATA:
        if save_entity(c, "lebewesen", l, id_field="name"):
            print(f"  ✅  Lebewesen: {l['name']} ({l['typ']}) – neu")
            ins += 1
        else:
            print(f"  🔄  Lebewesen: {l['name']} ({l['typ']}) – aktualisiert")
            upd += 1
    conn.commit()
    conn.close()
    return ins, upd

if __name__ == "__main__":
    seed()
