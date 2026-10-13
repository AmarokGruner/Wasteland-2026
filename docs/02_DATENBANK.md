# Datenbank-Schema & Migrationen

**Wasteland Database Schema | Version 1.6**

---

## 📊 Tabellen-Übersicht

Die Datenbank verwendet SQLite mit SQLAlchemy ORM. Alle Modelle sind in `app/models.py` definiert.

### Kern-Tabellen

| Tabelle | Zeilen | Beschreibung | Primärschlüssel |
|---------|--------|--------------|-----------------|
| `gebaeude_typen` | 209 | Gebäude-Typen | `id` (INTEGER) |
| `ressourcen` | 153 | Ressourcen-Arten | `id` (INTEGER) |
| `vorkommen` | 24 | Bodenschätze/Vorkommen | `id` (INTEGER) |
| `terrain_typen` | 42 | Landschaftstypen | `id` (INTEGER) |
| `provinzen` | - | Spieler-Provinzen | `id` (INTEGER) |
| `provinz_gebaeude` | - | Gebäude-Instanzen | `id` (INTEGER) |
| `einheiten_typen` | 63 | Militäreinheiten | `id` (INTEGER) |
| `lebewesen` | 8 | Tierarten | `id` (INTEGER) |
| `artikel` | 15 | Handelsartikel | `id` (INTEGER) |
| `regierungsformen` | 7 | Staatsformen | `id` (INTEGER) |

### Zusätzliche Tabellen

| Tabelle | Beschreibung |
|---------|--------------|
| `users` | Benutzerkonten |
| `players` | Spieler-Profile |
| `provinz_lager` | Lagerbestände pro Provinz |
| `provinz_einheiten` | Einheiten in Provinzen |
| `handels_routen` | Handelsrouten zwischen Provinzen |
| `game_logs` / `gamelog_entries` | Spielereignisse |
| `diplomatie` | Diplomatische Beziehungen |
| `combat_logs` | Kampfhistorie |

---

## 🏗️ Wichtige Tabellen-Details

### `gebaeude_typen` - Gebäude-Typen

```sql
CREATE TABLE gebaeude_typen (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    kategorie TEXT,              -- Farm, Industrie, Bildung, etc.
    bautyp TEXT,                 -- Land, Stadt, Stadtausbau, Weg
    baubar INTEGER DEFAULT 1,    -- 1=baubar, 0=nicht baubar
    ausbaubar INTEGER DEFAULT 0, -- 1=ausbaubar, 0=nicht ausbaubar
    unique_gebaeude INTEGER DEFAULT 0, -- 1=einmalig pro Provinz
    nur_kueste INTEGER DEFAULT 0,      -- 1=nur an Küste baubar
    ist_feld INTEGER DEFAULT 0,        -- 1=ist ein Feld (z.B. Farm)
    tech_level INTEGER DEFAULT 0,      -- Erforderliches Tech-Level
    baukosten_mips INTEGER DEFAULT 0,  -- MIPS-Kosten für Bau
    ausbaukosten_mips INTEGER DEFAULT 0,
    arbeiter INTEGER DEFAULT 0,        -- Benötigte Arbeiter
    wohnraum INTEGER DEFAULT 0,        -- Bietet Wohnraum
    lagerkapazitaet INTEGER DEFAULT 0, -- Lagerraum-Kapazität
    produktion TEXT DEFAULT '[]',      -- JSON: Produzierte Ressourcen
    rohstoffverbrauch TEXT DEFAULT '[]',-- JSON: Verbrauchte Ressourcen
    rohstoffbedarf_bau TEXT DEFAULT '[]', -- JSON: Rohstoffe für Bau
    terrain_effektivitaet TEXT DEFAULT '{}', -- JSON: Terrain-Boni
    spezial_eigenschaften TEXT DEFAULT '{}' -- JSON: Spezialboni
);
```

**Beispiel-Einträge:**
- ID 1: Bunker (Start-Gebäude, unique)
- ID 2-14: Verschiedene Farmen (Kartoffel, Erdnuss, etc.)
- ID 15-17: Rohstoffgewinnung (Holzfäller, Steinmetz)
- ID 64: Siedlung (Stadt-Level 0)

