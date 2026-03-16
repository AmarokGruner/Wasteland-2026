# Feature: Altersstruktur der Bevölkerung

## Status
**IMPLEMENTIERT** (v1.0)

## Design
1 tick (24h) = 5 years
- Kind (0-14):    0-2 ticks  → cannot work
- Arbeiter (15-64): 3-12 ticks → work, trade routes, military (age 20-25 = ticks 4-5)
- Rentner (65+):  13-15 ticks → no work, receive Rente
- Tod: after tick 15 (age 75+) → probability of death increases each tick

## Data Models
```python
PopulationCohort: 
  - id, province_id, tick_age (0-15), age_group ("kind"/"arbeiter"/"rentner"), count
  
TaxSettings:
  - province_id, tax_rate, lohn_rate, sold_rate, rente_rate, state_transfer_pct, kindergeld_rate
```

**Änderungen gegenüber SQLAlchemy:**
- `PopulationCohort.province_id` statt `provinz_id`
- `age_group` Spalte hinzugefügt für einfachere Queries

## Core Logic (app/population_logic.py)
```
AGING (every midnight tick):
  for each cohort: tick_age += 1
  cohorts with tick_age == 3: group changes "kind" → "arbeiter"
  cohorts with tick_age == 13: group changes "arbeiter" → "rentner"

DEATH RATE:
  tick 13 (Rentner 65): death_rate = 0.05 per tick
  tick 14 (70):         death_rate = 0.15  
  tick 15 (75):         death_rate = 1.0 (removed)
  tick >15               → removed automatically

BIRTHS (per midnight tick):
  birth_rate = (tech_level/10 + 1) * (1 - bildung/200) * base_birth_rate(0.02)
  new_children = arbeiter_count * birth_rate
  add/update cohort: tick_age=0, age_group="kind", count=new_children

PROVINCE TOTALS (computed from cohorts):
  population = sum(all cohorts)
  mips_available = arbeiter_count * produktivitaet_modifier
  eligible_20_25 = sum(cohort.count for tick_age in [4,5])  # trade/military eligible
```

## Kindergeld / Rente (app/population_logic.py:process_kindergeld_and_rente)
```
if Steueramt active:
  kindergeld = kind_count * settings.kindergeld_rate
  rente      = rentner_count * settings.rente_rate
  
  total_payment = kindergeld + rente
  if provinzkonto >= total_payment:
    provinzkonto -= total_payment
    volkskonto   += total_payment
```

## Bildung Effect (app/population_logic.py:calculate_bildung)
```
weighted_age = sum(tick_age * count) / total_count
bildung = min(100, weighted_age * 6 + bildungsgebaeude_points)
```

## Endpoints (app/api/province.py)
```
GET  /province/{id}/population 
     → {total, kind, arbeiter, rentner, eligible_20_25, bildung}

GET  /province/{id}/population/forecast?ticks=5 
     → {province_id, ticks_requested, forecast: [{tick, total, kind, arbeiter, rentner}, ...]}

POST /province/{id}/settings/soziales 
     {"kindergeld_rate": float, "rente_rate": float}
     → {success, province_id, kindergeld_rate, rente_rate}
```

## Integration
- `app/tick_logic.py`: Tägliche Verarbeitung um Mitternacht (hour == 0)
- `process_population_tick()`: Aging, Deaths, Births
- `process_kindergeld_and_rente()`: Nur wenn Steueramt aktiv

## Notes
- Population growth is slow by design (3-4 ticks to first worker)
- Birth rate uses tech_level as proxy for wachstum multiplier
- Military/trade eligibility: only tick_age 4-5 cohorts (age 20-25)
- Initial population distribution: 30% children, 50% workers, 20% retirees
