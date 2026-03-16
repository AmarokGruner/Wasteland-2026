# Feature: Handelskarren & Handelsrouten

## Source (seed_einheiten.py id=2/34, FAQ 4.3)
Handelskarren (id=2): geschwindigkeit=0.5, transport_land=100, module=[Siedler+Handelskarren]
Siedler (id=21): geschwindigkeit=1.0, einheitengroesse=1
- Only citizens aged 20-25 (tick_age 4-5) can leave province as Siedler
- Each player starts with 2 Handelskarren (can acquire more via trade/production)
- Route: create unit → assign karren → load cargo → depart → travel → arrive → trade → return
- Travel time based on map distance × (1/geschwindigkeit) per province hop
- Karren can be upgraded with Pferde → geschwindigkeit bonus

## Implementation Status: ✓ IMPLEMENTED (2026-03-15)

### Changes Made
1. **Trade Route Logic** (`app/trade_route_logic.py`):
   - `create_trade_route()`: Validates settlers, karren, capacity
   - `depart_route()`: Sets status to traveling, calculates travel time
   - `execute_trade_at_destination()`: Handles cargo_return loading
   - Returns settlers to PopulationCohort on homecoming

2. **API Endpoints** (`app/api/province.py:653-804`):
   - GET `/province/{id}/units` → all units + routes
   - POST `/province/{id}/trade-route/create`
   - POST `/province/{id}/trade-route/{route_id}/load`
   - POST `/province/{id}/trade-route/{route_id}/depart`
   - GET `/province/{id}/trade-route/{route_id}/status`
   - POST `/province/{id}/trade-route/{route_id}/trade`

3. **Tick Processing** (`app/tick_logic.py:105-110`):
   - `process_trade_routes()` called every tick

## Data Models
```python
TradeRoute (app/models.py):
  - id: Column(Integer, primary_key=True)
  - owner_province_id: FK to Province
  - destination_province_id: FK to Province  
  - cargo_json: Column(String) # {resource_id: amount}
  - status: String ("loading"/"traveling"/"arrived"/"returning"/"home")
  - travel_ticks_remaining: Integer
  - settler_count: Integer

ProvinceUnit (app/models.py):
  - province_id, einheiten_typ_id, count, status
  - cargo_json: Column(String) # {resource_id: amount}
```

## Core Logic (Implemented in app/trade_route_logic.py)
```
CREATE_ROUTE:
  - validate eligible settlers (tick_age 4-5) >= settler_count
  - validate karren available >= karren_count  
  - validate cargo fits in capacity (karren_count * transport_land)
  - deduct cargo from lager, settlers from PopulationCohort
  - calculate travel_ticks = distance / geschwindigkeit

TRAVEL (process_trade_routes):
  for routes with status="traveling":
    travel_ticks_remaining -= 1
    if <= 0: status = "arrived", log event

TRADING AT DESTINATION:
  execute_trade_at_destination():
    - load cargo_return from destination lager
    - status = "returning"

RETURN:
  travel_ticks_remaining -= 1  
  if <= 0: status = "home"
    - deposit cargo_return to origin lager
    - return settlers to PopulationCohort
```

## Endpoints (Implemented)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/province/{id}/units` | GET | All units + routes |
| `/province/{id}/trade-route/create` | POST | Create new route |
| `/province/{id}/trade-route/{route_id}/load` | POST | Load cargo |
| `/province/{id}/trade-route/{route_id}/depart` | POST | Depart route |
| `/province/{id}/trade-route/{route_id}/status` | GET | Route status |
| `/province/{id}/trade-route/{route_id}/trade` | POST | Trade at destination |

## Validation Errors
| Error | Cause |
|-------|-------|
| NO_ELIGIBLE_SETTLERS | No citizens aged 20-25 available |
| Not enough Handelskarren | Insufficient karren units in province |
| Cargo exceeds capacity | weight > total transport capacity |
