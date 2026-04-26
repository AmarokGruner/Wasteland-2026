# Feature: Marktplatz-Detail & Spieler-Handel

## Source (FAQ 4.x, 3.1.6, 7.1, 7.5)
- Marktplatz gives marktpunkte (e.g. 25 from seed)
- Per marktpunkt: 1 good can be sold to population
- Market buys 5-day supply upfront at 150% Staatswert from lager
- Categories split proportionally by stand count (2 Milch + 1 Wasser = 6.7/3.3)
- Staatswert drops to 50% floor when resource is abundant
- Kontor required for player-to-player trade
- Handelskonto funded separately; player trade routes use Handelskarren
- Only citizens aged 20-25 can form trade routes leaving province

## Implementation Status: ✓ IMPLEMENTED (2026-03-15)

### Changes Made
1. **Market Logic** (`app/market_logic.py`):
   - `get_market_preview()`: Demand calculation per category
   - `process_market_tick()`: Auto-buy 5-day supply at 150% Staatswert

2. **API Endpoints** (`app/api/market.py`):
   - GET `/province/{id}/market/stands`
   - POST `/province/{id}/market/stands`
   - DELETE `/province/{id}/market/stands/{resource_id}`
   - GET `/province/{id}/market/preview`

3. **Kontor Integration** (see Feature 16):
   - POST `/province/{id}/kontor/prices`
   - GET `/province/{id}/kontor/balance`

## Data Models
```python
MarketStand (app/models.py):
  - id, province_id, resource_id, auto_buy(int)

KontorPrice (app/models.py):
  - id, province_id, resource_id
  - mode: String ("buy"/"sell") 
  - price: Float
  - friends_only(int), verbündete_only(int), active(int)
```

## Market Logic (Implemented in app/market_logic.py)
```
GET_MARKET_PREVIEW:
  demand_nahrung = population * 0.1
  demand_getraenk = population * 0.05
  
  for each category:
    total_stands = sum(stands[resource] for resource in category)
    
  returns {demand, suggested_stand_count, potential_revenue}

PROCESS_MARKET_TICK:
  for each active MarketStand:
    resource_demand = demand_per_category * stand_ratio
    buy_amount = min(resource_demand * 5, lager[resource])
    
    if buy_amount > 0:
      price = staatswert * 1.5
      lager[resource] -= buy_amount
      provinzkonto += buy_amount * price  
      volkskonto -= buy_amount * price
```

## Endpoints (Implemented)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/province/{id}/market/stands` | GET | Current stands + stats |
| `/province/{id}/market/stands` | POST | Create new stand |
| `/province/{id}/market/stands/{resource_id}` | DELETE | Remove stand |
| `/province/{id}/market/preview` | GET | Demand forecast |

## Validation
- Stand creation requires available marktpunkte (marktpunkte > used_stands)
- Cannot create duplicate stand for same resource
- Auto-buy enabled by default on stand creation
