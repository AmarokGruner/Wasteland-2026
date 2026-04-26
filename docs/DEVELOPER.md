# Verbrannte Zone - Entwickler Setup

## Einrichtung

### 1. Dependencies installieren

```bash
pip install fastapi uvicorn sqlalchemy python-jose[ecdsa] bcrypt
```

### 2. Umgebung konfigurieren

```bash
# app/config.py - SECRET_KEY MUREN GEDREHT WERDEN!
# In Entwicklung kann dies bleiben, in Produktion AENDERN!
```

### 3. Datenbank initialisieren

```bash
# SQLite wird automatisch beim ersten Start erstellt
# Migrationsscripts manuell anwenden:
sqlite3 verbrannte_zone.db < migrations/001_crawler_tables.sql
```

### 4. Server starten

```bash
python main.py
# Server läuft unter: http://localhost:8011
```

## Testen

```bash
# Alle Tests ausfuehren
python -m pytest tests/

# Spezifischen Test
python -m pytest tests/test_fetcher.py -v
```

## Git Workflow

### Commit Nachrichten

```
feat: New feature hinzugefuegt
fix: Bug behoben
docs: Dokumentation aktualisiert
refactor: Code refactored (keine Funktionsaenderungen)
test: Tests hinzugefuegt
chore: Maintenance (CI, dependencies)
```

### Branch Strategy

```
main            # Produktions-Code
develop         # Entwicklung
feature/x       # Neue Features
bugfix/x        # Bugfixes
hotfix/x        # Kritische Fixes
```

## Dokumentation

### Beim Code aendern:

1. **API aendert sich?** → MANUAL.md aktualisieren
2. **Systemdesign aendert sich?** → ARCHITECTURE.md aktualisieren
3. **Neuer Block noetig?** → context/blocks/*.yaml erstellen
4. **Fehler aufgetreten?** → FAIL_LOG.md dokumentieren
5. **Feature fertig?** → CHANGELOG.md eintragen

### Block erstellen (Agent Onboarding)

```yaml
# context/blocks/b-neues-feature.yaml
id: "b-neues-feature"
type: "overview|api|code"
domain: "backend|frontend|data"
title: "Kurzbeschreibung"
summary: "<100 tokens"
details: |
  Detaillierte Beschreibung
sources: ["datei.py:zeile"]
related_blocks: ["b-bestehendes"]
tokens_estimate: 200
created_at: "2026-04-05T00:00:00Z"
updated_at: "2026-04-05T00:00:00Z"
status: "active"
```

## Debugging

### Logs einsehen

```bash
tail -f app.log
```

### DB inspizieren

```bash
sqlite3 verbrannte_zone.db
sqlite> SELECT * FROM crawl_sessions;
sqlite> .schema crawl_changes
```

### API testen

```bash
# Mit curl
curl -X POST http://localhost:8011/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
```

## Wichtige Dateien

| Datei | Zweck |
|---|---|
| app/main.py | App Entry Point, Scheduler |
| app/config.py | Konfiguration, SECRET_KEY |
| app/models.py | DB Models |
| app/api/crawler.py | Crawler-API |
| admin.html | Admin-UI Frontend |
| context/index.yaml | Agent Block-Index |

## Hilfe

- **Bug?** → FAIL_LOG.md lesen
- **Funktionalitaet unklar?** → MANUAL.md lesen
- **Architektur unklar?** → ARCHITECTURE.md lesen
- **Agent-Workflow?** → AGENTS.md lesen

---

**Version:** 3.5 | **Update:** 2026-04-05
