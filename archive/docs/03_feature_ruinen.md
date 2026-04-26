# Feature: Ruinen-Logik

## Source (FAQ 2.2, seed_gebaeude.py bautyp=Vorgabe)
- Ruin buildings: `baubar=0`, pre-placed on province map (not player-built)
- Province type (R) on map = abandoned province with pre-existing buildings
- Ruins have production but need repair (rohstoffbedarfbau = repair cost)
- Examples from seed: Ruine-Pumpstation (100 Wasser/24h), Ruine-Lageraum (25000 lager),
  Ruine-Festung (ausbildung+2, sicherheit+30), Ruine-Fabrik (20 Handelsgüter/24h)
- Ruin buildings CAN produce immediately if workers assigned
- Repair = pay rohstoffbedarfbau → building becomes fully functional + upgradable (if applicable)

## Data Models
```python
BuildingInstance: ..., is_ruin(bool), is_repaired(bool)
# Ruins placed via admin seed or province generation
```

## Core Logic
```
RUIN PRODUCTION:
  if is_ruin AND NOT is_repaired: produce at 50% efficiency (workers can still staff)
  if is_ruin AND is_repaired: produce at 100%, treated as normal building

REPAIR:
  require resources >= rohstoffbedarfbau (from template)
  require player.mips >= baukostenmips
  deduct resources + mips → set is_repaired=True

DEMOLISH RUIN:
  refund 25% rohstoffbedarfbau (lower than normal 50% for ruins)
  free field slot
```

## Endpoints
```
GET  /province/{id}/ruins → list of ruin buildings + repair cost
POST /province/{id}/ruins/{instance_id}/repair → deduct costs, set repaired
POST /province/{id}/ruins/{instance_id}/demolish → partial refund, free field
```

## Validation
- Only owner can repair ruins in their province
- Repair requires tech_level >= template.techlevel
- Cannot upgrade ruin until repaired
