# Changelog - Verbrannte Zone Admin

## [Unreleased]

### Added (Webcrawler-Integration)
- ✅ Crawler-API Router mit 12 Endpunkten
- ✅ DB-Modelle: CrawlSession, CrawlChange
- ✅ Admin-UI: Crawler-Tab mit Modal-Diff-Ansicht
- ✅ Export-Funktionen: CSV & JSON
- ✅ Kategorie-Filter in Pending-Changes
- ✅ Migration: crawl_sessions, crawl_changes

### Changed
- Modularisierte Admin-UI (11 Module)
- get_db() von app.database nach app.models ausgelagert

### Fixed
- Import-Fehler: get_db in models.py verfügbar
- SQLite CREATE INDEX Syntax (separate Statements)

## [3.5.0] - 2026-04-05

### Added
- Webcrawler-Integration vollständig
- Export-Funktionen CSV/JSON
- Kategorie-Filter im Admin-UI
- Diff-Modal für Änderungen

### Security
- ⚠️ SECRET_KEY muss in Produktion geändert werden!

## [3.4.0] - 2026-03-20

### Added
- 4-Konten-System (Finanzen)
- Handelsrouten-Logik
- Handelskarren (20-25 Jahre)

## [3.3.0] - 2026-03-10

### Added
- Building System v3 (15x15 Grid)
- Progressive Grid-Expansion (Level 1-8)
- Building- und Demolish-Logik

## [3.2.0] - 2026-03-05

### Added
- Kolonisationssystem (Siedler)
- Provincia-Transfer-Logik
- Gamelog-System
- Direktnachrichten (Posteingang/Ausgang)

## [3.1.0] - 2026-02-28

### Added
- Auth-System (JWT)
- Admin-Panel
- Admin-Endpoints

## [3.0.0] - 2026-02-15

### Major
- Module-Neustrukturierung von app/
- API Router-Refactoring
- FastAPI Migration

---

**KI-Agent Hinweis:** Bei Änderungen immer CHANGELOG.md aktualisieren in der [Unreleased]-Sektion!
