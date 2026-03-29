# Webcrawler Tests

## Test-Struktur

```
tests/
├── conftest.py           # Pytest-Fixtures (shared test data)
├── pytest.ini            # Pytest-Konfiguration
├── TEST_PLAN.md          # Detaillierter Test-Plan
│
├── test_fetcher.py       # Tests für HTTP-Fetching & Login
├── test_parsers.py       # Tests für HTML-Parsing
├── test_sync_engine.py   # Tests für DB-Synchronisation
└── test_integration.py   # Integrationstests (End-to-End)
```

---

## Installation der Test-Dependencies

Bevor die Tests ausgeführt werden können, müssen folgende Pakete installiert werden:

```bash
pip install pytest pytest-cov responses
```

**Hinweis:** Die Installation erfordert eine Internetverbindung zu pypi.org.

---

## Test-Ausführung

### Alle Tests ausführen

```bash
cd webcrawler
pytest tests/ -v
```

### Nur bestimmte Test-Datei

```bash
pytest tests/test_fetcher.py -v       # Nur Fetcher-Tests
pytest tests/test_parsers.py -v       # Nur Parser-Tests
pytest tests/test_sync_engine.py -v   # Nur Sync-Engine-Tests
```

### Nur Unit-Tests (ohne Integration)

```bash
pytest tests/ -v -m "not integration"
```

### Mit Code-Coverage-Report

```bash
pytest tests/ --cov=webcrawler --cov-report=html
```

Der Coverage-Report wird im `htmlcov/` Verzeichnis erstellt.

### Nur fehlgeschlagene Tests wiederholen

```bash
pytest tests/ --lf
```

---

## Test-Kategorien

### 1. Fetcher Tests (`test_fetcher.py`)

| Test | Zweck | Status |
|------|-------|--------|
| `test_create_session` | Session-Instanz erstellen | ✅ Lokal (kein Netzwerk) |
| `test_login_success` | Erfolgreicher Login | ⚠️ Benötigt HTTP-Verbindung |
| `test_fetch_page_success` | Seite laden | ⚠️ Benötigt HTTP-Verbindung |

### 2. Parser Tests (`test_parsers.py`)

| Test | Zweck | Status |
|------|-------|--------|
| `test_create_parser` | Parser-Instanz erstellen | ✅ Lokal |
| `test_extract_title_from_h1` | Titel aus HTML extrahieren | ✅ Lokal (mit Fixture) |
| `test_extract_table_data` | Tabellendaten extrahieren | ✅ Lokal (mit Fixture) |
| `test_parse_gebaeude_basic` | Gebäude-Seite parsen | ✅ Lokal (mit Fixture) |

### 3. Sync Engine Tests (`test_sync_engine.py`)

| Test | Zweck | Status |
|------|-------|--------|
| `test_sync_insert_new_record` | INSERT-Logik | ✅ Lokal (In-Memory DB) |
| `test_sync_update_changed_record` | UPDATE-Logik | ✅ Lokal (In-Memory DB) |
| `test_sync_skip_unchanged_record` | SKIP-Logik | ✅ Lokal (In-Memory DB) |
| `test_commit_transaction` | Transaktion commiten | ✅ Lokal (In-Memory DB) |

### 4. Integration Tests (`test_integration.py`)

| Test | Zweck | Status |
|------|-------|--------|
| `test_full_scrape_cycle` | Kompletter Scraping-Durchlauf | ⚠️ Benötigt HTTP-Verbindung |
| `test_dry_run_mode` | Dry-Run ohne DB-Schreiben | ⚠️ Benötigt HTTP-Verbindung |

---

## Test-Fixtures

Die Tests verwenden Pytest-Fixtures aus `conftest.py`:

- `sample_gebaeude_html` – Beispiel HTML für Gebäude-Seite
- `sample_rohstoffe_html` – Beispiel HTML für Rohstoff-Seite
- `sample_list_html` – Beispiel HTML für Listen-Seite
- `db_session` – In-Memory SQLite-Datenbank für Tests

---

## Mocking von HTTP-Requests

Für Tests ohne Netzwerk-Abhängigkeit wird die `responses`-Bibliothek verwendet:

```python
import responses

@responses.activate
def test_fetch_with_mock():
    # Mock HTTP response
    responses.add(
        responses.GET,
        "https://example.com/page.html",
        body="<html><body>Test</body></html>",
        status=200
    )
    
    # Test code that makes HTTP request
    session = WebScraperSession(...)
    html = session.fetch("https://example.com/page.html")
    
    assert html == "<html><body>Test</body></html>"
```

---

## Erfolgskriterien

- ✅ Alle Tests bestehen (100% pass rate)
- ✅ Code-Coverage > 80%
- ✅ Tests sind deterministisch (kein Flakiness)
- ✅ Tests sind schnell (< 30 Sekunden für alle Tests)

---

## Troubleshooting

### Tests schlagen fehl wegen Netzwerk

Die mit `@pytest.mark.skip` oder `pytest.skip()` markierten Tests benötigen eine HTTP-Verbindung. Diese werden automatisch übersprungen, wenn kein Netzwerk verfügbar ist.

### Coverage zu niedrig

Füge weitere Test-Fälle hinzu oder erhöhe die Test-Abdeckung der bestehenden Tests.

### Tests sind zu langsam

Identifiziere langsame Tests mit `pytest --durations=10` und optimiere diese.

---

**Erstellt:** 2026-03-29  
**Status:** Test-Struktur erstellt – wartet auf Installation von pytest
