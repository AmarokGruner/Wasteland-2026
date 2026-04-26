# Feature: Kontor & Spieler-Handel Detail

## Source (FAQ 4.4, 4.5, 4.1)
- Kontor required for player-to-player trade in own province
- Preise festlegen: buy/sell price per resource, optional friends-only flag
- Same resource can be listed multiple times (tiered pricing for different diplomacy levels)
- Handelskonto must be funded to purchase incoming goods
- Staatswert: volk pays +50% of own staatswert; optimal buy price = own staatswert
- Selling: andere Spieler only buy if they profit reselling to their own volk
- Kontor also enables % transfer of daily income to Staatskonto

## Implementation Status: ✓ IMPLEMENTED (2026-03-15)

### Changes Made
1. **Model Extension** (`app/models.py:305-320`):
   - KontorPrice now has: `mode`, `price`, `friends_only`, `verbündete_only`, `active`

2. **API Endpoints** (`app/api/market.py`):
   - GET `/province/{id}/kontor/prices`
   - POST `/province/{id}/kontor/prices`
   - DELETE `/province/{id}/kontor/prices/{price_id}`
   - GET `/province/{id}/kontor/balance`
   - POST `/province/{id}/kontor/trade`

3. **Trade Execution** (`app/api/market.py:249-397`):
   - Validates Kontor building exists
   - Executes buy/sell transactions with validation

## Data Models
```python
KontorPrice (app/models.py):
  - id: Column(Integer, primary_key=True)
  - province_id: FK(Province)
  - resource_id: FK(Resource)  
  - mode: Column(String) # "buy" or "sell"
  - price: Column(Float)
  - friends_only: Column(Integer, default=0)
  - verbündete_only: Column(Integer, default=0)  
  - active: Column(Integer, default=1)

Province (app/models.py):
  - handelskonto: Column(Float, default=0.0)
```

## Core Logic (Implemented in app/api/market.py)
```
GET_KONTOR_PRICES:
  returns all active prices with visibility filter
  - friends_only: hides from non-friends (future: check player.freunde)
  - verbündete_only: hides from non-verbündete (future: diplomacy check)

SET_KONTOR_PRICES:
  - creates new price entry or updates existing
  - validates mode is "buy" or "sell"
  - sets friends_only/verbündete_only flags

EXECUTE_KONTOR_TRADE (mode="sell"):
  - validates kontor building exists
  - checks lager[resource] >= amount (INSUFFICIENT_STOCK)
  - lager -= amount, handelskonto += amount * price
  - visitor cargo += amount

EXECUTE_KONTOR_TRADE (mode="buy"):
  - validates handelskonto >= total_cost (INSUFFICIENT_HANDELSKONTO)
  - validates visitor has enough cargo
  - handelskonto -= amount * price, lager += amount

HANDELSKONTO FUNDING:
  - POST /province/{id}/finance/transfer {"to":"handelskonto", "amount":float}
  - handled by finance_logic.transfer_money()
```

## Endpoints (Implemented)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/province/{id}/kontor/prices` | GET | All listings + visibility |
| `/province/{id}/kontor/prices` | POST | Set price for resource |
| `/province/{id}/kontor/prices/{price_id}` | DELETE | Soft-delete price |
| `/province/{id}/kontor/balance` | GET | Handelskonto balance |
| `/province/{id}/kontor/trade` | POST | Execute trade |

## Request/Response Examples
```python
# POST /province/{id}/kontor/prices
{
  "resource_id": 1,
  "mode": "sell",     # or "buy"
  "price": 10.0,
  "friends_only": False,
  "verbündete_only": False
}

# POST /province/{id}/kontor/trade  
{
  "route_id": 5,
  "transactions": [
    {"resource_id": 1, "mode": "sell", "amount": 50},
    {"resource_id": 2, "mode": "buy", "amount": 25}
  ]
}
```

## Validation Errors
| Error | Cause |
|-------|-------|
| KONTOR_REQUIRED | No Kontor building in province |
| INSUFFICIENT_STOCK | Not enough resources in lager (sell mode) |
| INSUFFICIENT_HANDELSKONTO | Not enough funds (buy mode) |
| PRICE_NOT_FOUND | No active price for resource/mode |
| INSUFFICIENT_CARGO | Visitor doesn't have enough of resource |

## Notes
- Price visibility filtering is simplified (placeholder for friends/verbündete check)
- Requires Building "Kontor" in province to enable trading
- Handelskonto must be funded before buying from visitors
