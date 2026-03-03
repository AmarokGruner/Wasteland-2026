# CONTEXT_MASTER.md – v2.8.0
> Datum: 2026-03-03 | Datei: seed_buildings_v5.7.py

---

## Projektübersicht
Spiel: **Wasteland / Verbrannte Zone** – Browsergame (v3.verbranntezone.ch)
Ziel: Seed-Datei mit allen Gebäuden, Ressourcen und Vorkommen für die Flask/SQLAlchemy-Datenbank.

---

## Datenbankstand

| Datensatz  | Anzahl | Datei                  |
|------------|--------|------------------------|
| Gebäude    | 108    | seed_buildings_v5.7.py |
| Ressourcen | 65     | seed_buildings_v5.7.py |
| Vorkommen  | 20     | seed_buildings_v5.7.py |

---

## Gebäude-Schema (GEBAEUDE_DATA)

```python
{
  'id': int,
  'name': str,
  'kategorie': str,
  'bautyp': str,           # Stadt, Land, Weg, Wegkreuzung, Speziell, Vorgabe
  'ausbaubar': bool,
  'baubar': bool,          # False = Vorgabe (vorplatziert, nicht baubar)
  'nur_kueste': bool,
  'ist_feld': bool,
  'unique_gebaeude': bool,
  'tech_level': int,
  'baukosten_mips': int,
  'ausbaukosten_mips': int,
  'arbeiter': int,
  'zusatzarbeiter_pro_stufe': int,
  'wohnraum': int,
  'zusatzwohnraum_pro_stufe': int,
  'energiebedarf': int,
  'lagerkapazitaet': int,
  'rohstoffbedarf_bau': [{'ressource': str, 'menge': float}],
  'rohstoffgrundbedarf_ausbau': [{'ressource': str, 'menge': float}],
  'rohstoffverbrauch': [{'ressource': str, 'menge': float}],
  'produktion': [{'ressource': str, 'menge': float}],
  'terrain_effektivitaet': {'50': [...], '75': [...], '100': [...]},
  'vorkommen_effektivitaet': {'Vorkommen-Name': int},
  'spezial_eigenschaften': {'key': value},
  'schlachtfeld': {'key': value},
  'symbol_emoji': str, 'symbol_url': str, 'bild_url': str,
  'beschreibung': str,
}
```

### Gebäude-Kategorien (Anzahl)

| Kategorie         | Anzahl | Kategorie       | Anzahl |
|-------------------|--------|-----------------|--------|
| Industrie         | 22     | Grube           | 3      |
| Farm              | 18     | Bildung         | 1      |
| Vorgabe           | 16     | Lager           | 1      |
| Abbau             | 8      | Rüstungsindustrie | 1    |
| Wohnhaus          | 7      | Schmiede        | 1      |
| Küste             | 5      | Verteidigung    | 1      |
| Weg               | 5      | Start           | 1      |
| Tierzucht         | 5      | Ausbildung      | 1      |
| Speziell          | 6      | Ausbau          | 3      |
| Forschung         | 3      |                 |        |

---

## Ressourcen-Schema (RESSOURCEN_DATA)

```python
{
  'id': int,
  'name': str,
  'typ': str,              # Baurohstoff, Industriegut, Nahrung, Getränk,
                           # Verbrauchsgut, Genussgut, Tier, Waffentyp, Transport
  'produktionswert': int,
  'platz_land': int,       # Sonderfälle: Handelskarren=50, Wollspinnen=15, Hühner=2
  'platz_wasser': int,     # Ziegen: Land=0, Wasser=5, Luft=5
  'platz_luft': int,
  'verbrauch_pro_1000': float,  # 0 = via FAQ 2.1.10 / kein direkter Volksverbrauch
  'beschreibung': str,
}
```

### Sonder-Transportplätze

| Ressource     | Land | Wasser | Luft |
|---------------|------|--------|------|
| Handelskarren | 50   | 50     | 50   |
| Wollspinnen   | 15   | 15     | 15   |
| Hühner        | 2    | 2      | 2    |
| Ziegen        | 0    | 5      | 5    |
| Alle anderen  | 1    | 1      | 1    |

