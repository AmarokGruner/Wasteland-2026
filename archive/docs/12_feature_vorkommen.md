# Feature: Bodenschätze & Vorkommen

## Source (seed_vorkommen-2.py)
- Vorkommen: id, name, typ(geologisch/Oberfläche/unt.Seen), tech, suchkosten, findwahrscheinlichkeit{terrain:pct}
- Search costs MIPS (suchkosten from seed), requires player.tech_level >= vorkommen.tech
- findwahrscheinlichkeit = % chance of finding per terrain type (0-100)
- If terrain not in findwahrscheinlichkeit → cannot search at all
- One search per vorkommen per province; if not found → permanent (no retry unless Grundwasser special rule)
- Wasser exception: can retry after Grundwasserspiegel recovers

## Data Models
```python
Vorkommen: id, name, typ, tech, suchkosten, findwahrscheinlichkeit(JSON)  # from seed
ProvinceDeposit: province_id, vorkommen_id, searched(bool), found(bool), quality(1-3)
# quality 1=50% yield, 2=100%, 3=150% — rolled on discovery
```

## Core Logic
```
CAN_SEARCH(province_id, vorkommen_id):
  vorkommen = lookup(vorkommen_id)
  if player.tech_level < vorkommen.tech: reject "TECH_TOO_LOW"
  if deposit.searched: reject "ALREADY_SEARCHED"
  prob = vorkommen.findwahrscheinlichkeit.get(province.terrain_name)
  if prob is None: reject "NOT_POSSIBLE_IN_TERRAIN"
  if province.mips_available < vorkommen.suchkosten: reject "INSUFFICIENT_MIPS"

SEARCH(province_id, vorkommen_id):
  CAN_SEARCH() checks
  deduct vorkommen.suchkosten from provinzkonto
  deposit.searched = True
  roll = random(1, 100)
  if roll <= prob:
    deposit.found = True
    deposit.quality = random.choices([1,2,3], weights=[0.4, 0.4, 0.2])[0]
    → trigger GameLog: "DEPOSIT_FOUND: {name}"
  else:
    deposit.found = False
    → trigger GameLog: "DEPOSIT_NOT_FOUND: {name}"

PRODUCTION MODIFIER (in roundlogic):
  if building.vorkommeneffektivitaet[resource]:
    if not deposit.found: production = 0
    else: production *= deposit.quality_multiplier[quality]
    # quality_multiplier = {1: 0.5, 2: 1.0, 3: 1.5}

WASSER SPECIAL RULE:
  if vorkommen.name == "Wasser" AND grundwasserspiegel recovered AND deposit.found==False:
    deposit.searched = False  # allow retry
```

## Endpoints
```
GET  /province/{id}/deposits → [{vorkommen_id, name, searched, found, quality, can_search}]
POST /province/{id}/deposits/search {"vorkommen_id": int}
     → {"found": bool, "quality": int, "cost": int}
GET  /province/{id}/deposits/searchable → filtered list: tech ok + terrain match + not yet searched
```

## Validation
- reject if deposit.searched == True (except Wasser retry rule)
- reject if terrain not in findwahrscheinlichkeit
- deduct cost atomically with search result
