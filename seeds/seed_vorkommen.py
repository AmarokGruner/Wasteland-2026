from db_config import get_connection, save_entity

VORKOMMEN_DATA = [
    {
        "id": 1,
        "name": "Wasser",
        "typ": "unt. Seen",
        "tech": 10,
        "suchkosten": 2000,
        "beschreibung": "Wasser ist die erste und wohl auch wichtigste Ressource für die Existenz auf den Inseln der Verbrannten Zone. Das kühle Nass ist fast immer in jeder Region zu finden, aber in Massen kommt sie nur im Meer, in den Tropen und in den Sümpfen der Insel vor.",
        "findwahrscheinlichkeit": "{\"Grasland\": 100, \"Steppe\": 100, \"Ödland\": 100, \"Wald\": 100, \"Grasfelsland\": 100, \"Sumpfland\": 100, \"Grashügel\": 100, \"Grasgebirge\": 100, \"Eiswüste\": 100, \"Wüste\": 100, \"Tropensumpf\": 100, \"Dschungel\": 100, \"Sanddünen\": 100, \"Felsgebirge\": 100, \"Ödhügel\": 100, \"Ödgebirge\": 100, \"Stepphügel\": 100, \"Steppgebirge\": 100, \"Ödfelsland\": 100, \"Steppfelsland\": 100, \"Grünland\": 100, \"Savanne\": 100, \"Grünhügel\": 100, \"Savannenhügel\": 100, \"Grüngebirge\": 100, \"Savannengebirge\": 100, \"Grünfelsland\": 100, \"Savannenfelsland\": 100, \"Brachland\": 100, \"Brachfelsland\": 100, \"Brachhügel\": 100, \"Brachgebirge\": 100, \"Pampa\": 100, \"Weideland\": 100, \"Regenwald\": 100, \"Pampagebirge\": 100, \"Plateau\": 100, \"Hochnebelwald\": 100, \"Pampafelsland\": 100, \"Weidefelsland\": 100, \"Steinwüste\": 100}"
    },
    {
        "id": 2,
        "name": "Steinkohle",
        "typ": "geologisch",
        "tech": 4000,
        "suchkosten": 75000,
        "beschreibung": "Ob als Stein- oder Braunkohle, beides kann dazu verwendet werden, um Maschinen anzutreiben, chemische Prozesse zu beeinflussen oder um es für die Wärmegewinnung einzusetzen. Man findet die Kohlevorkommen immer dort, wo auch massive Berge zu finden sind.",
        "findwahrscheinlichkeit": "{\"Grashügel\": 50, \"Grasgebirge\": 75, \"Eiswüste\": 50, \"Felsgebirge\": 100, \"Ödgebirge\": 75, \"Stepphügel\": 50, \"Steppgebirge\": 75, \"Grünhügel\": 50, \"Savannenhügel\": 50, \"Grüngebirge\": 75, \"Savannengebirge\": 75, \"Brachgebirge\": 75}"
    },
    {
        "id": 3,
        "name": "Eisenerz",
        "typ": "geologisch",
        "tech": 2400,
        "suchkosten": 50000,
        "beschreibung": "Eisen ist das am häufigsten verwendete Material für solide Gebäude, Gegenstände, Waffen und Rüstungen. Die Eiswüsten bieten reiche Erzvorkommen, aber Wissenschaftler sind sich noch nicht einig, wie es dorthin gelangte.",
        "findwahrscheinlichkeit": "{\"Grashügel\": 50, \"Grasgebirge\": 75, \"Eiswüste\": 100, \"Felsgebirge\": 75, \"Ödgebirge\": 75, \"Stepphügel\": 50, \"Steppgebirge\": 75, \"Grünhügel\": 50, \"Savannenhügel\": 50, \"Grüngebirge\": 75, \"Savannengebirge\": 75, \"Brachgebirge\": 75}"
    },
    {
        "id": 4,
        "name": "Silbererz",
        "typ": "geologisch",
        "tech": 10000,
        "suchkosten": 150000,
        "beschreibung": "Ohne Silber wäre die Münzproduktion unmöglich. Es glänzt, sieht gut aus und ist gut zu verarbeiten. Die Wahrscheinlichkeit, es in den hiesigen Gebirgen zu finden, liegt bei ca. 15%.",
        "findwahrscheinlichkeit": "{\"Grashügel\": 10, \"Grasgebirge\": 20, \"Sanddünen\": 30, \"Felsgebirge\": 40, \"Stepphügel\": 20, \"Steppgebirge\": 30, \"Grünhügel\": 10, \"Savannenhügel\": 20, \"Grüngebirge\": 20, \"Savannengebirge\": 30}"
    },
    {
        "id": 5,
        "name": "Golderz",
        "typ": "geologisch",
        "tech": 16000,
        "suchkosten": 180000,
        "beschreibung": "Ein Erz, wofür viele Leute und Staaten töten würden. Gold ist wohl eines der bekanntesten Edelmetalle auf der Erde. Forscher ermittelten, dass das Golderz nur zu ca. 6-9% zu finden sei.",
        "findwahrscheinlichkeit": "{\"Grasgebirge\": 10, \"Eiswüste\": 20, \"Sanddünen\": 20, \"Felsgebirge\": 30, \"Stepphügel\": 10, \"Steppgebirge\": 20, \"Savannenhügel\": 10, \"Grüngebirge\": 10, \"Savannengebirge\": 20}"
    },
    {
        "id": 6,
        "name": "Schwefel",
        "typ": "geologisch",
        "tech": 6400,
        "suchkosten": 120000,
        "beschreibung": "Der Stoff wird für die Waffenindustrie benötigt und wird dort in Schwarzpulver und Sprengstoffen verarbeitet. Außerdem erhält er einen wichtigen Nutzen in der Chemieindustrie zur Herstellung der Schwefelsäure.",
        "findwahrscheinlichkeit": "{\"Grasgebirge\": 25, \"Felsgebirge\": 75, \"Steppgebirge\": 50, \"Grüngebirge\": 25, \"Savannengebirge\": 50}"
    },
    {
        "id": 7,
        "name": "Kies",
        "typ": "Oberfläche",
        "tech": 660,
        "suchkosten": 15000,
        "beschreibung": "Eine weitere Möglichkeit den wichtigen Baustoff Kies abzubauen ist der Sedimenttagebau. Hier werden mit Hilfe einer Vielzahl von Werkzeugen große Löcher gegraben um Kies und Sand abzubauen.",
        "findwahrscheinlichkeit": "{\"Steppe\": 50, \"Grasfelsland\": 75, \"Grashügel\": 50, \"Wüste\": 90, \"Sanddünen\": 90, \"Stepphügel\": 75, \"Steppfelsland\": 75, \"Savanne\": 50, \"Grünhügel\": 50, \"Savannenhügel\": 75, \"Grünfelsland\": 75, \"Savannenfelsland\": 75}"
    },
    {
        "id": 8,
        "name": "Lehm",
        "typ": "Oberfläche",
        "tech": 60,
        "suchkosten": 5000,
        "beschreibung": "Kinder lieben es mit Lehm zu spielen, denn diese Ressource ermöglicht es unter Wärmezufuhr, feste Ziegel herzustellen. Die Öd- und Brachlanden sind wahre Fundgruben für Lehm.",
        "findwahrscheinlichkeit": "{\"Steppe\": 90, \"Stepphügel\": 75, \"Steppfelsland\": 50, \"Savanne\": 90, \"Savannenhügel\": 75, \"Savannenfelsland\": 50}"
    },
    {
        "id": 9,
        "name": "Ton",
        "typ": "Oberfläche",
        "tech": 30,
        "suchkosten": 2500,
        "beschreibung": "",
        "findwahrscheinlichkeit": "{\"Steppe\": 80, \"Stepphügel\": 50, \"Steppfelsland\": 50, \"Savanne\": 80, \"Savannenhügel\": 50, \"Savannenfelsland\": 50}"
    },
    {
        "id": 10,
        "name": "Braunkohle",
        "typ": "Oberfläche",
        "tech": 660,
        "suchkosten": 12000,
        "beschreibung": "",
        "findwahrscheinlichkeit": "{\"Steppe\": 50, \"Grasfelsland\": 50, \"Grashügel\": 50, \"Stepphügel\": 75, \"Steppfelsland\": 50, \"Savanne\": 50, \"Grünhügel\": 50, \"Savannenhügel\": 75, \"Grünfelsland\": 50, \"Savannenfelsland\": 50}"
    },
    {
        "id": 11,
        "name": "Kupfererz",
        "typ": "geologisch",
        "tech": 6000,
        "suchkosten": 100000,
        "beschreibung": "",
        "findwahrscheinlichkeit": "{\"Grashügel\": 25, \"Grasgebirge\": 50, \"Eiswüste\": 50, \"Felsgebirge\": 75, \"Stepphügel\": 50, \"Steppgebirge\": 75, \"Grünhügel\": 25, \"Savannenhügel\": 50, \"Grüngebirge\": 50, \"Savannengebirge\": 75}"
    },
    {
        "id": 12,
        "name": "Erdgas",
        "typ": "geologisch",
        "tech": 26000,
        "suchkosten": 120000,
        "beschreibung": "",
        "findwahrscheinlichkeit": "{\"Eiswüste\": 50, \"Wüste\": 25, \"Sanddünen\": 25}"
    },
    {
        "id": 13,
        "name": "Kalkstein",
        "typ": "Oberfläche",
        "tech": 1600,
        "suchkosten": 20000,
        "beschreibung": "",
        "findwahrscheinlichkeit": "{\"Grashügel\": 75, \"Grasgebirge\": 75, \"Sanddünen\": 75, \"Felsgebirge\": 90, \"Stepphügel\": 75, \"Steppgebirge\": 75, \"Grünhügel\": 75, \"Savannenhügel\": 75, \"Grüngebirge\": 75, \"Savannengebirge\": 75}"
    },
    {
        "id": 14,
        "name": "Bauxit",
        "typ": "geologisch",
        "tech": 22000,
        "suchkosten": 250000,
        "beschreibung": "",
        "findwahrscheinlichkeit": "{\"Grashügel\": 50, \"Grasgebirge\": 75, \"Felsgebirge\": 75, \"Stepphügel\": 50, \"Steppgebirge\": 75, \"Grünhügel\": 50, \"Savannenhügel\": 50, \"Grüngebirge\": 75, \"Savannengebirge\": 75}"
    },
    {
        "id": 15,
        "name": "Erdöl",
        "typ": "unt. Seen",
        "tech": 20000,
        "suchkosten": 150000,
        "beschreibung": "Das schwarze Gold. Die wohl ruhmreichste Entdeckung für die \"neue\" Erdbevölkerung. Einige wenige Menschen wissen von Erzählungen, dass das schwarze Gold einst für den Zerfall der Erde und die große Katastrophe verantwortlich gewesen sein soll.",
        "findwahrscheinlichkeit": "{\"Eiswüste\": 50, \"Wüste\": 50, \"Sanddünen\": 50}"
    },
    {
        "id": 16,
        "name": "Salpeter",
        "typ": "Oberfläche",
        "tech": 2000,
        "suchkosten": 50000,
        "beschreibung": "Ein Nitrat, das zur Herstellung von Schwarzpulver benötigt wird.",
        "findwahrscheinlichkeit": "{\"Wüste\": 50, \"Sanddünen\": 75, \"Felsgebirge\": 90, \"Steinwüste\": 50}"
    },
    {
        "id": 17,
        "name": "Diamanten",
        "typ": "Oberfläche",
        "tech": 12000,
        "suchkosten": 130000,
        "beschreibung": "",
        "findwahrscheinlichkeit": "{\"Wüste\": 50, \"Sanddünen\": 25, \"Felsgebirge\": 25, \"Steinwüste\": 50}"
    },
    {
        "id": 18,
        "name": "Salz",
        "typ": "Oberfläche",
        "tech": 1360,
        "suchkosten": 35000,
        "beschreibung": "",
        "findwahrscheinlichkeit": "{\"Steppe\": 25, \"Wüste\": 75, \"Sanddünen\": 90, \"Stepphügel\": 50, \"Savanne\": 25, \"Savannenhügel\": 50}"
    },
    {
        "id": 19,
        "name": "Uranerz",
        "typ": "geologisch",
        "tech": 200000,
        "suchkosten": 300000,
        "beschreibung": "",
        "findwahrscheinlichkeit": "{\"Grasgebirge\": 25, \"Eiswüste\": 50, \"Felsgebirge\": 25, \"Steppgebirge\": 25, \"Grüngebirge\": 25, \"Savannengebirge\": 25}"
    },
    {
        "id": 20,
        "name": "Neodymerz",
        "typ": "geologisch",
        "tech": 760000,
        "suchkosten": 500000,
        "beschreibung": "",
        "findwahrscheinlichkeit": "{\"Grasgebirge\": 75, \"Felsgebirge\": 75, \"Ödgebirge\": 75, \"Steppgebirge\": 75, \"Grüngebirge\": 75, \"Savannengebirge\": 75}"
    }
]

def seed():
    conn = get_connection()
    c = conn.cursor()
    ins = upd = 0
    print(f"\n🔹 Vorkommen:")
    for row in VORKOMMEN_DATA:
        if save_entity(c, "vorkommen", row):
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
