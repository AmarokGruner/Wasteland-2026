# Webcrawler für Verbrannte Zone

Ein Python-Tool zum automatisierten Scrapen und Synchronisieren von Daten aus https://v3.verbranntezone.ch/ mit der lokalen Datenbank.

---

## Installation

### 1. Dependencies installieren

```bash
pip install requests beautifulsoup4 lxml python-dotenv
```

### 2. Konfiguration erstellen

Kopiere `.env.example` nach `.env` und passe die Werte an:

```bash
cp .env.example .env
```

Die `.env`-Datei enthält:
- Login-Credentials für die Website
- Optional: Pfad zur Datenbank

---

## Verwendung

### Alle Kategorien synchronisieren

```bash
python main.py
```

### Nur bestimmte Kategorien

```bash
python main.py --category gebaeude rohstoffe
```

### Dry-Run (Vorschau ohne DB-Schreiben)

```bash
python main.py --dry-run
```

### Verbose-Modus (detaillierte Logs)

```bash
python main.py --verbose
```

### Kombination

```bash
python main.py --category gebaeude --dry-run --verbose
```

---

## Unterstützte Kategorien

| Kategorie | Beschreibung | DB-Tabelle | Parser-Modul |
|-----------|--------------|------------|--------------|
| `gebaeude` | Gebäude-Typen | `gebaeude_typen` | `parsers/gebaeude_parser.py` |
| `rohstoffe` | Ressourcen-Typen | `ressourcen` | `parsers/rohstoffe_parser.py` |
| `vorkommen` | Rohstoff-Vorkommen | `vorkommen` | `parsers/vorkommen_parser.py` |
| `terrains` | Terrain-Typen | `terrain_typen`, `terrain_configs` | `parsers/terrain_parser.py` |
| `lebewesen` | Tiere/Lebewesen | `tier_vorlagen`, `AnimalTemplate` | `parsers/lebewesen_parser.py` |
| `artikel` | Artikel/Items | `artikel` | `parsers/artikel_parser.py` |
| `einheiten` | Einheiten-Typen | `einheiten_typen`, `UnitType` | `parsers/einheiten_parser.py` |
| `regierungen` | Regierungsformen | `regierungsformen` | `parsers/regierungen_parser.py` |

---

## Funktionsweise

### 1. Login
Das Tool meldet sich mit den Credentials aus `.env` an der Website an und speichert die Session-Cookies.

### 2. Listen-Scan
Für jede Kategorie wird die jeweilige List-Seite gescraped (z.B. `gebaeudelist.php`).

### 3. ID-Extraktion
Aus der List-Seite werden alle Einträge identifiziert (via Links mit `?id={nummer}`).

### 4. Detail-Fetch
Für jede ID wird die Detail-Seite geladen (z.B. `gebaeudevorschau.php?id=123`).

### 5. Parsing
Das HTML der Detail-Seite wird mit BeautifulSoup geparst und in ein strukturiertes Python-Dict umgewandelt.

### 6. Sync
Die gescrapten Daten werden mit der lokalen SQLite-DB abgeglichen:
- **INSERT**: Neue Datensätze werden eingefügt
- **UPDATE**: Geänderte Datensätze werden aktualisiert
- **SKIP**: Unveränderte Datensätze werden übersprungen

---

## Ausgabe

Das Tool erstellt:
- **Console-Logs**: Echtzeit-Ausgabe im Terminal
- **Log-Files**: Detaillierte Protokolle im `logs/` Verzeichnis (eine Log-Datei pro Lauf)
- **Cache**: Roh-HTML im `cache/` Verzeichnis (für Debugging)

---

## Sync-Logik

Für jeden gescrapten Datensatz:

1. **Existenz-Check**: Ist die ID bereits in der DB?
   - ❌ NEIN → **INSERT** (neuer Datensatz)
   - ✅ JA → Weiter zu Schritt 2

2. **Feld-Vergleich**: Haben sich relevante Felder geändert?
   - ✅ ÄNDERUNG → **UPDATE** (Datensatz aktualisieren)
   - ❌ KEINE ÄNDERUNG → **SKIP** (keine Aktion)

---

## Fehlerbehandlung

| Fehlertyp | Verhalten |
|-----------|-----------|
| Login-Fehler | Abbruch mit Fehlermeldung |
| HTTP-Timeout | 3 Retries mit exponentiellem Backoff (1s, 2s, 4s) |
| HTTP-Fehler (403/404) | Wird protokolliert, Prozess setzt fort |
| DB-Fehler | Rollback der aktuellen Transaktion |

---

## Rate-Limiting

Das Tool wartet automatisch `1.0` Sekunden zwischen Requests, um:
- Server-Überlastung zu vermeiden
- Rate-Limiting (429 Errors) zu verhindern
- Fair Use der Website zu gewährleisten

---

## Sicherheitshinweise

1. **Credentials**: Die `.env`-Datei enthält sensible Daten
   - Nicht im Git committen (`.gitignore` prüft das)
   - Nicht mit anderen teilen

2. **Datenbank**: Das Tool schreibt direkt in die Produktiv-DB
   - Vor dem ersten Lauf: Backup erstellen
   - Dry-Run-Modus für Tests verwenden

---

## Troubleshooting

### Login schlägt fehl
- Credentials in `.env` prüfen
- Website im Browser testen (Login funktioniert?)
- Verbose-Modus für detaillierte Fehlermeldung

### Keine Daten werden synchronisiert
- Dry-Run-Modus deaktivieren (`--dry-run` entfernen)
- Log-Files im `logs/` Verzeichnis prüfen
- Website-Struktur geändert? (Parser anpassen)

### Parser-Fehler
- Cache-Files im `cache/` Verzeichnis prüfen (Roh-HTML)
- Mit Browser-DevTools vergleichen
- Parser-Modul anpassen

---

## Projektstruktur

```
webcrawler/
├── README.md           # Diese Datei
├── konzept.md          # Detailliertes Konzept & Architektur
├── main.py             # Entry Point (CLI)
├── config.py           # Konfiguration (URLs, Credentials, Pfade)
├── .env.example        # Template für Environment-Variablen
├── .gitignore          # Ausschluss von .env, cache/, logs/
│
├── scraper/            # Kern-Modul (HTTP & Parsing)
│   ├── fetcher.py      # HTTP-Fetching mit Login-Logik
│   └── parser.py       # Allgemeines HTML-Parsing
│
├── parsers/            # Kategorie-spezifische Parser
│   ├── gebaeude_parser.py
│   ├── rohstoffe_parser.py
│   ├── vorkommen_parser.py
│   ├── terrain_parser.py
│   ├── lebewesen_parser.py
│   ├── artikel_parser.py
│   ├── einheiten_parser.py
│   └── regierungen_parser.py
│
├── db/                 # Datenbank-Modul
│   ├── connection.py   # DB-Connection Helper
│   └── sync_engine.py  # INSERT/UPDATE/SKIP-Logik
│
├── cache/              # Rohdaten-Cache (HTML-Rohdaten)
└── logs/               # Log-Files (Protokolle)
```

---

## Beispiel-Ablauf

```bash
# 1. Alle Kategorien im Dry-Run testen
python main.py --dry-run --verbose

# 2. Nur Gebäude synchronisieren (echter Lauf)
python main.py --category gebaeude

# 3. Alle Kategorien synchronisieren (echter Lauf)
python main.py
```

---

**Version:** 1.0  
**Erstellt:** 2026-03-29  
**Status:** Implementiert (bereit zum Testen)