### `ressourcen` - Ressourcen-Arten

```sql
CREATE TABLE ressourcen (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    typ TEXT NOT NULL,           -- Nahrung, Getränk, Baurohstoff, etc.
    wert INTEGER DEFAULT 0       -- Basiswert für Handel
);
```

**Kategorien:**
- **Nahrung:** Kartoffeln, Reis, Mais, etc.
- **Getränke:** Wasser, Tee, Alkohol, etc.
- **Baurohstoffe:** Stein, Holz, Ziegel, Aluminium, etc.
- **Luxusgüter:** Stoffe, Möbel, Schmuck, etc.

### `vorkommen` - Bodenschätze/Vorkommen

```sql
CREATE TABLE vorkommen (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    typ TEXT,                    -- Geologisch, Oberfläche, Unter Seen
    tech INTEGER,                -- Erforderliches Tech-Level
    suchkosten INTEGER,          -- MIPS für Suche
    beschreibung TEXT,
    findwahrscheinlichkeit TEXT  -- JSON: {terrain_name: prozent}
);
```

### `provinzen` - Spieler-Provinzen

```sql
CREATE TABLE provinzen (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    besitzer_id INTEGER REFERENCES players(id),
    mips INTEGER DEFAULT 0,      -- Währung
    bevölkerung INTEGER DEFAULT 0,
    size_level INTEGER DEFAULT 0, -- 0=Siedlung, 1=Dorf, ..., 8=Großstadt
    next_required_building_id INTEGER REFERENCES gebaeude_typen(id),
    -- Weitere Felder...
);
```

### `provinz_gebaeude` - Gebäude-Instanzen

```sql
CREATE TABLE provinz_gebaeude (
    id INTEGER PRIMARY KEY,
    provinz_id INTEGER REFERENCES provinzen(id),
    gebaeude_typ_id INTEGER REFERENCES gebaeude_typen(id),
    x INTEGER NOT NULL,          -- Weltkarte X-Koordinate
    y INTEGER NOT NULL,          -- Weltkarte Y-Koordinate
    level INTEGER DEFAULT 1,     -- Ausbaustufe (1-10)
    built_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔄 Migrationen

### Letzte Migration: 2026-10-14
- Gebäude-Datenbank auf 209 Typen aktualisiert
- Neue Ressourcen (Aluminium, ID 91) hinzugefügt

### Wichtige Migrationen

| Datum | Beschreibung | Datei |
|-------|--------------|-------|
| 2026-09 | Datenbank-Schema Anpassung | `MIGRATION_2026-09.md` |
| 2026-10 | Weltkarte DB-Migration | `27_weltkarte_db_migration.md` |

### Migration durchführen

```bash
# Manuelle Migration
python scripts/db_migration.py

# Oder über Seed-Skript
python seeds/seed_main.py
```

---

## 🔗 Beziehungen zwischen Tabellen

```
provinzen (1) ────< (N) provinz_gebaeude
                      │
                      └──> gebaeude_typen (N)

provinzen (1) ────< (N) provinz_lager
                      │
                      └──> ressourcen (N)

provinzen (1) ────< (N) provinz_einheiten
                      │
                      └──> einheiten_typen (N)

provinzen (1) ────< (N) handels_routen
                      │
                      └──> provinzen (N) [Ziel]

players (1) ────< (N) provinzen
                      │
                      └──> (N) game_logs
```

---

## 📝 Hinweise für Entwickler

1. **Alle Modelle in `app/models.py`** - Bei Änderungen immer dort aktualisieren
2. **Seed-Daten in `seeds/`** - Initialisierung der Datenbank
3. **Migrationen versionieren** - Immer Datum und Beschreibung dokumentieren
4. **JSON-Felder** - `produktion`, `rohstoffverbrauch` etc. sind JSON-Strings
5. **Foreign Keys** - Immer referentielle Integrität beachten

---

**Letzte Aktualisierung:** 2026-10-14  
**Datenbank-Datei:** `verbrannte_zone.db`
