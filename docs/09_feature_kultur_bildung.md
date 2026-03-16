# Feature: Kulturpunkte, Bildung & Staatsform

## Status
**IMPLEMENTIERT** (v1.0)

## Source (FAQ 2.8, 2.9, 6.5)
- Kulturpunkte: 1 per province size_level + from buildings (e.g. Glockenturm)
- Regierungsform modifies kulturpunkte by percentage
- Kultureinfluss grows → annexes free neighboring fields on world map (TODO)
- Foreign culture in own province → moral malus (TODO)
- Bildung (Education): increases techproduktion bonus + reduces birth rate
- Bildung raised by: higher average citizen age + Bildungsgebäude (Bildungspunkte)
- Techproduktion: Bunker=2, Feuerstelle=+1 each, Ruine-Laboratorium=+2
- Every province has independent tech_level that catches up to player max over time

## Data Models (app/models.py)
```python
Province:
  - kulturpunkte (int): Current culture points
  - kultureinfluss_total (float): Accumulates for field annexation
  - tech_production (int): Daily tech production points
  - size_level (int): 1-7 (Camp to Metropole)

Player:
  - tech_level (int): Player's technology level
  - regierungsform_id (int, FK): Current government form

Regierungsform:
  - id, name, kulturverbreitung (kultur_mult), forschungsfortschritt
  - produktivitaet, wachstum, finanzen, sicherheit
  - provinzanzahl_bis_malus (max provinces without moral penalty)
```

## Core Logic (app/kultur_bildung_logic.py)

### TECHPRODUKTION (daily at midnight)
```
tech_multiplier = 1 + (bildung / 100.0) * forschungsfortschritt
tech_production = sum(building.techproduktion) * tech_multiplier
player.tech_level += tech_production
```
- Bunker: +2 techproduktion per level
- Ruine-Laboratorium terrain: +2 base

### KULTURPUNKTE (daily at midnight)
```
daily_kultur = size_level + sum(building.kulturpunkte * level)
daily_kultur *= regierungsform.kulturverbreitung
kulturpunkte += daily_kultur
kultureinfluss_total += daily_kultur
```
- Buildings: Glockenturm, Theater, etc. add kulturpunkte

### BILDUNG (computed)
```
bildung = min(100, avg_tick_age * 6 + bildungsgebaeude_points)
```
- Used for tech multiplier and birth rate reduction

### MULTI-PROVINCE MORAL PENALTY (daily at midnight)
```
provinz_max = regierungsform.provinzanzahl_bis_malus
extra_provinces = max(0, province_count - provinz_max)
moral_loss = extra_provinces * 16
```

## Endpoints (app/api/)

### GET /player/{id}/tech
Returns player's tech level and daily production per province:
```json
{
  "player_id": 1,
  "total_tech_level": 42,
  "daily_tech_total": 5,
  "forschungs_mult": 1.0,
  "provinces": [
    {"province_id": 1, "name": "Home", "tech_production_base": 4, "daily_tech_expected": 4}
  ]
}
```

### GET /province/{id}/kultur
Returns culture points and influence data:
```json
{
  "province_id": 1,
  "kulturpunkte_current": 25,
  "kultureinfluss_total": 150.0,
  "kulturpunkte_daily": 5,
  "can_annex_field": true,
  "progress_percent": 50.0,
  "next_annex_at": 100
}
```

### POST /player/{id}/regierungsform
Change player's government form:
```json
{"form_id": 2}
```
Returns: `{"success": true, "player_id": 1, "regierungsform_id": 2, "regierungsform_name": "Anarchie"}`

## Notes
- Kultur/Tech processing runs once daily at midnight (hour 0)
- Bildung is calculated from population age distribution + building points
- Multi-province penalty applies only when exceeding provincial limit
