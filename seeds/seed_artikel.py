"""
Seed data for Artikel (Articles/Equipment) in Wasteland.

Covers all equipment types: weapons, armor, vehicles, tools, and transport.
"""

from db_config import get_connection, save_entity

ARTIKEL_DATA = [
    # === Waffen (Weapons) ===
    {
        "id": 1,
        "name": "Lederrüstung",
        "spezies": "Menschen",
        "einheittext": "Krieger",
        "modultyp": "Rüstung",
        "zugehoerig": "Militär",
        "bautyp": "Waffenwerkstatt",
        "produktionspunkte": 2,
        "rohstoffbedarf": [{"ressource": "Leder", "menge": 5}],
        "modulgroesse": 1,
        "auswirkung_einheitenwerte": {"fernkampf_panzerung": "+2"},
        "beschreibung": "Eine einfache Rüstung aus gegerbtem Leder. Bietet minimalen Schutz gegen leichte Angriffe."
    },
    {
        "id": 4,
        "name": "Kettenhemd",
        "spezies": "Menschen",
        "einheittext": "Krieger",
        "modultyp": "Rüstung",
        "zugehoerig": "Militär",
        "bautyp": "Waffenwerkstatt",
        "produktionspunkte": 5,
        "rohstoffbedarf": [{"ressource": "Eisen", "menge": 10}],
        "modulgroesse": 1,
        "auswirkung_einheitenwerte": {"fernkampf_panzerung": "+5", "geschwindigkeit": -0.2},
        "beschreibung": "Ein schweres Kettenhemd aus miteinander vermaschten Eisringen. Bietet guten Schutz, beeinträchtigt aber die Beweglichkeit."
    },
    {
        "id": 11,
        "name": "Holzschild",
        "spezies": "Menschen",
        "einheittext": "Schütze",
        "modultyp": "Schild",
        "zugehoerig": "Militär",
        "bautyp": "Waffenwerkstatt",
        "produktionspunkte": 2,
        "rohstoffbedarf": [{"ressource": "Bauholz", "menge": 5}],
        "modulgroesse": 1,
        "auswirkung_einheitenwerte": {"fernkampf_panzerung": "+3"},
        "beschreibung": "Ein einfacher Holzschild aus einem Baumstamm geschnitten. Bietet grundlegenden Schutz."
    },
    {
        "id": 18,
        "name": "Eisenschild",
        "spezies": "Menschen",
        "einheittext": "Schütze",
        "modultyp": "Schild",
        "zugehoerig": "Militär",
        "bautyp": "Waffenwerkstatt",
        "produktionspunkte": 6,
        "rohstoffbedarf": [{"ressource": "Eisen", "menge": 15}],
        "modulgroesse": 1,
        "auswirkung_einheitenwerte": {"fernkampf_panzerung": "+8", "geschwindigkeit": -0.3},
        "beschreibung": "Ein massiver Eisenschild mit Metallverstärkung. Bietet hervorragenden Schutz, verlangsamt aber den Träger."
    },
    {
        "id": 34,
        "name": "Axt",
        "spezies": "Menschen",
        "einheittext": "Kämpfer",
        "modultyp": "Waffe",
        "zugehoerig": "Militär",
        "bautyp": "Waffenwerkstatt",
        "produktionspunkte": 3,
        "rohstoffbedarf": [{"ressource": "Bauholz", "menge": 3}, {"ressource": "Eisen", "menge": 2}],
        "modulgroesse": 1,
        "auswirkung_einheitenwerte": {"nahkampf_staerke": "+4"},
        "beschreibung": "Eine robuste Kampfaxt aus Holz und Eisen. Effektiv im Nahkampf gegen leicht gepanzerte Gegner."
    },
    {
        "id": 36,
        "name": "Schwert",
        "spezies": "Menschen",
        "einheittext": "Kämpfer",
        "modultyp": "Waffe",
        "zugehoerig": "Militär",
        "bautyp": "Waffenwerkstatt",
        "produktionspunkte": 5,
        "rohstoffbedarf": [{"ressource": "Eisen", "menge": 8}],
        "modulgroesse": 1,
        "auswirkung_einheitenwerte": {"nahkampf_staerke": "+6"},
        "beschreibung": "Ein geschmiedetes Eisenschwert. Der Standard der Nahkampfwaffen in den öden Landen."
    },
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
        "beschreibung": "Ein primitiver Speer aus Holz, welcher in den richtigen Händen sehr effektiv sein kann. Geeignet zur Verteidigung und Jagd."
    },
    {
        "id": 50,
        "name": "Bogen",
        "spezies": "Menschen",
        "einheittext": "Schütze",
        "modultyp": "Fernwaffe",
        "zugehoerig": "Militär",
        "bautyp": "Waffenwerkstatt",
        "produktionspunkte": 4,
        "rohstoffbedarf": [{"ressource": "Bauholz", "menge": 5}, {"ressource": "Seil", "menge": 2}],
        "modulgroesse": 1,
        "auswirkung_einheitenwerte": {"fernkampf_staerke": "+5", "reichweite": "+2"},
        "beschreibung": "Ein einfacher Bogen aus Holz und Seil. Ermöglicht Angriffe auf Distanz."
    },
    
    # === Fahrzeuge & Transport (Vehicles & Transport) ===
    {
        "id": 58,
        "name": "Heißluftballon",
        "spezies": "Menschen",
        "einheittext": "Luftfahrzeug",
        "modultyp": "Fahrzeug",
        "zugehoerig": "Militär/Zivil",
        "bautyp": "Luftfahrtwerkstatt",
        "produktionspunkte": 15,
        "rohstoffbedarf": [{"ressource": "Stoff", "menge": 20}, {"ressource": "Bauholz", "menge": 10}],
        "modulgroesse": 3,
        "auswirkung_einheitenwerte": {"geschwindigkeit": "+2"},
        "transportkapazitaet": {"luft": 50},
        "platzbedarf": {"see": 10, "untersee": 10, "luft": 50},
        "beschreibung": "Ein Heißluftballon aus Stoff und Holz. Ermöglicht den Transport über unwegsames Terrain."
    },
    {
        "id": 61,
        "name": "Pferd",
        "spezies": "Menschen",
        "einheittext": "Reiter",
        "modultyp": "Tier",
        "zugehoerig": "Militär/Zivil",
        "bautyp": "Stall",
        "produktionspunkte": 8,
        "rohstoffbedarf": [{"ressource": "Futter", "menge": 5}],
        "modulgroesse": 1,
        "auswirkung_einheitenwerte": {"geschwindigkeit": "+3"},
        "transportkapazitaet": {"land": 15},
        "platzbedarf": {"see": 2, "untersee": 2, "luft": 2},
        "beschreibung": "Ein domestiziertes Pferd. Schneller Transport über Land, erhöht die Bewegungsgeschwindigkeit erheblich."
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
        "platzbedarf": {"see": 40, "untersee": 40, "luft": 40},
        "beschreibung": "Ein robuster Karren für den Handel. Erhöht die Transportkapazität auf Landwegen erheblich."
    },
    {
        "id": 77,
        "name": "Segelboot",
        "spezies": "Menschen",
        "einheittext": "Schiff",
        "modultyp": "Fahrzeug",
        "zugehoerig": "Militär/Zivil",
        "bautyp": "Werft",
        "produktionspunkte": 12,
        "rohstoffbedarf": [{"ressource": "Bauholz", "menge": 30}, {"ressource": "Stoff", "menge": 15}],
        "modulgroesse": 2,
        "auswirkung_einheitenwerte": {"geschwindigkeit": "+1"},
        "transportkapazitaet": {"see": 60},
        "platzbedarf": {"see": 60, "untersee": 10, "luft": 10},
        "beschreibung": "Ein Segelboot für den Transport über Gewässer. Ermöglicht Handel und Bewegung auf dem Wasser."
    },
    
    # === Werkzeuge & Spezial (Tools & Special) ===
    {
        "id": 100,
        "name": "Bukhts",
        "spezies": "Menschen",
        "einheittext": "Lasttier",
        "modultyp": "Tier",
        "zugehoerig": "Zivil",
        "bautyp": "Stall",
        "produktionspunkte": 6,
        "rohstoffbedarf": [{"ressource": "Futter", "menge": 3}],
        "modulgroesse": 1,
        "transportkapazitaet": {"land": 20},
        "beschreibung": "Ein widerstandsfähiges Lasttier der öden Lande. Wird zum Transport schwerer Güter eingesetzt."
    },
    {
        "id": 114,
        "name": "Korb",
        "spezies": "Menschen",
        "einheittext": "Korb",
        "modultyp": "Erweiterung",
        "zugehoerig": "Militär/Zivil",
        "bautyp": "kein/speziell",
        "produktionspunkte": 1,
        "rohstoffbedarf": [{"ressource": "Pflanzenfasern", "menge": 3}],
        "modulgroesse": 1,
        "transportkapazitaet": {"land": 4},
        "platzbedarf": {"see": 4, "untersee": 4, "luft": 4},
        "beschreibung": "Ein einfacher Korb aus geflochtenen Pflanzenfasern. Geringe Transportkapazität, aber leicht herzustellen."
    },
    {
        "id": 115,
        "name": "Werkzeug",
        "spezies": "Menschen",
        "einheittext": "Pionier",
        "modultyp": "Beidhändig",
        "zugehoerig": "Militär/Zivil",
        "bautyp": "kein/speziell",
        "produktionspunkte": 2,
        "rohstoffbedarf": [{"ressource": "Eisen", "menge": 3}],
        "modulgroesse": 1,
        "auswirkung_einheitenwerte": {"nahkampf_staerke": "+2"},
        "beschreibung": "Grundlegendes Werkzeugset aus Eisen. Nützlich für Bauarbeiten und im Nahkampf."
    }
]

def seed():
    conn = get_connection()
    c = conn.cursor()
    ins = upd = 0
    print("\n🔹 Artikel:")
    for a in ARTIKEL_DATA:
        if save_entity(c, "artikel", a, id_field="id"):
            print(f"  ✅  Artikel: {a['name']} (ID={a['id']}) – neu")
            ins += 1
        else:
            print(f"  🔄  Artikel: {a['name']} (ID={a['id']}) – aktualisiert")
            upd += 1
    conn.commit()
    conn.close()
    return ins, upd

if __name__ == "__main__":
    seed()
