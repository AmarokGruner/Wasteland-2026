from db_config import get_connection, save_entity

ARTIKEL_DATA = [
    {
        "id": 44,
        "name": "Holzspeer",
        "spezies": "Menschen",
        "einheittext": "Speerkämpfer",
        "modultyp": "Beidhändig",
        "zugehoerig": "Militär",
        "bautyp": "Waffenwerkstatt",
        "produktionspunkte": 3,
        "rohstoffbedarf": [{"ressource": "Bauholz", "menge": 3}],
        "modulgroesse": 1,
        "auswirkung_einheitenwerte": {"nahkampf_staerke": "+3"},
        "beschreibung": "Ein Primitiver Speer aus Holz, welche in den richtigen Händen sehr effektiv sein kann. Er ist gleichermaßen geeignet zur Verteidigung und Jagd wilder Tiere."
    },
    {
        "id": 66,
        "name": "Handelskarren",
        "spezies": "Menschen",
        "einheittext": "Handelskarren",
        "modultyp": "Erweiterung",
        "zugehoerig": "Militär/Zivil",
        "bautyp": "Karrenwerkstatt",
        "produktionspunkte": 4,
        "rohstoffbedarf": [{"ressource": "Bauholz", "menge": 20}],
        "modulgroesse": 1,
        "auswirkung_einheitenwerte": {"geschwindigkeit": -0.5, "fernkampf_panzerung": "+2"},
        "transportkapazitaet": {"land": 99},
        "platzbedarf": {"see": 40, "untersee": 40, "luft": 40}
    },
    {
        "id": 114,
        "name": "Korb",
        "spezies": "Menschen",
        "einheittext": "Korb",
        "modultyp": "Erweiterung",
        "zugehoerig": "Militär/Zivil",
        "bautyp": "kein/speziell",
        "modulgroesse": 1,
        "transportkapazitaet": {"land": 4},
        "platzbedarf": {"see": 4, "untersee": 4, "luft": 4}
    },
    {
        "id": 115,
        "name": "Werkzeug",
        "spezies": "Menschen",
        "einheittext": "Pionier",
        "modultyp": "Beidhändig",
        "zugehoerig": "Militär/Zivil",
        "bautyp": "kein/speziell",
        "modulgroesse": 1,
        "auswirkung_einheitenwerte": {"nahkampf_staerke": "+2"}
    }
]

def seed():
    conn = get_connection()
    c = conn.cursor()
    ins = upd = 0
    print("\n🔹 Artikel:")
    for a in ARTIKEL_DATA:
        if save_entity(c, "artikel", a, id_field="id"):
            print(f"  ✅  Artikel: {a['name']} – neu")
            ins += 1
        else:
            print(f"  🔄  Artikel: {a['name']} – aktualisiert")
            upd += 1
    conn.commit()
    conn.close()
    return ins, upd

if __name__ == "__main__":
    seed()
