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

## Data Models
```python
MarketStand: province_id, resource_id, auto_buy(bool)
TradeRoute: id, owner_id, origin_province, destination, cargo{dict}, 
            settlers_count, status("traveling"/"arrived"/"returning")
KontorPrice: province_id, resource_id, buy_price, sell_price, friends_only(bool)
```

## Market Logic (per 24h tick)
```
DEMAND CALCULATION:
  demand_per_category = population * consumption_rate[category]

STAND SPLIT:
  for each category: 
    total_stands = sum(stands for resource in category)
    per_resource_sold = demand * (stands[resource] / total_stands)

MARKET BUY (pre-purchase):
  market_stock[resource] += min(demand*5, lager[resource]) 
  lager[resource] -= purchased
  provinzkonto += purchased * staatswert * 1.5
  volkskonto -= purchased * staatswert * 1.5

STAATSWERT FLOOR:
  if supply_ratio >= 1.0: staatswert = base_value * 0.5 (minimum)
```

## Endpoints
```
GET  /province/{id}/market/stands → current stands + stats
POST /province/{id}/market/stands {"resource_id":int, "auto_buy":bool}
DELETE /province/{id}/market/stands/{resource_id} → dissolve (160% buyback)
GET  /province/{id}/market/preview → demand forecast, suggested stands
POST /province/{id}/kontor/prices → set buy/sell prices
POST /province/{id}/trade-route/create {"destination":int, "cargo":{}, "settlers":int}
```
