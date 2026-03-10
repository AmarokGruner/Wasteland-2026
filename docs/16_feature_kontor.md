# Feature: Kontor & Spieler-Handel Detail

## Source (FAQ 4.4, 4.5, 4.1)
- Kontor required for player-to-player trade in own province
- Preise festlegen: buy/sell price per resource, optional friends-only flag
- Same resource can be listed multiple times (tiered pricing for different diplomacy levels)
- Handelskonto must be funded to purchase incoming goods
- Staatswert: volk pays +50% of own staatswert; optimal buy price = own staatswert
- Selling: andere Spieler only buy if they profit reselling to their own volk
- Kontor also enables % transfer of daily income to Staatskonto

## Data Models
```python
KontorPrice: id, province_id, resource_id, mode("buy"/"sell"), price,
             friends_only(bool), verbündete_only(bool), active(bool)
# Multiple rows per resource for tiered pricing

ProvinceFinance: ..., handelskonto(float)
```

## Core Logic
```
PRICE VISIBILITY (per visiting trade route):
  if KontorPrice.friends_only AND visitor NOT in player.freunde: hide
  if KontorPrice.verbündete_only AND visitor NOT verbündeter: hide
  else: show price

SELL TO VISITOR:
  if lager[resource] >= amount AND price agreed:
    lager[resource] -= amount
    handelskonto += amount * price
    visitor.cargo[resource] += amount

BUY FROM VISITOR:
  if handelskonto >= amount * price:
    handelskonto -= amount * price
    lager[resource] += amount
    visitor.cargo[resource] -= amount

STAATSWERT CONTEXT:
  optimal_sell_price = visitor.staatswert[resource]
  profit_margin = (visitor.staatswert * 1.5 - our_price) / our_price * 100
  → show in price preview: "Visitor profit: +X%"

HANDELSKONTO FUND:
  POST /province/{id}/finance/transfer {"to":"handelskonto", "amount":float}
```

## Endpoints
```
GET  /province/{id}/kontor/prices → all listings + visitor profit estimate
POST /province/{id}/kontor/prices
     Body: {resource_id, mode, price, friends_only, verbündete_only}
DELETE /province/{id}/kontor/prices/{price_id}
GET  /province/{id}/kontor/balance → handelskonto balance
POST /province/{id}/kontor/trade   # executed by visiting trade route
     Body: {route_id, transactions:[{resource_id, mode, amount}]}
```

## Validation
- Requires Kontor building in province
- Buy: handelskonto >= total_cost else "INSUFFICIENT_HANDELSKONTO"
- Sell: lager[resource] >= amount else "INSUFFICIENT_STOCK"
- Enemy players (diplomacy=Feind/Unerwünscht): all trade blocked
