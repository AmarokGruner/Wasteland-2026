# Datenbank-Abgleich: Original vs. models.py

**Datum:** 2026-10-14

## Zusammenfassung

- **Tabellen in Original-DB:** 50
- **Models in models.py:** 45
- **Tabellen nur in DB (nicht gemapped):** 5
- **Models ohne DB-Tabelle:** 0
- **Tabellen mit Spalten-Unterschieden:** 11

## ⚠️ Tabellen nur in Original-DB (nicht in models.py gemapped)

- `building_data`
- `handels_routen`
- `lebewesen`
- `provinz_feldtypen`
- `ressourcen_reserven`

## 🔍 Spalten-Unterschiede (Achtung!)

### `artikel` (Model: Article)

**Fehlt in DB:**
- `created_at`
- `gewicht`
- `haltbarkeit`
- `updated_at`

### `einheiten_typen` (Model: UnitType)

**Fehlt in DB:**
- `beschreibung`
- `created_at`
- `erstellbedingung`
- `fernkampf_panzerung`
- `fortbewegung`
- `geschwindigkeit`
- `max_reichweite`
- `nahkampf_panzerung`
- `nahkampf_staerke`
- `platzbedarf_luft`
- `platzbedarf_see`
- `platzbedarf_untersee`
- `transport_land`
- `updated_at`
- `zugehoerig`

### `gebaeude_typen` (Model: BuildingType)

**Fehlt in DB:**
- `bautyp`
- `beschreibung`
- `created_at`
- `energiebedarf`
- `schlachtfeld`
- `symbol_emoji`
- `symbol_url`
- `updated_at`
- `vorkommen_effektivitaet`
- `zusatzarbeiter_pro_stufe`
- `zusatzwohnraum_pro_stufe`
**Fehlt im Model:**
- `Bautyp`

### `handelsrouten` (Model: TradeRoute)

**Fehlt in DB:**
- `cargo_json`
- `origin_province_id`
- `owner_id`
- `settlers_count`

### `players` (Model: Player)

**Fehlt in DB:**
- `last_reset_at`

### `regierungsformen` (Model: Regierungsform)

**Fehlt in DB:**
- `beschreibung`
- `created_at`
- `updated_at`

### `ressourcen` (Model: Resource)

**Fehlt in DB:**
- `beschreibung`
- `created_at`
- `fleisch_bei_schlachtung`
- `platz_land`
- `platz_luft`
- `platz_wasser`
- `platzbedarf`
- `produktionswert`
- `produziert_von`
- `updated_at`
- `verbrauch`
- `verbrauch_hinweis`
- `verbraucht_von`

### `terrain_typen` (Model: TerrainType)

**Fehlt in DB:**
- `abwertungen`
- `aufwertungen`
- `created_at`
- `gebaeude_effektivitaet`
- `updated_at`
**Fehlt im Model:**
- `abwertungen_json`
- `aufwertungen_json`
- `gebaeude_effektivitaet_json`

### `users` (Model: User)

**Fehlt in DB:**
- `created_at`
- `reset_token_expires`
- `updated_at`

### `vorkommen` (Model: Vorkommen)

**Fehlt in DB:**
- `beschreibung`
- `created_at`
- `updated_at`

### `world_map_cells` (Model: MapCell)

**Fehlt in DB:**
- `preset_buildings`

## ✅ Vollständigkeitsprüfung - Kern-Tabellen

| Tabelle | In DB | In Model | Spalten DB | Spalten Model | Status |
|---------|-------|----------|------------|---------------|--------|
| gebaeude_typen | ✅ | ✅ | 33 | 23 | ⚠️ 33 vs 23 |
| ressourcen | ✅ | ✅ | 17 | 4 | ⚠️ 17 vs 4 |
| vorkommen | ✅ | ✅ | 10 | 7 | ⚠️ 10 vs 7 |
| terrain_typen | ✅ | ✅ | 21 | 19 | ⚠️ 21 vs 19 |
| provinzen | ✅ | ✅ | 34 | 34 | ✅ OK |
| provinz_gebaeude | ✅ | ✅ | 7 | 7 | ✅ OK |
| einheiten_typen | ✅ | ✅ | 27 | 12 | ⚠️ 27 vs 12 |
| lebewesen | ✅ | ❌ | 9 | 0 | ❌ Fehlt im Model |
| artikel | ✅ | ✅ | 22 | 18 | ⚠️ 22 vs 18 |
| regierungsformen | ✅ | ✅ | 30 | 27 | ⚠️ 30 vs 27 |

---

## 📋 Empfohlene Aktionen

1. **Tabellen nur in DB prüfen:**
   - `building_data` - Existiert nur in Datenbank, nicht im Model
   - `handels_routen` - Existiert nur in Datenbank, nicht im Model
   - `lebewesen` - Existiert nur in Datenbank, nicht im Model
   - `provinz_feldtypen` - Existiert nur in Datenbank, nicht im Model
   - `ressourcen_reserven` - Existiert nur in Datenbank, nicht im Model

2. **Spalten-Unterschiede beheben:**
   - `artikel`: DB fehlt Spalten: created_at, gewicht, haltbarkeit, updated_at
   - `einheiten_typen`: DB fehlt Spalten: beschreibung, created_at, erstellbedingung, fernkampf_panzerung, fortbewegung
   - `gebaeude_typen`: Model fehlt Spalten: Bautyp
   - `gebaeude_typen`: DB fehlt Spalten: bautyp, beschreibung, created_at, energiebedarf, schlachtfeld
   - `handelsrouten`: DB fehlt Spalten: cargo_json, origin_province_id, owner_id, settlers_count
   - `players`: DB fehlt Spalten: last_reset_at
   - `regierungsformen`: DB fehlt Spalten: beschreibung, created_at, updated_at
   - `ressourcen`: DB fehlt Spalten: beschreibung, created_at, fleisch_bei_schlachtung, platz_land, platz_luft
   - `terrain_typen`: Model fehlt Spalten: abwertungen_json, aufwertungen_json, gebaeude_effektivitaet_json
   - `terrain_typen`: DB fehlt Spalten: abwertungen, aufwertungen, created_at, gebaeude_effektivitaet, updated_at
   - `users`: DB fehlt Spalten: created_at, reset_token_expires, updated_at
   - `vorkommen`: DB fehlt Spalten: beschreibung, created_at, updated_at
   - `world_map_cells`: DB fehlt Spalten: preset_buildings

3. **Datenbank initialisieren:**
   ```bash
   python seeds/seed_main.py
   ```