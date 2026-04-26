# Feature: Jagen, Sammeln & Feiertag

## Source
- Unassigned workers (not in any building) can: Arbeitslos / Sammeln / Jagen
- Only one mode active per province at a time (radio button)
- Feiertag: checkbox, active 1 day, stacks with any mode → moral boost, workers paid but no output
- Sammeln: building materials (Bauholz, Stein, Kies), local farmable food, Notrationen,
  forageable food (Beeren, Pilze, Gewürze, Stroh), Genussmittel
- Jagen: terrain-native animals → Häute + Fleisch; rare: live animal captured
- Base yield + random variation on ALL outputs (no identical results each day)
- 1 Sammler feeds ~2-4 people/day (food yield scaled to that range)

## Data Models
```python
ProvinceSettings: province_id, worker_mode("idle"/"sammeln"/"jagen"),
                  feiertag_active(bool), feiertag_expires_at(datetime)

SammelLoot: terrain_id, resource_id, base_amount, random_min, random_max,
            weight, loot_category("material"/"food_farmable"/"food_forage"/"genuss")
JagdLoot:   terrain_id, resource_id, base_amount, random_min, random_max,
            is_animal(bool), capture_chance
```

## Loot Categories (Sammeln)

### Materials (always present, terrain-independent base):
```
Bauholz:     base=2.0  + random(0.5, 2.0)
Stein:       base=1.0  + random(0.3, 1.5)
Kies:        base=1.0  + random(0.2, 1.2)
Notrationen: base=0.5  + random(0.0, 0.8)
Stroh:       base=0.5  + random(0.0, 1.0)   # always findable
```

### Food – Farmable (terrain-specific, what could be grown here):
```
# Resolved via terrain → possible_crops mapping (same as building terraineffektivitaet)
# e.g. Grasland → Getreide, Kartoffeln; Wald → Pilze, Beeren; Savanne → Hirse
base_per_crop = 0.3 + random(0.1, 0.6)   # small amounts, hints at what to farm
```

### Food – Forageable (semi-terrain-independent, common finds):
```
Beeren:   base=0.4 + random(0.0, 0.8)   # Wald, Grünland, Dschungel: +50% bonus
Pilze:    base=0.3 + random(0.0, 0.7)   # Wald, Sumpf, Dschungel: +100% bonus
Gewürze:  base=0.1 + random(0.0, 0.4)   # Savanne, Grünland, Dschungel: +50% bonus
Früchte:  base=0.2 + random(0.0, 0.6)   # Tropen, Dschungel, Wald: +100% bonus
```

## Core Logic (per 24h tick)
```
IDLE WORKERS:
  idle_workers = province.mips_available - sum(building.arbeiter)

FEIERTAG CHECK:
  if feiertag_active:
    moral += 5
    provinzkonto -= idle_workers * lohn_rate   # paid but no output
    feiertag_active = False  # expires after 1 tick
    return

SAMMELN (worker_mode == "sammeln" AND idle_workers > 0):
  efficiency = min(1.0, idle_workers / 100)  # 100 workers = full yield

  # MATERIALS (always, terrain-independent):
  for resource, base, rmin, rmax in MATERIAL_LOOT:
    amount = (base + random.uniform(rmin, rmax)) * efficiency
    lager_add(resource, amount)

  # FOOD TARGET: 1 idle_worker feeds 2-4 people
  food_target = idle_workers * random.uniform(2.0, 4.0)
  food_found = 0.0

  # FARMABLE FOOD (terrain-specific):
  for resource in terrain_possible_crops[province.terrain_id]:
    crop_amount = (0.3 + random.uniform(0.1, 0.6)) * efficiency
    lager_add(resource, crop_amount)
    food_found += crop_amount

  # FORAGEABLE FOOD (semi-universal):
  for resource, base, rmin, rmax, terrain_bonus_terrains in FORAGE_LOOT:
    bonus = 1.5 if province.terrain_id in terrain_bonus_terrains else 1.0
    amount = (base + random.uniform(rmin, rmax)) * efficiency * bonus
    lager_add(resource, amount)
    food_found += amount

  # SCALE UP if food_found < food_target (top up with Notrationen):
  if food_found < food_target:
    gap = food_target - food_found
    lager_add("Notrationen", gap * 0.5)  # partial gap fill

JAGEN (worker_mode == "jagen" AND idle_workers > 0):
  efficiency = min(1.0, idle_workers / 100)
  for loot in JagdLoot[province.terrain_id]:
    if loot.is_animal:
      if random() < loot.capture_chance * efficiency:
        lager_add(loot.resource_id, 1)  # live capture
    else:
      amount = (loot.base_amount + random.uniform(loot.random_min, loot.random_max)) * efficiency
      lager_add(loot.resource_id, amount)
  # Base Fleisch/Fell always present in any terrain:
  lager_add("Fleisch", 1.0 + random.uniform(0.0, 2.5) * efficiency)
  lager_add("Fell",    0.5 + random.uniform(0.0, 1.5) * efficiency)
```

## Endpoints
```
GET  /province/{id}/settings → worker_mode, feiertag_active, idle_workers
POST /province/{id}/settings {"worker_mode": "sammeln"/"jagen"/"idle"}
POST /province/{id}/feiertag  # activates for next tick (once per 24h)
GET  /province/{id}/settings/loot-preview
     → {"food_estimate": "feeds ~6-12 people", "materials": {...}, "forage": {...}}
```

## Validation
- feiertag: max once per 24h, cannot stack two days
- worker_mode change: effective next spool tick
- lager overflow: silently capped at lagerkapazitaet_total, preview shows "OVERFLOW_RISK"
- Jagen ohne JagdLoot für terrain → still yields base Fleisch/Fell
