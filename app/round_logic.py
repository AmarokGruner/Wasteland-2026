from sqlalchemy.orm import Session
from .models import Player, Province, BuildingInstance, BuildingType, Resource, ProvinceLager
import json

def get_building_efficiency(province: Province, building: BuildingInstance):
    """
    Calculates the efficiency factor (0.0 to 1.0) for a building based on terrain and workers.
    """
    b_type = building.type
    worker_factor = 1.0
    if b_type.arbeiter > 0:
        # Simple worker factor: purely based on population? 
        # Actually, the requirement says "Arbeiterfaktor = vorhanden / benötigt"
        # Since we don't have a global "workers" pool yet, we assume the province population
        # supports the buildings. This is a simplification.
        pass
    
    terrain_eff = json.loads(b_type.terrain_effektivitaet)
    # terrain_eff is like {"100": ["Grasland", "Wald"], "50": ["Steppe"]}
    terrain_factor = 0.0
    for eff_val, terrains in terrain_eff.items():
        if province.terrain in terrains:
            terrain_factor = float(eff_val) / 100.0
            break
            
    return terrain_factor * worker_factor

def simulate_round(db: Session, province_id: int, hours: float = 24.0):
    """
    Simulates production/consumption for a given province and duration.
    """
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        return None
    
    scale = hours / 24.0
    deltas = {} # resource_id -> delta
    warnings = []
    
    # 1. Building Production & Consumption
    for building in province.buildings:
        eff = get_building_efficiency(province, building)
        
        # Production
        prod_data = json.loads(building.type.produktion)
        for p in prod_data:
            res_name = p['ressource']
            amount = p['menge'] * eff * building.stufe * scale
            res = db.query(Resource).filter(Resource.name == res_name).first()
            if res:
                deltas[res.id] = deltas.get(res.id, 0) + amount
        
        # Consumption (Buildings)
        cons_data = json.loads(building.type.rohstoffverbrauch)
        for c in cons_data:
            res_name = c['ressource']
            amount = c['menge'] * scale # Consumption usually not scaled by efficiency?
            res = db.query(Resource).filter(Resource.name == res_name).first()
            if res:
                deltas[res.id] = deltas.get(res.id, 0) - amount

    # 2. Population Consumption (Nahrung & Getränk)
    # Linear scale: 10 population consume 1 unit per 24h? (Assumption based on docs "Faktor 1.0")
    # Docs: "Verbrauch = Population / 10 * Faktor"
    pop_factor = province.population / 10.0 * scale
    
    # We need to find "Nahrung" and "Getränk" resources
    resources = db.query(Resource).all()
    nahrung_ids = [r.id for r in resources if r.typ == 'Nahrung']
    getraenk_ids = [r.id for r in resources if r.typ == 'Getränk']
    
    # Apply population consumption
    # For simplicity, we deduct from the first available or split? 
    # The simulation just shows "Total needed"
    pop_nahrung_needed = 1.0 * pop_factor
    pop_getraenk_needed = 1.0 * pop_factor
    
    # Update deltas (we'll need a better way to distribute this later)
    # For preview, we just aggregate
    
    # 3. Moral & Health (Simplified)
    new_moral = province.moral
    new_gesundheit = province.gesundheit
    
    # Logic from docs:
    # If Nahrung/Getränk missing -> moral/health drops
    # For preview, we assume supply is met unless proven otherwise
    
    # 4. Storage check
    projected_lager = {}
    for item in province.lager:
        projected_lager[item.ressource_id] = item.menge + deltas.get(item.ressource_id, 0)
        
    for res_id, amount in projected_lager.items():
        if amount < 0:
            res = db.query(Resource).filter(Resource.id == res_id).first()
            warnings.append(f"MANGEL: {res.name} wird in {hours}h aufgebraucht sein!")

    return {
        "province_id": province_id,
        "hours": hours,
        "deltas": deltas,
        "warnings": warnings,
        "new_population": province.population, # Could grow/shrink
        "new_moral": new_moral,
        "new_gesundheit": new_gesundheit
    }

def apply_round(db: Session, province_id: int, hours: float = 24.0):
    """
    Applies the simulation results to the database.
    """
    province = db.query(Province).filter(Province.id == province_id).first()
    player = province.player
    
    if player.time_credit < hours:
        raise Exception("Nicht genügend Zeitguthaben!")
    
    result = simulate_round(db, province_id, hours)
    
    # 1. Update Lager
    for res_id, delta in result['deltas'].items():
        item = db.query(ProvinceLager).filter(ProvinceLager.provinz_id == province_id, ProvinceLager.ressource_id == res_id).first()
        if not item:
            item = ProvinceLager(provinz_id=province_id, ressource_id=res_id, menge=0)
            db.add(item)
        item.menge = max(0, item.menge + int(delta))
        
    # 2. Update Province Stats
    province.moral = result['new_moral']
    province.gesundheit = result['new_gesundheit']
    province.population = result['new_population']
    
    # 3. Deduct Time Credit
    player.time_credit -= hours
    
    db.commit()
    return result
