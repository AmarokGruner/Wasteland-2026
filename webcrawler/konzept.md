# Webcrawler Konzept – Verbrannte Zone

## Zielsetzung

Ein Python-Skript, das Daten von **https://v3.verbranntezone.ch/** scraped und mit der lokalen `verbrannte_zone.db` synchronisiert.

---

## 1. Datenquellen & Mapping

### 1.1 Zu scrapende URLs

| Kategorie | Listen-URL | Detail-Muster | DB-Tabelle |
|-----------|------------|---------------|------------|
| Rohstoffe | `rohstofflist.php` | `rohstoffvorschau.php?id={id}` | `ressourcen` |
| Gebäude | `gebauedelist.php` | `gebaeudevorschau.php?id={id}` | `gebaeude_typen` |
| Vorkommen | `vorkommenlist.php` | `vorkommenvorschau.php?id={id}` | `vorkommen` |
| Terrains | `terrainlist.php` | `terrainvorschau.php?id={id}` | `terrain_typen` / `terrain_configs` |
| Lebewesen | `lebewesenlist.php` | `tiervorschau.php?id={id}` | `tier_vorlagen` / `AnimalTemplate` |
| Artikel | `artikellist.php` | `artikelvorschau.php?id={id}` | `artikel` |
| Einheiten | `einheitenlist.php` | `einheitenvorschau.php?id={id}` | `einheiten_typen` / `UnitType` |
| Regierungsformen | `regierungenlist.php` | `regierungvorschau.php?id={id}` | `regierungsformen` |

### 1.2 Datenbank-Mapping (Beispiel Gebäude)

```
Scraped-Felder → DB-Columns:
  "Name" → name (String)
  "Kategorie" → kategorie (String)
  "Bautyp" → bautyp (String)
  "Ausbaubar" → ausbaubar (Integer: 0/1)
  "Unique(einmalig)" → unique_gebaeude (Integer: 0/1)
  "Nur an Küste" → nur_kueste (Integer: 0/1)
  "ist Feld" → ist_feld (Integer: 0/1)
  "Benötigtes Techlevel" → tech_level (Integer)
  "Baukosten in Mips" → baukosten_mips (Integer)
  "Rohstoffbedarf Bau" → rohstoffbedarf_bau (JSON-String)
  "Energiebedarf" → spezial_eigenschaften (JSON)
  "Arbeiter" → arbeiter (Integer)
  "Wohnraum" → wohnraum (Integer)
  "Lagerraumkapazität" → lagerkapazitaet (Integer)
  "Effektivität bei Terrain:" → terrain_effektivitaet (JSON)
  "Rohstoffproduktion im Betrieb" → produktion (JSON-String)
  "Gebäudespezifische Eigenschaften:" → spezial_eigenschaften (JSON)
  "Beschreibung:" → beschreibung (String)
```

---

## 2. Technische Architektur

### 2.1 Benötigte Packages

```
requests==2.32.3        # HTTP-Requests
beautifulsoup4==4.12.3  # HTML-Parsing (bs4)
lxml==5.1.0             # Schneller Parser für BeautifulSoup
python-dotenv==1.0.1    # Environment-Variablen (.env)
```

### 2.2 Projektstruktur

```
webcrawler/
├── konzept.md              # Dieses Dokument
├── README.md               # Kurzanleitung
├── config.py               # Konfiguration (URLs, DB-Pfad, Timeout)
├── .env.example            # Template für Environment-Variablen
│
├── scraper/                # Hauptmodul
│   ├── __init__.py
│   ├── fetcher.py          # HTTP-Fetching mit Session-Handling
│   ├── parser.py           # HTML-Parsing (BeautifulSoup)
│   └── sync.py             # DB-Synchronisation
│
├── parsers/                # Kategorie-spezifische Parser
│   ├── __init__.py
│   ├── gebaeude_parser.py  # Gebäude-HTML → Dict
│   ├── rohstoffe_parser.py # Rohstoff-HTML → Dict
│   ├── vorkommen_parser.py # Vorkommen-HTML → Dict
│   ├── terrain_parser.py   # Terrain-HTML → Dict
│   ├── regierung_parser.py # Regierungsformen-HTML → Dict
│   ├── einheiten_parser.py # Einheiten-HTML → Dict
│   ├── tier_parser.py      # Tiere-HTML → Dict
│   └── artikel_parser.py   # Artikel-HTML → Dict
│
├── db/                     # Datenbank-Modul
│   ├── __init__.py
│   ├── connection.py       # DB-Connection Helper
│   └── sync_engine.py      # INSERT/UPDATE-Logik
│
├── cache/                  # Rohdaten-Cache (für Debugging)
│   └── .gitkeep
│
├── logs/                   # Log-Files
│   └── .gitkeep
│
└── main.py                 # Entry Point (CLI)
```

### 2.3 Datenfluss-Diagramm

```
┌─────────────────┐
│  config.py      │ ──→ Lädt URLs, Credentials, DB-Pfad
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  fetcher.py     │ ──→ HTTP-Request mit Login-Cookie
└────────┬────────┘
         │ (HTML-Rohdaten)
         ↓
┌─────────────────┐
│  parser.py      │ ──→ BeautifulSoup → strukturierte Dicts
└────────┬────────┘
         │ (Python-Dicts)
         ↓
┌─────────────────┐
│  sync_engine.py │ ──→ Vergleich mit DB (SELECT)
└────────┬────────┘
         │ (INSERT/UPDATE/SKIP Entscheidung)
         ↓
┌─────────────────┐
│  verbrannte_    │ ──→ Transaktionale DB-Updates
│  zone.db        │
└─────────────────┘
```

---

## 3. Implementierungs-Phasen

