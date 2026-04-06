# Feature: Bunker-Mechanik & Startprovinz

## Source (FAQ 3.1.1, 2.2)
- Bunker: unique start building, opened once per empty province globally
- Gives techproduktion +2 (spezialeigenschaft)
- Cannot be built by player – only "opened" to claim province
- Destroyed automatically if province is conquered (not transferable)
- Bunkerprovinz harder to conquer (defense bonus)
- First province always has Bunker; colonized provinces do NOT

## Data Models
```python
Province: ..., has_bunker(bool), is_bunker_province(bool),
          bunker_defense_bonus(int)  # applied in combat

BuildingInstance: ...  # Bunker pre-seeded with baubar=0 (Vorgabe type)
```

## Core Logic
```
PROVINCE CLAIM (open bunker):
  require target_province.owner_id IS NULL
  require no other bunker opened by same player on this map (1 per player)
  create Province for player
  place Bunker building (baubar=0, indestructible, unique)
  set is_bunker_province = True
  set techproduktion += 2

BUNKER IN COMBAT:
  if province.is_bunker_province:
    defense_multiplier *= 1.3  # harder to conquer (30% bonus)

ON CONQUEST:
  if conquered_province.has_bunker:
    BuildingInstance(Bunker).destroy()  # auto-demolished
    province.has_bunker = False
    province.is_bunker_province = False
    province.techproduktion -= 2

COLONIZATION (new province, no bunker):
  require Siedler unit arrives at empty province
  create Province (no bunker)
  seed with basic terrain buildings if any pre-exist (Ruinen)

TECH PRODUCTION (in roundlogic):
  tech_points += sum(building.spezialeigenschaften.techproduktion)
  # Bunker contributes 2, Feuerstelle 1, Ruine-Laboratorium 2
```

## Endpoints
```
POST /world/claim {"province_id": int}  # open bunker, claim empty province
GET  /province/{id}/bunker → {has_bunker, defense_bonus, tech_contribution}
```

## Validation
- One bunker per player per world map
- Target province must be unowned
- Cannot manually demolish Bunker (indestructible)
- Conquest auto-triggers bunker destruction