---

## Vorkommen-Schema (VORKOMMEN_DATA)

```python
{
  'id': int,
  'name': str,
  'typ': str,                 # 'geologisch', 'Oberfläche', 'unt. Seen'
  'tech': int,                # Benötigtes Techlevel
  'suchkosten': int,          # Kosten in Mips
  'beschreibung': str,
  'findwahrscheinlichkeit': {'Terrainname': int},  # Terrain → % (0–100)
}
```

### Übersicht aller 20 Vorkommen

| ID | Name        | Typ         | Tech    | Suchkosten | Max-% | Terrain-Fokus          |
|----|-------------|-------------|---------|------------|-------|------------------------|
| 1  | Wasser      | unt. Seen   | 10      | 2.000      | 100%  | Alle Terrains          |
| 2  | Steinkohle  | geologisch  | 4.000   | 75.000     | 100%  | Felsgebirge            |
| 3  | Eisenerz    | geologisch  | 2.400   | 50.000     | 100%  | Eiswüste, Gebirge      |
| 4  | Silbererz   | geologisch  | 10.000  | 150.000    | 40%   | Felsgebirge            |
| 5  | Golderz     | geologisch  | 16.000  | 180.000    | 30%   | Felsgebirge            |
| 6  | Schwefel    | geologisch  | 6.400   | 120.000    | 75%   | Felsgebirge            |
| 7  | Kies        | Oberfläche  | 660     | 15.000     | 90%   | Wüste, Sanddünen       |
| 8  | Lehm        | Oberfläche  | 60      | 5.000      | 90%   | Steppe, Savanne        |
| 9  | Ton         | Oberfläche  | 30      | 2.500      | 80%   | Steppe, Savanne        |
| 10 | Braunkohle  | Oberfläche  | 660     | 12.000     | 75%   | Hügel-Terrains         |
| 11 | Kupfererz   | geologisch  | 6.000   | 100.000    | 75%   | Felsgebirge, Gebirge   |
| 12 | Erdgas      | geologisch  | 26.000  | 120.000    | 50%   | Eiswüste               |
| 13 | Kalkstein   | Oberfläche  | 1.600   | 20.000     | 90%   | Felsgebirge            |
| 14 | Bauxit      | geologisch  | 22.000  | 250.000    | 75%   | Gebirge                |
| 15 | Erdöl       | unt. Seen   | 20.000  | 150.000    | 50%   | Wüste, Sanddünen       |
| 16 | Salpeter    | Oberfläche  | 2.000   | 50.000     | 90%   | Felsgebirge, Wüste     |
| 17 | Diamanten   | Oberfläche  | 12.000  | 130.000    | 50%   | Wüste, Steinwüste      |
| 18 | Salz        | Oberfläche  | 1.360   | 35.000     | 90%   | Sanddünen              |
| 19 | Uranerz     | geologisch  | 200.000 | 300.000    | 50%   | Eiswüste, Gebirge      |
| 20 | Neodymerz   | geologisch  | 760.000 | 500.000    | 75%   | Alle Gebirge           |

### Terrain-Besonderheiten
- **Felsgebirge**: Höchste Fundquote für fast alle geologischen Vorkommen
- **Eiswüste**: Eisenerz (100%), Uranerz (50%), Golderz (20%), Erdöl (50%)
- **Sanddünen/Wüste**: Kies (90%), Salpeter, Salz, Diamanten, Erdöl, Golderz
- **Steppe/Savanne**: Lehm (90%), Ton (80%), Braunkohle, Kies, Salz
- **Wasser**: 100% auf allen Terrains (einziges universelles Vorkommen)

---

## Wichtige Rohstoff-Ketten