### Phase 1: Grundgerüst (MVP)
**Ziel:** Funktionierender Scraper für EINE Kategorie (Gebäude)

- [x] `config.py` erstellen
- [x] `.env.example` erstellen
- [ ] `scraper/fetcher.py` implementieren
- [ ] `scraper/parser.py` implementieren
- [ ] `parsers/gebaeude_parser.py` implementieren
- [ ] `db/sync_engine.py` implementieren
- [ ] `main.py` erstellen

### Phase 2: Parser-Erweiterung
**Ziel:** Alle 8 Kategorien unterstützen

- [ ] `parsers/rohstoffe_parser.py`
- [ ] `parsers/vorkommen_parser.py`
- [ ] `parsers/terrain_parser.py`
- [ ] `parsers/regierung_parser.py`
- [ ] `parsers/einheiten_parser.py`
- [ ] `parsers/tier_parser.py`
- [ ] `parsers/artikel_parser.py`

### Phase 3: Robustheit & Logging
**Ziel:** Produktionsreife

- [ ] Logging-System (log/ Verzeichnis)
- [ ] Retry-Mechanismus bei Fehlern
- [ ] Cache-System (cache/ Verzeichnis)

### Phase 4: CLI-Features
**Ziel:** Benutzerfreundliche Bedienung

- [ ] Dry-Run-Modus (`--dry-run`)
- [ ] Kategorie-Filter (`--category gebaeude,rohstoffe`)
- [ ] Verbose-Modus (`--verbose`)

---

## 4. Technische Details

### 4.1 Login-Flow

```python
# Standard HTML-Formular Login
POST /login.html (oder API-Endpoint)
  username: Dargoamarok
  password: katerfelix
  
# Response: Set-Cookie Header → Session-Cookie speichern
# Folge-Requests: Cookie im Session-Header mitsenden
```

### 4.2 HTML-Parsing-Strategie

**Empfehlung:** Kombination aus CSS-Selektoren und XPath

```python
# Beispiel Gebäude-Parser
from bs4 import BeautifulSoup

def parse_gebaeude(html: str) -> dict:
    soup = BeautifulSoup(html, 'lxml')
    
    # Titel extrahieren (z.B. <h1>Bunker</h1>)
    title = soup.find('h1').text.strip()
    
    # Tabelle mit Eigenschaften (typisches Muster)
    table = soup.find('table', {'class': 'details'})
    
    result = {}
    for row in table.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) >= 2:
            key = cells[0].text.strip()
            value = cells[1].text.strip()
            result[key] = value
    
    return result
```

### 4.3 Synchronisations-Logik

```python
def sync_record(db_session, table_name: str, data: dict, pk_field: str = 'id'):
    """
    Synchronisiert einen Datensatz.
    
    Args:
        db_session: SQLAlchemy Session
        table_name: Name der DB-Tabelle
        data: Dict mit gescrapten Daten
        pk_field: Primärschlüssel-Feld (default: 'id')
    
    Returns:
        dict: {'action': 'INSERT'|'UPDATE'|'SKIP', 'id': 123}
    """
    # 1. Existenz-Check
    existing = db_session.query(table_name).filter_by(id=data['id']).first()
    
    if not existing:
        # 2. INSERT (neuer Datensatz)
        new_record = table_name(**data)
        db_session.add(new_record)
        return {'action': 'INSERT', 'id': data['id']}
    
    # 3. UPDATE (wenn Änderungen)
    has_changes = False
    for key, value in data.items():
        if getattr(existing, key) != value:
            setattr(existing, key, value)
            has_changes = True
    
    if has_changes:
        return {'action': 'UPDATE', 'id': data['id']}
    
    # 4. SKIP (keine Änderungen)
    return {'action': 'SKIP', 'id': data['id']}
```

### 4.4 Rate-Limiting & Error-Handling

```python
import time
from requests.exceptions import RequestException, Timeout

def fetch_with_retry(session, url: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            response = session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except Timeout:
            log_warning(f"Timeout bei {url}, Retry {attempt + 1}/{max_retries}")
            time.sleep(2 ** attempt)  # Exponential Backoff
        except RequestException as e:
            log_error(f"HTTP-Fehler bei {url}: {e}")
            if attempt == max_retries - 1:
                raise
    return None
```

---

## 5. Risiken & Gegenmaßnahmen

| Risiko | Wahrscheinlichkeit | Auswirkung | Gegenmaßnahme |
|--------|-------------------|------------|---------------|
| JavaScript-basiertes Login | Mittel | Hoch (Scraper funktioniert nicht) | Fallback auf Selenium/Playwright |
| HTML-Struktur ändert sich | Mittel | Mittel (Parser brechen) | Robuste Selektoren, Fallback-Werte |
| Session-Timeout | Hoch | Niedrig (einfach zu handlen) | Re-Login bei Session-Verlust |
| Rate-Limiting/Blocking | Mittel | Mittel (429 Errors) | Delays zwischen Requests (1-2 Sek.) |
| CSRF-Protection | Mittel | Hoch (Login ohne Token unmöglich) | Token aus Login-Form extrahieren |

---

## 6. Erfolgskriterien

- ✅ Scraper loggt sich erfolgreich ein (Session-Cookie erhalten)
- ✅ HTML-Seiten werden korrekt geparst (alle relevanten Felder extrahiert)
- ✅ DB-Sync erkennt neue Datensätze (INSERT)
- ✅ DB-Sync erkennt Änderungen (UPDATE)
- ✅ DB-Sync ignoriert unveränderte Datensätze (SKIP)
- ✅ Logging funktioniert (Erfolg/Fehler protokolliert)
- ✅ Dry-Run-Modus zeigt geplante Änderungen

---

**Erstellt:** 2026-03-29  
**Status:** Implementierungsphase  
**Version:** 1.0
