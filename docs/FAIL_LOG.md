# Fail Log - Verbrannte Zone Admin

> Fehler-Dokumentation: Vermeidung wiederholter Fehler

## 2026-04-05 - SQL CREATE INDEX Syntax

**Problem:** `CREATE TABLE ... INDEX idx...` nicht in SQLite möglich  
**Fehlermeldung:** `near "INDEX": syntax error`  
**Root Cause:** SQLite unterstützt keine Inline-Index-Definitionen  

**Lösung:**
```sql
-- FALSCH:
CREATE TABLE t1 (
  id INTEGER PRIMARY KEY,
  INDEX idx_id (id)  -- ❌
);

-- RICHTIG:
CREATE TABLE t1 (id INTEGER PRIMARY KEY);
CREATE INDEX idx_id ON t1(id);  -- ✅
```

**Prevention:** Immer separate `CREATE INDEX` Statements verwenden

---

## 2026-04-05 - Import-Fehler: get_db nicht gefunden

**Problem:** `ImportError: cannot import name 'get_db' from 'app.database'`  
**Root Cause:** `get_db()` war in app/models.py definiert, nicht in app/database.py  

**Lösung:**
1. Import in crawler.py korrigieren: `from app.models import get_db`
2. get_db() in models.py für andere Module verfügbar halten

**Prevention:**
- In DEVELOPER.md dokumentieren, wo get_db definiert ist
- Bei Refactoring Importe überall aktualisieren

---

## 2026-04-04 - Migration nicht angewendet

**Problem:** Migration-Script war noch in migrations/ vorhanden  
**Entscheidung:** Migrationen direkt ausführen, Script kann gelöscht werden  

**Lösung:** migrations/001_crawler_tables.sql nach erfolgreicher Ausführung löschen

**Prevention:** Migrationsscripts nach Anwendung archivieren oder löschen

---

## 过去 - Import-Fehler bei Crawler-Modellen

**Problem:** `CrawlSession, CrawlChange` nicht in models.py importierbar  
**Root Cause:** Modelle in models.py definiert, aber nicht am Ende  

**Lösung:** Modell-Klassen ganz am Ende von models.py hinzufügen, nach allen anderen Imports

**Prevention:** Neue Models immer in models.py am Ende hinzufügen

---

**KI-Agent Hinweise:**
- Bei ähnlichen Fehlern zuerst FAIL_LOG.md durchsuchen
- Lösungen dokumentieren, wenn neu entdeckt
- Prevention-Maßnahmen umsetzen
