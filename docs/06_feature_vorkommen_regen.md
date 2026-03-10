# Feature: Vorkommenseffektivität, Bodenschätze & Regen

## Source (FAQ 3.2.2, 3.2.8, seed_gebaeude.py vorkommeneffektivitaet/regenabhaengig)
- vorkommeneffektivitaet: resource deposit multiplier for specific terrain
  e.g. Tongrube: Ton=100 (only works where Ton deposit found)
- regenabhaengig: building (e.g. Auffangbecken) only produces when it rains
- Bodenschätze (resource deposits): hidden, require Geologen search (costs money)
  - search possible only if techlevel >= resource.techlevel AND deposit type exists in terrain
  - one search per resource type per province; if not found → never available
- Terrain has Bodenfeuchtigkeit (moisture): rains → +moisture, drains 10%/day
- moisture > average → terrain upvalue over time; < average → downvalue
- Upgrade path: Wüste→Ödland→Steppe→Grasland→Wald→Sumpf etc.

## Data Models
```python
ProvinceDeposit: province_id, resource_id, found(bool), searched(bool)
ProvinceClimate: province_id, bodenfeuchtigkeit(0-100), grundwasserspiegel(0-100),
                 rain_probability, last_rained
TerrainUpgradeChain: {terrain_id: next_terrain_id}  # upgrade path
```

## Core Logic (per 24h tick)
```
RAIN CHECK:
  if random() < terrain.rain_probability:
    bodenfeuchtigkeit += terrain.rain_amount
    if regenabhaengig buildings: production *= 1 (active)
  else:
    if regenabhaengig buildings: production *= 0 (no output)
  bodenfeuchtigkeit -= bodenfeuchtigkeit * 0.10  # daily drain

VORKOMMENS PRODUCTION MODIFIER:
  base_production = template.produktion[resource] * terraineffektivitaet/100
  if template.vorkommeneffektivitaet[resource]: 
    require ProvinceDeposit.found == True else production = 0
    apply deposit_quality multiplier

TERRAIN CHANGE CHECK (every 24h):
  avg = terrain.average_moisture
  if bodenfeuchtigkeit > avg * 1.2 for >7 days: trigger TERRAIN_UPVALUE event
  if bodenfeuchtigkeit < avg * 0.8 for >7 days: trigger TERRAIN_DOWNVALUE event

GRUNDWASSER:
  grundwasserspiegel += rain_infiltration (10% of rain)
  if brunnen.active: grundwasserspiegel -= brunnen.consumption
  if grundwasserspiegel <= 0: brunnen production = 0 + warn
```

## Endpoints
```
GET  /province/{id}/climate → bodenfeuchtigkeit, grundwasser, rain_forecast
POST /province/{id}/irrigate {"water_amount": float}  # raises bodenfeuchtigkeit
GET  /province/{id}/deposits → known deposits + searchable types
POST /province/{id}/deposits/search {"resource_id": int}  # costs money
```
