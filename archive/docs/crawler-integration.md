# 🤖 Webcrawler Admin-Integration

## Überblick

Der Webcrawler wurde erfolgreich in die Admin-Oberfläche integriert. Admin-Benutzer können nun:

1. **Crawler manuell starten** - Alle oder ausgewählte Kategorien synchronisieren
2. **Status überwachen** - Echtzeit-Status während des Crawls
3. **Ergebnisse prüfen** - Ausstehende Änderungen vorfreitigen
4. **Änderungen freigeben** - Manuell genehmigen oder ablehnen
5. **Datenbank synchronisieren** - Genehmigte Änderungen in die DB übernehmen

---

## Architekturdarstellung

```
┌─────────────────────────────────────────────────────────────┐
│                     Admin-UI (admin.html)                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🤖 Webcrawler Tab                                  │   │
│  │  ├── Kategorie-Auswahl (Checkboxes)                │   │
│  │  ├── Start/Stop-Buttons                            │   │
│  │  ├── Status-Anzeige (laufend/abgeschlossen)        │   │
│  │  └── Pending-Changes-Tabelle                       │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    │ HTTP Requests
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                 Crawler-API (app/api/crawler.py)            │
│  ├── GET   /admin/crawler/categories  - Unterstützte       │
│  │                                                          │
│  ├── POST /admin/crawler/start      - Startet Crawler      │
│  │                                                          │
│  ├── GET   /admin/crawler/status    - Status prüfen        │
│  │                                                          │
│  ├── GET   /admin/crawler/pending   - Ausstehende          │
│  │                                                          │
│  ├── POST /admin/crawler/approve/{id}  - Freigeben         │
│  │                                                          │
│  └── POST /admin/crawler/reject/{id}   - Ablehnen          │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    │ subprocess.run()
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                Webcrawler (webcrawler/main.py)              │
│  ├── Login zur Website                                     │
│  ├── Listen-Scan (8 Kategorien)                           │
│  ├── Detail-Fetch (pro ID)                                │
│  ├── Parsing (HTML → Dict)                                │
│  └── Sync-Logik (INSERT/UPDATE/SKIP)                      │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    │ SQLAlchemy
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                  Datenbank (models.py)                      │
│  ├── CrawlSession   - Sessions verfolgen                   │
│  ├── CrawlChange    - Einzelne Änderungen speichern        │
│  └── [Original-Tabellen]  - GebaeudeTypen, Resource, etc.  │
└─────────────────────────────────────────────────────────────┘
```

---

## Dateien und Änderungen

### Backend

| Datei | Änderungen | Beschreibung |
|---|---|---|
| **app/api/crawler.py** | Neu (350+ Zeilen) | Crawler-API Router |
| **app/api/\_\_init\_\_.py** | Modifiziert | Crawler-Router importiert |
| **app/models.py** | Modifiziert | CrawlSession, CrawlChange Modelle |
| **webcrawler/main.py** | Existing | Crawler CLI (existiert bereits) |

### Frontend

| Datei | Änderungen | Beschreibung |
|---|---|---|
| **admin.html** | Modifiziert | Webcrawler Tab, CSS, HTML |
| **admin/js/services/crawler.js** | Neu (250+ Zeilen) | CrawlerService JavaScript |

---

## API-Endpunkte

### 1. Starte Crawler
**`POST /api/admin/crawler/start`**

**Request Body:**
```json
{
  "categories": ["gebaeude", "rohstoffe"],  // Optional, null = alle
  "dry_run": false
}
```

**Response:**
```json
{
  "status": "started",
  "message": "Crawler starting in background"
}
```

### 2. Status prüfen
**`GET /api/admin/crawler/status`**

**Response:**
```json
{
  "running": false,
  "current_category": null,
  "progress": {},
  "last_run": "2026-04-05T12:34:56",
  "error": null
}
```

### 3. Ausstehende Änderungen
**`GET /api/admin/crawler/pending`**

