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

## Implementation Status: ✓ IMPLEMENTED (2026-03-15)

### Changes Made
1. **Model Extensions** (`app/models.py`):
   - `Province`: +provinzkonto, +volkskonto, +handelskonto (lines 60-62)
   - `Player`: +staatskonto (line 18)
   - `TaxSettings` model (lines 217-228)

2. **Finance Logic** (`app/finance_logic.py`):
   - `get_finance_overview()`: Returns all 4 account balances + PKV calculation
   - `transfer_money()`: Supports transfer to handelskonto/staatskonto
   - `process_tax_tick()`: Tax collection with Bank bonus (+20%)
   - `process_wages_tick()`: Wage/sold distribution

3. **API Endpoints** (`app/api/province.py`):
   - GET `/province/{id}/finance` → finance overview
   - POST `/province/{id}/tax-settings` → update rates
   - POST `/province/{id}/finance/transfer` → transfer funds

## Data Models
```python
Province (app/models.py):
  - provinzkonto: Column(Float, default=0.0)
  - volkskonto: Column(Float, default=0.0) 
  - handelskonto: Column(Float, default=0.0)

Player (app/models.py):
  - staatskonto: Column(Float, default=0.0)

TaxSettings (app/models.py):
  - tax_rate: Column(Integer, default=10)
  - lohn_rate: Column(Float, default=1.0)
  - sold_rate: Column(Float, default=1.0)
  - rente_rate: Column(Float, default=0.5)
  - state_transfer_pct: Column(Integer, default=0)
```

## Core Logic (Implemented in app/finance_logic.py)
```
GET_FINANCE_OVERVIEW:
  pkv = (provinzkonto + volkskonto) / max(population, 1)
  returns {provinzkonto, volkskonto, handelskonto, staatskonto, pkv}

TRANSFER_MONEY (handelskonto):
  valid targets: ["provinzkonto", "volkskonto", "handelskonto", "staatskonto"]
  if from="provinzkonto" to="handelskonto": province.handelskonto += amount

TAX COLLECTION (process_tax_tick):
  requires Steueramt building
  steuer = volkskonto * tax_rate/100  
  if pkv < 0: steuer = 0, warn "PKV_NEGATIVE"
  bonus = 1.2 if has_Bank else 1.0
  provinzkonto += steuer * bonus

STATE TRANSFER:
  if state_transfer_pct > 0: 
    player.staatskonto += province.provinzkonto * state_transfer_pct/100
```

## Endpoints (Implemented)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/province/{id}/finance` | GET | All 4 account balances + PKV |
| `/province/{id}/tax-settings` | POST | Update tax_rate, lohn_rate, etc. |
| `/province/{id}/finance/transfer` | POST | Transfer between accounts |

## Validation
- Tax collection blocked if PKV negative (volk cannot pay)
- Bank building provides +20% tax income bonus
- Transfer validation: sufficient source balance required
