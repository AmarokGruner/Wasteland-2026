# Feature: Inaktivitäts-Cleanup & Ruinen-System

## Ziel
Die Weltkarte wird irgendwann voll. Spieler, die sich anmelden und nie wiederkommen, blockieren Startgebiete. Sie müssen systematisch aufgeräumt werden.

## 1. Schwellenwerte (Admin-Config oder Konstanten)
- `WARNING_DAYS` = 14 Tage (E-Mail / Notification)
- `RUIN_DAYS` = 21 Tage (Provinzen werden zu Ruinen)
- `DELETE_DAYS` = 30 Tage (Account wird gelöscht)

## 2. Der Cleanup-Cronjob (Täglich nachts)
- **Phase 1 (Warnung):** Suche User mit `last_login < (NOW - 14 days)` und `cleanup_warned == False`. Setze Flag, sende Gamelog/Systemnachricht.
- **Phase 2 (Verfall):** Suche User mit `last_login < (NOW - 21 days)`.
  - Iteriere über alle Provinzen des Users.
  - Setze `world_map_cells.is_ruin_province = True`.
  - Setze `owner_id = NULL`.
  - Reduziere alle Gebäude-Level um 50%.
  - Lagerbestand bleibt erhalten (als Loot für Plünderer).
- **Phase 3 (Löschung):** Suche User mit `last_login < (NOW - 30 days)`. Lösche User-Datensatz (Cascading Deletes für Nachrichten, Handel, etc.).

## 3. UI-Feedback
- Weltkarte: Ruinen-Provinzen haben ein spezielles Overlay (z.B. grauer Schleier oder Totenkopf-Icon auf der Zelle).
- Tooltip auf der Weltkarte zeigt "Ruine (Ehemals Spieler XYZ)".
- Andere Spieler können auf Ruinen eine "Expedition" oder "Plünderung" starten (greift in Siedler-Mechanik ein).
