# Feature: Steuer-System & Geldlogik

## Source (FAQ 2.5, 3.1.3, 3.1.4, 7.2, 7.4)
- 4 accounts per province: Provinzkonto, Volkskonto, Handelskonto, Staatskonto
- Steuern active only AFTER Steueramt is built
- Tax change → immediate moral impact (increase lowers moral MORE than decrease raises it)
- Volk pays: taxes + market purchases → Volk loses money
- Volk earns: wages (Lohn), Sold (military pay), Kindergeld, Rentenzahlungen
- PKV (Pro-Kopf-Vermögen): if negative → volk cannot pay taxes
- Bank (+20% tax income): enables direct transfer to Staatskonto
- Münzerei: consumes 0.05 Kupfer/24h → produces 1500 MIPS/24h
- Steueramt: enables Gewerbepunkte (fresh capital production)
- Building costs → money goes TO Volkskonto

## Data Models
```python
ProvinceFinance: province_id, provinzkonto, volkskonto, handelskonto
StateFinance: player_id, staatskonto
TaxSettings: province_id, tax_rate(0-100), lohn_rate, sold_rate, rente_rate, state_transfer_pct
```

## Core Logic (per 24h tick)
```
MIPS PRODUCTION:
  for each Münzerei: consume 0.05 Kupfer → +1500 provinzkonto

TAX COLLECTION (requires Steueramt):
  steuer = volkskonto * tax_rate/100
  if volkskonto < 0: steuer = 0 (warn: "PKV_NEGATIVE")
  provinzkonto += steuer * (1.2 if has_Bank else 1.0)
  volkskonto -= steuer

WAGES/SOLD (requires Steueramt):
  wages = sum(building.arbeiter) * lohn_rate
  sold = units.count * sold_rate
  provinzkonto -= wages + sold
  volkskonto += wages + sold

TAX MORAL IMPACT:
  on tax_rate change: delta = new - old
  if delta > 0: moral -= delta * 1.5   # increase hurts more
  if delta < 0: moral += abs(delta) * 1.0

STATE TRANSFER (requires Bank OR Steueramt %):
  if state_transfer_pct > 0: staatskonto += provinzkonto * state_transfer_pct/100
```

## Endpoints
```
GET  /province/{id}/finance → all 4 account balances + PKV
POST /province/{id}/tax-settings → update tax/wage rates
POST /province/{id}/finance/transfer {"amount":float, "to":"staatskonto"/"handelskonto"}
```
