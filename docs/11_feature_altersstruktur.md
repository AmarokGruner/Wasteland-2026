# Feature: Altersstruktur der Bevölkerung

## Design
1 tick (24h) = 5 years
- Kind (0-14):    0-2 ticks  → cannot work
- Arbeiter (15-64): 3-12 ticks → work, trade routes, military (age 20-25 = ticks 4-5)
- Rentner (65+):  13-15 ticks → no work, receive Rente
- Tod: after tick 15 (age 75+) → probability of death increases each tick

## Data Models
```python
PopulationCohort: province_id, age_group("kind"/"arbeiter"/"rentner"),
                  tick_age(int), count(int)
# One cohort row per tick_age (0-15) per province
```

## Core Logic (per 24h tick)
```
AGING (every tick):
  for each cohort: tick_age += 1
  cohorts with tick_age == 3: group changes "kind" → "arbeiter"
  cohorts with tick_age == 13: group changes "arbeiter" → "rentner"

DEATH RATE:
  tick 13 (Rentner 65): death_rate = 0.05 per tick
  tick 14 (70):         death_rate = 0.15
  tick 15 (75):         death_rate = 0.40
  tick >15 (80+):       cohort.count = 0 (fully removed)

BIRTHS (per 24h tick):
  birth_rate = regierungsform.wachstum * (1 - bildung/200) * base_birth_rate(0.02)
  new_kind = arbeiter_count * birth_rate
  add new cohort: tick_age=0, count=new_kind

PROVINCE TOTALS (computed from cohorts):
  population = sum(all cohorts)
  mips_available = sum(cohort.count for arbeiter cohorts) * produktivitaet_modifier
  arbeitsfaehig_20_25 = sum(cohort.count for tick_age in [4,5])  # trade/military eligible

KINDERGELD / RENTE (per tick if Steueramt active):
  provinzkonto -= kind_count   * kindergeld_rate
  provinzkonto -= rentner_count * rente_rate
  volkskonto   += kind_count   * kindergeld_rate + rentner_count * rente_rate

BILDUNG EFFECT:
  avg_tick_age = weighted_avg(cohort.tick_age, cohort.count)
  bildung = min(100, avg_tick_age * 6 + bildungsgebaeude_points)
```

## Endpoints
```
GET  /province/{id}/population → {total, kind, arbeiter, rentner, eligible_20_25, bildung}
GET  /province/{id}/population/forecast?ticks=5 → projected cohort evolution
POST /province/{id}/settings/soziales {"kindergeld_rate": float, "rente_rate": float}
```

## Notes
- Population growth is slow by design (3-4 ticks to first worker)
- regierungsform.wachstum multiplier applied to birth_rate
- Military/trade eligibility: only tick_age 4-5 cohorts (age 20-25)
