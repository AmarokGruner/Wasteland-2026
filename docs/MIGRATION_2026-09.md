# Datenbank-Migration 2026-09

**Datum:** 2026-09-01  
**Skript:** `scripts/db_migration.py`  
**Datenbank:** `verbrannte_zone.db`

## Problemstellung

SQLAlchemy Model-Definitionen in `app/models.py` wichen von der tatsächlichen
SQLite-Datenbank ab. Fehlende Spalten führten zu `no such column`-Fehlern
im Game-Tick und bei API-Anfragen.

## Durchgeführte Migrationen

### Neue Spalten hinzugefügt (16 insgesamt)

| Tabelle | Spalte | Typ | Grund |
|---------|--------|-----|-------|
| `game_logs` | `player_id` | INTEGER | Referenz auf Spieler für Log-Einträge |
| `gebaeude_typen` | `Bautyp` | VARCHAR | Existierte bereits (Case-Sensitivity), kein Update nötig |
| `provinz_reserven` | `vorkommen_id` | INTEGER | Verweis auf Vorkommen-Tabelle |
| `steuer_einstellungen` | `kindergeld_rate` | FLOAT | Kindergeld-Parameter für Steuerkonfiguration |
| `handelsrouten` | `owner_province_id` | INTEGER | Provinz des Route-Eigentümers |
| `handelsrouten` | `cargo_outbound_json` | VARCHAR | Ausgehende Fracht (JSON) |
| `handelsrouten` | `cargo_return_json` | VARCHAR | Rückkehrende Fracht (JSON) |
| `handelsrouten` | `settler_count` | INTEGER | Anzahl Siedler auf Route |
| `handelsrouten` | `karren_count` | INTEGER | Anzahl Handelskarren auf Route |
| `handelsrouten` | `travel_ticks_remaining` | INTEGER | Verbleibende Ticks bis Ziel |
| `handelsrouten` | `total_travel_ticks` | INTEGER | Gesamte Reisedauer in Ticks |
| `kontor_preise` | `mode` | VARCHAR | "buy" oder "sell" Modus |
| `kontor_preise` | `price` | FLOAT | Kontor-Preis |
| `kontor_preise` | `verbündete_only` | INTEGER | Nur für Verbündete sichtbar |
| `kontor_preise` | `active` | INTEGER | Aktiv/Inaktiv-Flag |
| `province_fields` | `id` | INTEGER | Primärschlüssel für Grid-Felder |
| `province_fields` | `occupied_building_id` | INTEGER | Verweis auf belegendes Gebäude |
| `admin_logs` | `created_at` | DATETIME | Erstellungszeitpunkt des Admin-Logs |

### Case-Sensitivity-Hinweis (SQLite)

Die Spalte `Bautyp` in `gebaeude_typen` existierte bereits in der Datenbank,
wurde aber vom Migrationsskript aufgrund von SQLite's Case-Sensitivity bei
`PRAGMA table_info()` nicht als vorhanden erkannt. Das Migrationsskript wurde
daher um eine Case-Insensitive-Vergleichslogik erweitert.

## Unveränderte Tabellen (Orphan Tables)

Folgende DB-Tabellen haben keine entsprechenden SQLAlchemy Models:

| Tabelle | Bemerkung |
|---------|-----------|
| `building_data` | Gebäudedaten aus Webcrawler |
| `handels_routen` | Alte Handelsrouten-Tabelle (evtl. veraltet) |
| `lebewesen` | Lebewesen-Daten aus Webcrawler |
| `provinz_feldtypen` | Feldtyp-Konfiguration |
| `ressourcen_reserven` | Ressourcen-Reserven aus Webcrawler |
| `trade_route_logic` | Alte Handelsrouten-Logik |

Diese Tabellen wurden **nicht** entfernt, da sie Daten enthalten könnten.
Models für diese Tabellen können bei Bedarf in `app/models.py` ergänzt werden.

## Migrationsskript

**Pfad:** `scripts/db_migration.py`

### Features
- **Idempotent:** Mehrmaliges Ausführen ohne Fehler (zweiter Lauf: "schema up to date")
- **Automatisch:** Erkennt fehlende Tabellen und Spalten via SQLAlchemy Models
- **Sicher:** Keine Datenlöschung, nur `ALTER TABLE ADD COLUMN`

### Usage
```bash
cd /home/fabian/Wasteland && python3 scripts/db_migration.py
```

## Verifikation

- ✅ Migration lief ohne Fehler durch (16 Spalten hinzugefügt)
- ✅ Zweiter Lauf bestätigt: "Database schema is up to date"
- ✅ Alle migrierten Spalten in DB verifiziert

## Nächste Schritte

1. Server neu starten und Game-Tick testen
2. Eventuell Models für Orphan Tables ergänzen
3. Regelmäßige Migration-Checks einplanen
