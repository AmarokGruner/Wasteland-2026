# Feature: Handelskarren & Handelsrouten

## Source (seed_einheiten.py id=2/34, FAQ 4.3)
Handelskarren (id=2): geschwindigkeit=0.5, transport_land=100, module=[Siedler+Handelskarren]
Siedler (id=21): geschwindigkeit=1.0, einheitengroesse=1
- Only citizens aged 20-25 (tick_age 4-5) can leave province as Siedler
- Each player starts with 2 Handelskarren (can acquire more via trade/production)
- Route: create unit → assign karren → load cargo → depart → travel → arrive → trade → return
- Travel time based on map distance × (1/geschwindigkeit) per province hop
- Karren can be upgraded with Pferde → geschwindigkeit bonus

## Data Models
```python
EinheitenTyp: id, name, geschwindigkeit, transport_land, module(JSON)  # from seed

ProvinceUnit: id, province_id, einheiten_typ_id, count, status,
              cargo{dict}, route_id, current_location_province_id

TradeRoute: id, owner_province_id, destination_province_id, 
            cargo_outbound{dict}, cargo_return{dict},
            status("loading"/"traveling"/"arrived"/"returning"/"home"),
            travel_ticks_remaining, settler_count, karren_count
```

## Core Logic
```
CREATE ROUTE:
  require eligible_settlers (tick_age 4-5) >= settler_count
  require karren_available >= karren_count
  require cargo_outbound resources in lager
  deduct cargo + settlers from province
  set travel_ticks = distance(origin, destination) / geschwindigkeit

TRAVEL (per 24h tick):
  travel_ticks_remaining -= 1
  if travel_ticks_remaining <= 0: status = "arrived"
  → GameLog: "ROUTE_ARRIVED: {destination}"

TRADING AT DESTINATION (when status="arrived"):
  auto-execute if KontorPrice matches available resources
  OR player manually selects trade at destination province
  load cargo_return
  status = "returning", travel_ticks = same as outbound

RETURN (per 24h tick):
  travel_ticks_remaining -= 1
  if 0: status = "home"
  deposit cargo_return into lager
  settlers return to PopulationCohort (tick_age preserved)
  → GameLog: "ROUTE_RETURNED: {cargo_summary}"

PFERDE UPGRADE:
  if unit has Pferde module: geschwindigkeit *= 2.0
```

## Endpoints
```
GET  /province/{id}/units → all units + routes + status
POST /province/{id}/trade-route/create
     Body: {destination_id, cargo_outbound{}, settler_count, karren_count}
POST /province/{id}/trade-route/{route_id}/load {"cargo": {}}
POST /province/{id}/trade-route/{route_id}/depart
GET  /province/{id}/trade-route/{route_id}/status
POST /province/{id}/trade-route/{route_id}/trade  # manual trade at destination
```

## Validation
- settler_count requires eligible citizens (tick_age 4-5) in PopulationCohort
- karren_count <= player.karren_available
- cargo weight <= karren_count * transport_land(100)
- Cannot depart if destination province is enemy (diplomacy check)
- "NO_ELIGIBLE_SETTLERS" if no 20-25 age cohort available
