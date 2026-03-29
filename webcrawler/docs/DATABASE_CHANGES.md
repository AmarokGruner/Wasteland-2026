# Database Changes Documentation

This document describes all database schema changes made for the webcrawler integration.

## Overview

The webcrawler scrapes game data from https://v3.verbranntezone.ch/ and syncs it to the local SQLite database. This document tracks all database schema changes needed to support the crawler.

## Changes Summary

### Date: 2026-03-29

Added new columns to support image/logo URLs and additional data fields from the website.

---

## Table: gebaeude_typen (Buildings)

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `icon_url` | VARCHAR(255) | '' | Building symbol/icon image URL (e.g., `./gebpics/1/bunker.png`) |
| `bild_url` | VARCHAR(255) | '' | Building image URL (e.g., `/geb/1/g1_0r.png`) |

**Source:** Extracted from `<div class='title'>` format and table rows with "Gebäudesymbol" / "Gebäudebild" labels.

---

## Table: terrain_typen (Terrains)

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `bild_url` | VARCHAR(255) | '' | Terrain map image URL (e.g., `/map/1/t1a.gif`) |
| `grundwasserspiegel` | REAL | 50.0 | Ground water level |
| `durchschnittliche_feuchtigkeit` | REAL | 50.0 | Average moisture |
| `startgebiet` | INTEGER | 0 | Is start territory (0/1) |
| `regen_pct` | INTEGER | 0 | Rain probability percentage |
| `holz_yield` | REAL | 1.0 | Wood yield multiplier |
| `stein_yield` | REAL | 1.0 | Stone yield multiplier |
| `eisen_yield` | REAL | 1.0 | Iron yield multiplier |

**Source:** Extracted from `<div class='title'>` format and table rows with terrain data.

---

## Table: einheiten_typen (Units)

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `bild_url` | VARCHAR(255) | '' | Unit image URL |

**Source:** Extracted from table rows with "Bild" or "Symbol" labels.

---

## Table: artikel (Articles/Items)

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `bild_url` | VARCHAR(255) | '' | Article/item image URL |

**Source:** Extracted from table rows with "Bild" or "Symbol" labels.

---

## Table: vorkommen (Resource Deposits)

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `bild_url` | VARCHAR(255) | '' | Deposit image URL |

**Source:** Extracted from table rows with "Bild" or "Symbol" labels.

---

## Table: regierungsformen (Government Forms)

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `bild_url` | VARCHAR(255) | '' | Government form image URL |

**Source:** Extracted from table rows with "Bild" or "Symbol" labels.

---

## Table: tier_vorlagen (Animal Templates)

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `bild_url` | VARCHAR(255) | '' | Animal image URL |

**Source:** Extracted from table rows with "Bild" or "Symbol" labels.

---

## Migration

To apply these changes to an existing database, run the migration script:

```bash
python webcrawler/migrations/001_webcrawler_fields.py
```

The script will:
1. Attempt to add each column
2. Skip columns that already exist (no error)
3. Report any other errors

---

## HTML Parsing Changes

### Title Extraction

All detail pages now use `<div class='title'>` format instead of `<h1>`:

```html
<!-- Old format -->
<h1>Bunker</h1>

<!-- New format (real website) -->
<div class='title'>Bunker <i>(ID: 1)</i></div>
```

The parsers now extract the name using regex:
```python
match = re.match(r'^(.+?)(?:\s*<i>)?\s*\(ID:\s*\d+\)', title_text)
name = match.group(1).strip()
```

### Image URLs

Building detail pages contain images in table rows:

```html
<tr>
    <td class='boxfarbe4'>Gebäudesymbol</td>
    <td class='boxfarbe9'><img src='./gebpics/1/bunker.png'></td>
</tr>
<tr>
    <td class='boxfarbe4'>Gebäudebild</td>
    <td class='boxfarbe9'><img src='/geb/1/g1_0r.png'></td>
</tr>
```

---

## Usage in Game Code

### Displaying Building Images

```python
from app.models import BuildingType

building = session.query(BuildingType).filter_by(id=1).first()
if building.bild_url:
    # Full URL: https://v3.verbranntezone.ch/ + building.bild_url
    image_url = f"https://v3.verbranntezone.ch/{building.bild_url}"
```

### Displaying Terrain Map

```python
from app.models import TerrainType

terrain = session.query(TerrainType).filter_by(id=1).first()
if terrain.bild_url:
    map_url = f"https://v3.verbranntezone.ch/{terrain.bild_url}"
```

---

## Notes

1. **Image URLs are relative** - prepend `https://v3.verbranntezone.ch/` to get the full URL
2. **Image URLs may change** - the crawler captures the current state from the website
3. **Run crawler periodically** to keep images/URLs updated
4. **Handle missing images** - some items may not have images (empty string)
