# Feature: Einheiten & Militär-System

## Source (FAQ 5.x + 3.1.x)
- Province starts with 20 soldiers (minimum, cannot dismiss)
- Ausbildungscamp/Kaserne trains 2 recruits/24h per building (scales with ausbaukostenmips level)
- Training buildings auto-train existing units when no new recruits queued (max training=100)
- Soldiers need wohnraum + 0.5 Nahrung + 0.5 Getränk /24h (same as citizens)
- Security target: ~1 soldier per 10 inhabitants → moral bonus; below → moral malus
- Sicherheitsbonus from buildings (e.g. Palisadenwall +50, Ruine-Festung +30)
- Einheiten count toward einheiten_count in province supply calculations
- Only citizens aged 20-25 can leave province (for trade routes / expeditions)

## Data Models
```python
Unit: id, province_id, count, training(0-100), fitness(0-100), type("soldier"/"settler")
Province: ..., min_soldiers=20, security_bonus(sum from buildings)
```

## Core Logic (per 24h tick)
```
TRAINING:
  if new_recruits_queued: train queue (ausbildung * buildings)
  else: increase training by (ausbildung_total / unit_count) per tick, cap 100

SUPPLY (already in roundlogic):
  consume 0.5 Nahrung + 0.5 Getränk per unit per 24h

SECURITY:
  security_ratio = units / population
  if security_ratio >= 0.1: moral += security_bonus
  else: moral -= proportional_malus

FITNESS:
  idle units: fitness += 1/tick, cap 100
  combat/marching: fitness -= per action
```

## Endpoints
```
POST /province/{id}/military/train {"unit_type": str, "count": int}
GET  /province/{id}/military/status → {units, training, fitness, security_ratio}
POST /province/{id}/military/dismiss {"count": int}  # min 20 enforced
```

## Validation
- Cannot dismiss below min_soldiers=20
- Training requires Ausbildungscamp (ausbaukostenmips spezialeigenschaft)
- Fitness/training = 0 → combat power at 50%; =50 → 75%