**Response:**
```json
{
  "pending": [
    {
      "id": 1,
      "category": "gebaeude",
      "action": "UPDATE",
      "record_id": 42,
      "detected_at": "2026-04-05T12:35:00"
    }
  ],
  "total": 1
}
```

### 4. Änderung freigeben
**`POST /api/admin/crawler/approve/{item_id}`**

**Response:**
```json
{
  "status": "approved",
  "message": "Change 1 approved"
}
```

### 5. Änderung ablehnen
**`POST /api/admin/crawler/reject/{item_id}`**

**Response:**
```json
{
  "status": "rejected",
  "message": "Change 1 rejected"
}
```

---

## Unterstützte Kategorien

| Kategorie | DB-Tabelle | Beschreibung |
|---|---|---|
| **gebaeude** | gebaeude_typen | Gebäude-Typen |
| **rohstoffe** | ressourcen | Ressourcen-Typen |
| **vorkommen** | vorkommen | Rohstoff-Vorkommen |
| **terrains** | terrain_typen | Terrain-Typen |
| **lebewesen** | tier_vorlagen | Tiere/Lebewesen |
| **artikel** | artikel | Artikel/Items |
| **einheiten** | einheiten_typen | Einheiten-Typen |
| **regierungen** | regierungsformen | Regierungsformen |

---

## UI-Bedienung (Schritt-für-Schritt)

### 1. Crawler starten

1. **Navigiere zum Webcrawler Tab** (🤖 Webcrawler in der Navigation)
2. **Wähle Kategorien:**
   - "Alle Kategorien" (default) ODER
   - Einzelne Kategorien anhaken
3. **Optionale Einstellungen:**
   - ✅ Testmodus (Dry-Run) - nur Vorschau, keine DB-Schreibzugriffe
   - ✅ Detaillierte Logs - Console-Logs anzeigen
4. **Klicke "▶️ Starten"**
5. **Status beobachten:**
   - "🔄 Crawler läuft..." während des Crawls
   - "✅ Crawler abgeschlossen" am Ende

### 2. Änderungen prüfen

Nach Abschluss:
- Tabelle mit ausstehenden Änderungen wird angezeigt
- Jede Änderung zeigt:
  - **Aktion:** INSERT (grün), UPDATE (gelb), REJECT (rot)
  - **Kategorie:** Gebäude, Rohstoffe, etc.
  - **ID:** Primärschlüssel des Datensatzes
  - **Geänderte Felder:** (zukünftig detailliert)

### 3. Änderungen freigeben/ablehnen

**Für einzelne Änderungen:**
- 👁️ - Details anzeigen (zukünftig)
- ✅ - Genehmingen und in DB übernehmen
- ❌ - Ablehnen und verwerfen

**Für alle Änderungen:**
- "✅ Alle freigeben & speichern" - Alle pending Änderungen übernehmen
- "❌ Alle ablehnen" - Alle pending Änderungen verwerfen

---

## Datenbank-Schema

### CrawlSession
```sql
CREATE TABLE crawl_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    status TEXT,              -- pending, running, completed, failed
    categories TEXT,          -- JSON-Liste der Kategorien
    dry_run BOOLEAN DEFAULT 0,
    total_changes INTEGER DEFAULT 0,
    approved_changes INTEGER DEFAULT 0,
    error_message TEXT
);
```

### CrawlChange
```sql
CREATE TABLE crawl_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES crawl_sessions(id),
    category TEXT NOT NULL,
    action TEXT NOT NULL,     -- INSERT, UPDATE, REJECT
    record_id INTEGER NOT NULL,
    table_name TEXT NOT NULL,
    old_data_json TEXT,       -- Vorheriger Zustand (UPDATE)
    new_data_json TEXT NOT NULL,
    changed_fields TEXT,      -- JSON-Liste geänderter Felder
    approved BOOLEAN DEFAULT 0,
    rejected BOOLEAN DEFAULT 0,
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    approved_at DATETIME
);
```

