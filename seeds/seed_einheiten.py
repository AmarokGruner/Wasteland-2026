from db_config import get_connection, save_entity

EINHEITEN_DATA = [
    {
        "id": 1,
        "name": "Rekrut(en)",
        "spezies": "Menschen",
        "einheitenklasse": "Infanterie",
        "zugehoerig": "Militär",
        "fortbewegung": "Boden",
        "erstellbedingung": "keine",
        "max_reichweite": "Nahkampf",
        "geschwindigkeit": 1.0,
        "nahkampf_staerke": 2,
        "nahkampf_panzerung": 2,
        "fernkampf_panzerung": 2,
        "einheitengroesse": 1,
        "transport_land": 1,
        "platzbedarf_see": 10,
        "platzbedarf_untersee": 10,
        "platzbedarf_luft": 10,
        "module": "[{\"typ\": \"Rekruten\", \"menge\": 1}]",
        "beschreibung": ""
    },
    {
        "id": 2,
        "name": "Handelskarren",
        "spezies": "Menschen",
        "einheitenklasse": "Handelsfahrzeug",
        "zugehoerig": "Zivil",
        "fortbewegung": "Boden",
        "erstellbedingung": "keine",
        "max_reichweite": "Nahkampf",
        "geschwindigkeit": 0.5,
        "nahkampf_staerke": 2,
        "nahkampf_panzerung": 2,
        "fernkampf_panzerung": 4,
        "einheitengroesse": 3,
        "transport_land": 100,
        "platzbedarf_see": 50,
        "platzbedarf_untersee": 50,
        "platzbedarf_luft": 50,
        "module": "[{\"typ\": \"Siedler\", \"menge\": 1}, {\"typ\": \"Handelskarren\", \"menge\": 1}]",
        "beschreibung": ""
    },
    {
        "id": 10,
        "name": "Speerkämpfer",
        "spezies": "Menschen",
        "einheitenklasse": "Infanterie",
        "zugehoerig": "Militär",
        "fortbewegung": "Boden",
        "erstellbedingung": "keine",
        "max_reichweite": "Nahkampf",
        "geschwindigkeit": 1.0,
        "nahkampf_staerke": 5,
        "nahkampf_panzerung": 2,
        "fernkampf_panzerung": 2,
        "einheitengroesse": 1,
        "transport_land": 1,
        "platzbedarf_see": 10,
        "platzbedarf_untersee": 10,
        "platzbedarf_luft": 10,
        "module": "[{\"typ\": \"Rekruten\", \"menge\": 1}, {\"typ\": \"Holzspeer\", \"menge\": 1}]",
        "beschreibung": ""
    },
    {
        "id": 21,
        "name": "Siedler",
        "spezies": "Menschen",
        "einheitenklasse": "Zivilist",
        "zugehoerig": "Zivil",
        "fortbewegung": "Boden",
        "erstellbedingung": "keine",
        "max_reichweite": "Nahkampf",
        "geschwindigkeit": 1.0,
        "nahkampf_staerke": 2,
        "nahkampf_panzerung": 2,
        "fernkampf_panzerung": 2,
        "einheitengroesse": 1,
        "transport_land": 1,
        "platzbedarf_see": 10,
        "platzbedarf_untersee": 10,
        "platzbedarf_luft": 10,
        "module": "[{\"typ\": \"Siedler\", \"menge\": 1}]",
        "beschreibung": ""
    },
    {
        "id": 34,
        "name": "Handelskarren",
        "spezies": "Menschen",
        "einheitenklasse": "",
        "zugehoerig": "Zivil",
        "fortbewegung": "Boden",
        "erstellbedingung": "keine",
        "max_reichweite": "0",
        "geschwindigkeit": 0.5,
        "nahkampf_staerke": 2,
        "nahkampf_panzerung": 2,
        "fernkampf_panzerung": 4,
        "einheitengroesse": 1,
        "transport_land": 100,
        "platzbedarf_see": 109,
        "platzbedarf_untersee": 109,
        "platzbedarf_luft": 109,
        "module": "[{\"typ\": \"Siedler\", \"menge\": 1}, {\"typ\": \"Handelskarren\", \"menge\": 1}]",
        "beschreibung": ""
    },
    {
        "id": 120,
        "name": "Handelskarren",
        "spezies": "Menschen",
        "einheitenklasse": "Handelsfahrzeug",
        "zugehoerig": "Militär",
        "fortbewegung": "Boden",
        "erstellbedingung": "keine",
        "max_reichweite": "Nahkampf",
        "geschwindigkeit": 0.5,
        "nahkampf_staerke": 2,
        "nahkampf_panzerung": 2,
        "fernkampf_panzerung": 4,
        "einheitengroesse": 3,
        "transport_land": 100,
        "platzbedarf_see": 50,
        "platzbedarf_untersee": 50,
        "platzbedarf_luft": 50,
        "module": "[{\"typ\": \"Rekruten\", \"menge\": 1}, {\"typ\": \"Handelskarren\", \"menge\": 1}]",
        "beschreibung": ""
    },
    {
        "id": 133,
        "name": "Pionier",
        "spezies": "Menschen",
        "einheitenklasse": "Infanterie",
        "zugehoerig": "Militär",
        "fortbewegung": "Boden",
        "erstellbedingung": "keine",
        "max_reichweite": "Nahkampf",
        "geschwindigkeit": 1.0,
        "nahkampf_staerke": 4,
        "nahkampf_panzerung": 2,
        "fernkampf_panzerung": 2,
        "einheitengroesse": 1,
        "transport_land": 1,
        "platzbedarf_see": 10,
        "platzbedarf_untersee": 10,
        "platzbedarf_luft": 10,
        "module": "[{\"typ\": \"Rekruten\", \"menge\": 1}, {\"typ\": \"Werkzeug\", \"menge\": 1}]",
        "beschreibung": ""
    }
]

def seed():
    conn = get_connection()
    c = conn.cursor()
    ins = upd = 0
    print(f"\n🔹 Einheiten typen:")
    for row in EINHEITEN_DATA:
        if save_entity(c, "einheiten_typen", row):
            print(f"  ✅  ID {row['id']:>3} | {row['name']} – neu")
            ins += 1
        else:
            upd += 1
    conn.commit()
    conn.close()
    print(f"   → {ins} neu, {upd} aktualisiert")
    return ins, upd

if __name__ == '__main__':
    seed()
