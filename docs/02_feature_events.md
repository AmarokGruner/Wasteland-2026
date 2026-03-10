# Feature: Events System

## Source (FAQ 1.2, 2.4, 8.x)
- Events fire every 24h tick (not every spool)
- Types: animal attacks (Fleischfresser attack when starving), disease, drought/terrain change, random finds
- Animal attacks: only if animals are starving in province; Pflanzenfresser eat fields instead
- Revolution: moral == 0 triggers revolt (see moral logic)
- Gefangenschaft: being captured → all provinces get moral malus

## Event Types
```python
EventType: ANIMAL_ATTACK | DISEASE_OUTBREAK | DROUGHT_WARNING |
           TERRAIN_UPVALUE | TERRAIN_DOWNVALUE | REVOLT | RANDOM_FIND |
           POPULATION_BORN | POPULATION_DIED
```

## Data Models
```python
ProvinceEvent: id, province_id, event_type, payload(JSON), triggered_at, resolved
GameLog: id, event_id, message(DE), visible_to(player/all/admin)
```

## Core Logic (per 24h tick)
```
REVOLT check: if moral <= 0 → trigger REVOLT, population -= random(5-20%)
ANIMAL_ATTACK: if animals.count > 0 AND animal.food_supply < threshold → attack
DISEASE: if gesundheit < 20 → random outbreak, population -= small %
DROUGHT_WARNING: if bodenfeuchtigkeit < average - threshold → warn + potential terrain change
RANDOM_FIND: small probability per tick, adds unknown resource to lager
POPULATION_BORN/DIED: every 24h, calc births (Bildung-adjusted) + deaths (health-adjusted)
```

## Preview Warnings (GET /province/{id}/preview)
```json
"events": [
  {"type": "REVOLT_RISK", "detail": "Moral at 12 – revolt in ~2 days"},
  {"type": "DROUGHT_WARNING", "detail": "Terrain downgrade possible in 48h"}
]
```

## Endpoints
```
GET  /province/{id}/events?last=10 → recent gamelog entries
GET  /province/{id}/events/preview → predicted events next 48h
POST /admin/events/trigger {"province_id":int, "type":str}  # admin override
```