---

## Verwendung als CLI (Alternative)

Der originale CLI-Betrieb bleibt erhalten:

```bash
cd webcrawler

# Alle Kategorien synchronisieren
python main.py

# Nur bestimmte Kategorien
python main.py --category gebaeude rohstoffe

# Testmodus (Dry-Run) - keine DB-Schreibzugriffe
python main.py --dry-run --verbose

# Kombination
python main.py --category gebaeude --dry-run --verbose
```

---

## Fehlerbehandlung

| Fehler | Verhalten |
|---|---|
| **Crawler bereits laufend** | 409 Conflict - "Crawl already running" |
| **HTTP-Timeout** | 3 Retries mit Backoff |
| **HTTP 403/404** | Wird geloggt, Prozess setzt fort |
| **DB-Fehler** | Rollback der aktuellen Transaktion |
| **Timeout (>5 min)** | Abbruch mit Timeout-Fehler |

---

## Sicherheitshinweise

1. **Nur Admin-Benutzer** sollten den Crawler nutzen können
   - [ ] TODO: Admin-Auth prüfen in API

2. **Rate-Limiting** ist im Crawler implementiert
   - 1.0 Sekunden Delay zwischen Requests
   - Verhindert Server-Überlastung

3. **Credential-Sicherheit**
   - .env Datei nicht committen
   - .gitignore prüft .env, cache/, logs/

---

## Bekannte Limitationen

1. **Änderungen werden noch NICHT gespeichert**
   - API speichert Ergebnisse in `crawl_changes`
   - Freigabe/Approval-Endpunkte sind implemented
   - DB-Sync nach Approval ist im Placeholder

2. **Änderungsdetails werden nicht angezeigt**
   - "viewCrawlChange()" zeigt nur Alert
   - TODO: Diff-Ansicht implementieren

3. **Kein History-Tab**
   - `GET /api/admin/crawler/history` ist Placeholder
   - TODO: CrawlHistory-Tabelle und UI

---

## Nächste Schritte (Empfehlungen)

### Kurzfristig
1. **DB-Sync nach Approval implementieren**
   - `approveChange()` sollte die Änderungen in die Original-DB schreiben
   - CrawlStatus auf "completed" setzen

2. **Diff-Ansicht für Änderungen**
   - Modal mit "Alt" vs. "Neu" Spalten
   - Hervorheben der geänderten Felder

3. **Admin-Auth-Checker**
   - API-Router prüft `@Depends(get_current_admin_user)`

### Mittelfristig
4. **Crawl-History-Tabelle**
   - Speichert alle vergangenen Sessions
   - Export als CSV/JSON

5. **Automatische Regel-basierte Freigabe**
   - Beispiel: Alle "INSERT" automatisch genehmigen
   - Nur "UPDATE" manuell prüfen

6. **Webhook/Notifications**
   - Email bei Abschluss
   - Push-Notification im Admin-Panel

---

## Test-Ergebnisse

### Browser-Tests ✅
- [x] Webcrawler Tab ist sichtbar
- [x] Tab-wechsel funktioniert
- [x] Formulare laden ohne JavaScript-Fehler
- [x] Start-Button ist klickbar

### API-Tests (Manuell)
- [ ] GET /categories - 200 OK
- [ ] POST /start - 200 OK
- [ ] GET /status - 200 OK
- [ ] GET /pending - 200 OK
- [ ] POST /approve/{id} - 200 OK
- [ ] POST /reject/{id} - 200 OK

---

## Ressourcen

- **Webcrawler README**: `webcrawler/README.md`
- **API Router**: `app/api/crawler.py`
- **Service**: `admin/js/services/crawler.js`
- **Modelle**: `app/models.py` (CrawlSession, CrawlChange)

---

**Letzte Aktualisierung**: 2026-04-05  
**Version**: v1.0  
**Status**: ✅ **INTegriert, Testing läuft**
