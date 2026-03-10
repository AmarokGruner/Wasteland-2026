# Feature: Kulturpunkte, Bildung & Staatsform

## Source (FAQ 2.8, 2.9, 6.5)
- Kulturpunkte: 1 per province size_level + from buildings (e.g. Glockenturm)
- Regierungsform modifies kulturpunkte by percentage
- Kultureinfluss grows → annexes free neighboring fields on world map
- Foreign culture in own province → moral malus
- Bildung (Education): increases techproduktion bonus + reduces birth rate
- Bildung raised by: higher average citizen age + Bildungsgebäude (Bildungspunkte)
- Techproduktion: Bunker=2, Feuerstelle=+1 each, Ruine-Laboratorium=+2
- Every province has independent tech_level that catches up to player max over time

## Data Models
```python
Province: ..., kulturpunkte_per_day, kultureinfluss_total, bildung(0-100), tech_production
Player: ..., tech_level, regierungsform_id
RegierungsformModifier: id, name, kultur_mult, provinz_max_no_penalty, ...
```

## Core Logic (per 24h tick)
```
TECHPRODUKTION:
  tech_points = sum(building.spezialeigenschaften.techproduktion) 
              * (1 + bildung/100)
  player.tech_level += tech_points

KULTURPUNKTE:
  daily_kultur = province.size_level 
               + sum(building.spezialeigenschaften.kulturpunkte)
  daily_kultur *= regierungsform.kultur_mult
  province.kultureinfluss_total += daily_kultur

KULTUREINFLUSS (world map effect):
  if kultureinfluss_total > threshold: annex nearest free field
  → triggers GameLog event

BILDUNG:
  avg_age = population_age_distribution.mean()
  bildung = min(100, avg_age * 2 + bildungsgebaeude_points)
  birth_rate = base_birth_rate * (1 - bildung/200)  # higher edu = lower births

MULTI-PROVINCE MORAL PENALTY:
  extra_provinces = max(0, len(player.provinces) - regierungsform.provinz_max)
  all_provinces.moral -= extra_provinces * penalty_per_province
```

## Endpoints
```
GET  /player/{id}/tech → tech_level, daily_techproduktion, bildung per province
GET  /province/{id}/kultur → kulturpunkte, einfluss, annexed_fields
POST /player/{id}/regierungsform {"form_id": int}  # requires Regierungssitz
```
