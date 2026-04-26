# Feature: Tierzucht & Wildtier-Management

## Source (seed_gebaeude.py: Hühnerfarm, Nuggretszucht; FAQ 3.x)
- Pflanzenfresser eat province fields if starving (reduce terrain yield)
- NO fleischfresser attacks (by design)
- Animals can be captured (via Jagen), bred in farms, or released
- Live animals in lager = breedable stock
- Tierzucht buildings (e.g. Hühnerfarm): require starter animals + feed resource
- Animals in province contribute to Jagen yield passively

## Data Models
```python
ProvinceAnimal: province_id, animal_resource_id, count, is_wild(bool)
# wild=True: roaming (from Jagen captures or pre-seeded)
# wild=False: in breeding building (BuildingInstance manages them)

AnimalTemplate (from seed_ressourcen.py typ="Tier"):
  resource_id, feed_resource_id, feed_amount_per_24h,
  breed_output_resource_id, breed_rate, is_pflanzenfresser(bool)
```

## Core Logic (per 24h tick)
```
WILD ANIMAL FEEDING (Pflanzenfresser only):
  for each wild animal (is_wild=True, is_pflanzenfresser=True):
    food_needed = count * feed_amount_per_24h
    available = lager[feed_resource_id]
    if available >= food_needed:
      lager[feed_resource_id] -= food_needed
    else:
      # starving: eat fields instead
      starving_ratio = (food_needed - available) / food_needed
      terrain_yield_malus -= starving_ratio * 0.1  # up to -10% terrain eff per tick
      lager[feed_resource_id] = 0

BREEDING (in Tierzucht building, per 24h):
  for each active breeding building:
    if lager[starter_animal] >= min_stock AND lager[feed_resource] >= feed_amount:
      lager[feed_resource] -= feed_amount
      new_animals = floor(stock_count * breed_rate)
      lager[breed_output_resource] += new_animals  # e.g. Eier, Fleisch, Fell
      lager[starter_animal] += new_stock_growth    # herd grows slowly

CAPTURE → BREED:
  captured animal (from Jagen) → stored in lager as resource
  player assigns to breeding building manually
  → ProvinceAnimal created with is_wild=False

RELEASE:
  player releases animals → ProvinceAnimal is_wild=True
  → increases passive Jagen yield for terrain
```

## Endpoints
```
GET  /province/{id}/animals → {wild: [...], breeding: [...], terrain_malus}
POST /province/{id}/animals/release {"animal_resource_id": int, "count": int}
POST /province/{id}/animals/assign {"building_instance_id": int, "animal_resource_id": int}
GET  /province/{id}/animals/preview → feeding costs + expected breed output next tick
```

## Validation
- Cannot assign animal to building that doesn't match AnimalTemplate
- Release requires count <= lager[animal_resource_id]
- terrain_yield_malus capped at -50% (animals cannot destroy province completely)
