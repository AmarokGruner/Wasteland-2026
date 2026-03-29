# Unit Tests für Webcrawler

## Test-Strategie

### Test-Kategorien

1. **Fetcher Tests** (`tests/test_fetcher.py`)
   - Login-Funktionalität
   - HTTP-Requests mit Retry-Logik
   - Session-Handling

2. **Parser Tests** (`tests/test_parsers.py`)
   - HTML-Parsing für jede Kategorie
   - Edge Cases (fehlende Felder, spezielle Zeichen)

3. **Sync Engine Tests** (`tests/test_sync_engine.py`)
   - INSERT-Logik (neue Datensätze)
   - UPDATE-Logik (geänderte Datensätze)
   - SKIP-Logik (unveränderte Datensätze)

4. **Integration Tests** (`tests/test_integration.py`)
   - End-to-End Test mit Mock-Datenbank
   - Kompletter Scraping-Durchlauf

---

## Test-Setup

### Benötigte Test-Dependencies

```
pytest==8.0.0           # Test-Framework
pytest-cov==4.1.0       # Code-Coverage
responses==0.25.0       # HTTP-Mocking (für Fetcher-Tests)
```

### Test-Fixtures

- Mock-HTML-Fixtures (lokale HTML-Dateien)
- Mock-Datenbank (In-Memory SQLite)
- Mock-HTTP-Responses (via responses-Bibliothek)

---

## Test-Fälle im Detail

### 1. Fetcher Tests (`test_fetcher.py`)

```python
# Test-Fälle:
- test_login_success: Login mit gültigen Credentials
- test_login_failure: Login mit ungültigen Credentials
- test_fetch_page_success: Erfolgreicher HTTP-Request
- test_fetch_page_retry: Retry-Logik bei Timeout
- test_fetch_page_404: Handling von 404-Fehlern
- test_session_cookie_persistence: Session-Cookies werden gespeichert
```

### 2. Parser Tests (`test_parsers.py`)

```python
# Test-Fälle pro Kategorie (gebaeude, rohstoffe, etc.):
- test_parse_detail_page: Normale Detail-Seite
- test_parse_missing_fields: Seite mit fehlenden Feldern
- test_parse_special_characters: Seite mit speziellen Zeichen (UTF-8)
- test_parse_empty_table: Leere Tabelle
- test_parse_list_page: List-Seite mit mehreren Einträgen
```

### 3. Sync Engine Tests (`test_sync_engine.py`)

```python
# Test-Fälle:
- test_sync_insert_new_record: Neuer Datensatz → INSERT
- test_sync_update_changed_record: Geänderter Datensatz → UPDATE
- test_sync_skip_unchanged_record: Unveränderter Datensatz → SKIP
- test_sync_invalid_data: Ungültige Daten → Fehlerbehandlung
- test_sync_commit: Transaktion wird korrekt committed
- test_sync_rollback: Rollback bei Fehler
```

### 4. Integration Tests (`test_integration.py`)

```python
# Test-Fälle:
- test_full_scrape_cycle: Kompletter Durchlauf mit Mock-Daten
- test_dry_run_mode: Dry-Run schreibt nicht in DB
- test_category_filter: Nur bestimmte Kategorien werden gescraped
```

---

## Test-Daten (Fixtures)

### Mock-HTML-Fixtures

Erstelle lokale HTML-Dateien für Tests:

```
tests/fixtures/
├── html/
│   ├── gebaeude_detail_1.html      # Bunker-Detail-Seite
│   ├── gebaeude_list.html          # Gebäude-Liste
│   ├── rohstoffe_detail_1.html     # Wasser-Detail-Seite
│   ├── rohstoffe_list.html         # Rohstoff-Liste
│   └── ... (für jede Kategorie)
├── db/
│   ├── empty.db                    # Leere Datenbank
│   └── populated.db                # Datenbank mit Test-Daten
└── responses/
    ├── mock_login_success.json     # Mock-Login-Response
    └── mock_list_response.json     # Mock-List-Response
```

### Mock-Datenbank-Schema

Für Tests wird eine In-Memory SQLite-Datenbank verwendet:

```python
# tests/conftest.py
@pytest.fixture
def test_db():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
```

---

## Test-Ausführung

### Alle Tests ausführen

```bash
pytest tests/ -v
```

### Nur bestimmte Test-Kategorie

```bash
pytest tests/test_fetcher.py -v           # Nur Fetcher-Tests
pytest tests/test_parsers.py -v           # Nur Parser-Tests
pytest tests/test_sync_engine.py -v       # Nur Sync-Engine-Tests
```

### Mit Code-Coverage

```bash
pytest tests/ --cov=webcrawler --cov-report=html
```

### Nur fehlgeschlagene Tests wiederholen

```bash
pytest tests/ --lf
```

---

## Test-Plan (Phasen)

### Phase 1: Test-Infrastruktur
- [x] pytest als Dependency definieren
- [ ] `tests/conftest.py` erstellen (Fixtures)
- [ ] Test-Fixtures vorbereiten (HTML, DB)

### Phase 2: Fetcher Tests
- [ ] `tests/test_fetcher.py` erstellen
- [ ] Mock-HTTP-Responses einrichten (responses-Bibliothek)
- [ ] Login-Tests implementieren
- [ ] HTTP-Request-Tests implementieren

### Phase 3: Parser Tests
- [ ] `tests/test_parsers.py` erstellen
- [ ] HTML-Fixtures für alle Kategorien erstellen
- [ ] Parser-Tests für jede Kategorie

### Phase 4: Sync Engine Tests
- [ ] `tests/test_sync_engine.py` erstellen
- [ ] INSERT/UPDATE/SKIP-Tests
- [ ] Transaktions-Tests (Commit/Rollback)

### Phase 5: Integration Tests
- [ ] `tests/test_integration.py` erstellen
- [ ] End-to-End-Tests mit Mock-Datenbank

---

## Erfolgskriterien

- ✅ Alle Tests bestehen (100% pass rate)
- ✅ Code-Coverage > 80%
- ✅ Tests sind deterministisch (kein Flakiness)
- ✅ Tests sind schnell (< 30 Sekunden für alle Tests)

---

**Erstellt:** 2026-03-29  
**Status:** Planungsphase – wartet auf Installation der Test-Dependencies