| Kette          | Weg                                                    |
|----------------|--------------------------------------------------------|
| Holz → Möbel   | Edelholzfäller/Tropenholzfäller → Schreinerei          |
| Rattan-Möbel   | Tropenholzfäller → Möbelflechter                       |
| Rattan-Körbe   | Tropenholzfäller → Korbwarenflechter                   |
| Rattan-Seile   | Tropenholzfäller → Seileflechterei                     |
| Seide          | Seidenspinnerzucht → Seidenfarm → Seidenspinnerei      |
| Flachs-Stoffe  | Flachsplantage → Flachswebstube → Leinen               |
| Flachs-Seile   | Flachsplantage → Flachsseilerei → Seile                |
| Hanf-Seile     | Hanfplantage → Hanfseilerei → Seile                    |
| Papier         | Schilfbauer → Papiermacher (+ Wasser)                  |
| Tinte          | Tintenmischer ← Gummi (Kautschukplantage) + Edelholz   |
| Keramik        | Tongrube → Töpferei (+ Brennholz)                      |
| Ziegel         | Lehmgrube → Lehmziegelei (+ Brennholz)                 |
| Werkzeug       | Werkzeugmacher (Bauholz+Eisen) / Beisser-Werkstatt     |
| Mips           | Münzerei (Kupfer → 1500 Mips/Tick)                     |

---

## Float-Produktionswerte (alle bekannten)

| Gebäude           | Ressource  | Menge |
|-------------------|------------|-------|
| Lehmhaus (Bau)    | Möbel      | 0.4   |
| Blockhaus (Bau)   | Möbel      | 0.5   |
| Werkzeugmacher    | Eisen      | 0.5   |
| Münzerei          | Kupfer     | 0.05  |
| Beisser-Werkstatt | Werkzeug   | 0.5   |
| Möbelflechter     | Möbel      | 0.5   |
| Möbelflechter     | Bauholz    | 0.1   |
| Federkielhärter   | Bauholz    | 0.4   |
| Ruine-Schutt      | Werkzeug   | 0.1   |
| Grabungsstätte    | Werkzeug   | 0.5   |
| Erfinderwerkstatt | Werkzeug   | 0.5   |
| Perlentaucher     | unbekannt  | 0.2   |

---

## Spezial-Eigenschaften (bekannte Keys)

| Key                  | Gebäude-Beispiele                      |
|----------------------|----------------------------------------|
| marktpunkte          | Marktplatz (25), Ruine-Markt (10)      |
| ausbildung           | Ausbildungscamp (2), Ruine-Festung (2) |
| mipsproduktion       | Münzerei (1500), Villa (1000)          |
| techproduktion       | Ruine-Labor (2), Schulungszelt (4)…    |
| transportpunkte      | Lagerhütte (1), Kontor (1)…            |
| sicherheitsbonus     | Ruine-Festung (30)                     |
| kulturpunkte         | Glockenturm (2), Leuchtturm (2)        |
| moralbonus           | Grünanlage (300), Ruine-Park (1000)    |
| hafen                | Anlegestelle (2)                       |
| kontor               | Kontor (1), Anlegestelle (1)           |
| jagen                | Jägerhütte (10)                        |
| gewerbepunkte        | Steueramt (20)                         |
| steuerfunktion       | Steueramt (0)                          |
| bankfunktion         | Steueramt (0)                          |
| bildungspunkte       | Schulungszelt (2)                      |
| regenabhaengig       | Auffangbecken, Küstenauffangbecken     |
| festung              | Pallisadenwall (1)                     |
| schlachter           | Schlachthaus (0)                       |
| wegstufe             | Kiesweg/Kieskreuzung (3)               |
| umweltverschmutzung  | Grünanlage (-10), Ruine-Park (-10)     |
| gesundheitsbonus     | Ruine-Park (500)                       |

---

## Ausstehend / TODO

- Fehlende Gebäude-IDs (Lücken zwischen gelieferten Blöcken, Anzahl unbekannt)
- symbol_emoji, symbol_url, bild_url für alle Gebäude (werden separat befüllt)
- Gebäude mit „unbekanntem Rohstoff" in Produktion/Verbrauch (noch nicht identifiziert)
- Ressourcen mit „unbekanntem Gebäude" als Produzent/Konsument
