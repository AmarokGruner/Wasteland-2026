# Wastelands Round Logic System - Complete FastAPI/Python Implementation

## Objective
Complete round-based system for browser RTS game. Province preview + time spooling via time credits (max 240h). All production/consumption rates are **per 24h base**, scale linearly: `(hours/24)`.

## Core Data Models (Assume DB Schema)
```python
Province: id, terrain_id, population, mips(workers), resources(dict), 
  wohnraum_total, lagerkapazitaet_total, moral(0-100), gesundheit(0-100), 
  marktpunkte, strassennetz(wegstufe_sum), einheiten_count

Player: id, time_credit(≤240), tech_level

BuildingInstance: province_id, gebaeude_id, level

Gebaeude: id, produktion(dict), rohstoffverbrauch(dict), arbeiter, 
  terraineffektivitaet(dict), spezialeigenschaften(dict), wohnraum, lagerkapazitaet

Ressource: id, name, typ(Getränk/Nahrung/Verbrauchsgut/Genussgut/Medizin/Luxusgut), wert, verbrauch

## Core Spool Logic (hours)

1. VALIDATE: hours ≤ time_credit ∧ all(resources ≥ 0) ∧ population ≥ 0

2. BUILDING EFFICIENCY (per building):
   terrain_eff = gebaeude.terraineffektivitaet[terrain_id] / 100
   worker_factor = min(1, province.mips / total_required_workers)
   effective_rate_per_24h = terrain_eff × worker_factor × base_rate

3. PRODUCTION/CONSUMPTION (hours/24 × effective_rate):
   - CONSUME first: scale by min(available/required, 1)
   - PRODUCE: reject if lagerkapazitaet_total exceeded

4. POPULATION SUPPLY (parallel to buildings):
   BASE NEED: 0.5 Nahrung + 0.5 Getränk per (population + einheiten_count) per 24h
   MARKET (if marktpunkte > 0): 1 good per marktpunkt sold at 150% wert
     Split demand proportionally: [2 Milk + 1 Water stands = 6.7/3.3 split]

5. MORAL/HEALTH Update (every 24h tick):
   MORAL = taxes + 4_basics(Nahrung+Trinken+Sicherheit+Wohnraum) 
         +1/Verbrauchsgut +2.5/Genussgut(health_malus) +1-2/Luxusgut
   HEALTH = wohnraum_ratio + strassennetz + food/drink_variety + Medizin 
          - Genussgut_malus

6. WARNINGS (Preview only): 
   "HUNGER_IN_XH" if <0.5 food/drink supply within ≤48h

7. COMMIT: time_credit -= hours, atomic DB transaction

## FastAPI Endpoints

GET  /province/{province_id}/preview?hours=24 → {
  "current": {...state...},
  "projected_deltas": {...changes...},
  "spool_24h_possible": true/false,
  "max_spool_hours": 24,
  "warnings": ["HUNGER_IN_36H"],
  "market_suggestion": {"wasser": 3, "milch": 2}
}

POST /province/{province_id}/spool
Body: {"hours": int}
→ updated_state or {"error": "insufficient_credit"}

## Implementation Requirements

Deliver COMPLETE working code:
	Pydantic models for all endpoints
	SQLAlchemy ORM with session management
	core_logic(spool_hours: int) → simulates + applies
	Full API routes with validation/error handling
 	Use seed_gebaeude.py / seed_ressourcen.py as lookup tables
	Atomic transactions, no negative resources/population
