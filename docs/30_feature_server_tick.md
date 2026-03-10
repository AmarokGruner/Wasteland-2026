# Feature: Server-Tick Engine (Cronjob)

## Ziel
Die Produktion, Nahrungsaufnahme und Alterung (Rundenmechanik) darf nicht nur getriggert werden, wenn ein Spieler klickt, sondern muss verlässlich und automatisiert auf dem Server laufen.

## 1. Architektur (Scheduler)
- Integration eines Background-Task-Schedulers im Backend (z.B. `APScheduler` in FastAPI oder als separater Python-Worker-Prozess).
- **Intervall:** Läuft alle X Minuten (z.B. jede Stunde für einen "Game-Tick").
- **Locking-Mechanismus:** DB-Tabelle `system_locks` (Tabelle mit `task_name`, `is_running`, `last_run`). Verhindert, dass zwei Ticks gleichzeitig laufen, falls ein Tick länger dauert als das Intervall.

## 2. Der Tick-Algorithmus (Chunking)
Da bei 1.000+ Provinzen ein RAM-Limit auftreten kann:
1. Hole alle aktiven Provinzen aus der DB in 100er-Chunks (Pagination/Limit-Offset).
2. Für jede Provinz:
   - Berechne Produktion (Gebäude-Effizienz * Arbeiter).
   - Berechne Verbrauch (Nahrung/Wasser für Bevölkerung).
   - Berechne Moral-Updates.
3. Update die Lagerbestände in der DB (idealerweise Bulk-Updates `UPDATE lager SET menge = ... WHERE id IN (...)`).
4. Erstelle Gamelog-Einträge für Events (Verhungern, Revolten).

## 3. Fehlerbehandlung (Resilience)
- Wenn die Berechnung für eine Provinz fehlschlägt (z.B. Division by Zero), fange die Exception (`try/except`), logge sie, und setze mit der nächsten Provinz fort. Der gesamte Tick darf nicht crashen!
- Nach Abschluss: Speichere Tick-Dauer und betroffene Provinzen in einer `tick_logs` Tabelle für den Admin zur Performance-Überwachung.

## 4. Admin-Interface
- Neuer Tab in der Admin-UI: "Tick-Engine".
- Zeigt: Letzter Tick (Zeitstempel), Dauer (ms), Status (Running/Idle), Button "Manuellen Tick erzwingen".
