# Feature: Siedler & Kolonisierung

## Source (FAQ 3.1.1, 4.3, seed_einheiten.py id=21)
- Siedler (id=21): Zivilist, geschwindigkeit=1.0, fortbewegung=Boden
- Only citizens tick_age 4-5 (age 20-25) can become Siedler
- Siedler travels to empty/own-culture province → claims it
- New province: no Bunker, starts with basic terrain, optional pre-seeded Ruinen
- Provinzübergabe: transfer owned province to another player

## Data Models
```python
# Reuses ProvinceUnit + TradeRoute structure from feature_15
SiedlerExpedition: id, owner_id, origin_province_id, destination_province_id,
                   settler_count, karren_count, cargo{dict},
                   status("preparing"/"traveling"/"arrived"/"colonizing"),
                   travel_ticks_remaining

Province: ..., owner_id, kultureinfluss_owner_id  # annex bonus if own culture
```

## Core Logic
```
CREATE EXPEDITION:
  require eligible_settlers (tick_age 4-5) >= settler_count
  require destination.owner_id IS NULL  # unowned
  OR destination.kultureinfluss_owner_id == player_id  # own culture bonus
  deduct settlers from PopulationCohort
  load cargo (founding resources: Bauholz, Stein, Notrationen min amounts)
  travel_ticks = distance(origin, destination) / siedler.geschwindigkeit

ARRIVAL & COLONIZATION:
  if destination.owner_id IS NULL:
    create Province(owner=player, terrain=destination.terrain)
    place founding cargo into new lager
    seed pre-existing Ruinen buildings (baubar=0, from world gen)
    → GameLog: "PROVINCE_COLONIZED: {name}"
  else: reject "PROVINCE_OCCUPIED"

KULTURBONUS:
  if destination.kultureinfluss_owner_id == player_id:
    founding_cargo_cost *= 0.8  # 20% cheaper to settle own culture hex

PROVINZÜBERGABE:
  require both players consent (request + accept flow)
  transfer province.owner_id
  Bunker auto-destroyed on transfer (not transferable)
  → GameLog: "PROVINCE_TRANSFERRED: {from} → {to}"
```

## Endpoints
```
POST /expedition/create
     Body: {destination_province_id, settler_count, karren_count, cargo{}}
GET  /expedition/{id}/status → travel progress, ETA
POST /world/provinces/{id}/transfer {"target_player_id": int}  # request
POST /world/provinces/{id}/transfer/accept {"expedition_id": int}  # confirm
GET  /world/provinces/colonizable → unowned provinces + kultur bonus flag
```

## Validation
- settler_count requires tick_age 4-5 cohort availability
- Destination must be unowned OR own-culture
- Minimum founding cargo enforced (prevent instant-starve colony)
- Bunker province transfer: bunker destroyed automatically
