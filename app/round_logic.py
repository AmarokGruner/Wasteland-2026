from sqlalchemy.orm import Session
from .models import Player, Province, BuildingInstance, BuildingType, Resource, ProvinceLager, RoadInstance
import json

def get_building_efficiency(province: Province, building: BuildingInstance):
    """
    Calculates the efficiency factor (0.0 to 1.0) for a building based on terrain and workers.
    """
    b_type = building.type
    worker_factor = 1.0
    if b_type.arbeiter > 0:
        pass
    
    terrain_eff = json.loads(b_type.terrain_effektivitaet)
    terrain_factor = 0.0
    for eff_val, terrains in terrain_eff.items():
        if province.terrain in terrains:
            terrain_factor = float(eff_val) / 100.0
            break
            
    return terrain_factor * worker_factor

QUALITY_MULTIPLIERS = {1: 0.5, 2: 1.0, 3: 1.5}

def get_vorkommen_modifier(db: Session, province_id: int, building: BuildingInstance, resource_name: str) -> float:
    """
    Returns vorkommen multiplier (0.0 to 1.5) based on resource deposits.
    Returns 1.0 if no vorkommenseffektivitaet applies or deposit not found.
    """
    from app.models import ProvinceDeposit, Vorkommen
    
    b_type = building.type
    spezial = json.loads(b_type.spezial_eigenschaften)
    vorkommen_data = spezial.get("vorkommeneffektivitaet", {})
    
    if resource_name not in vorkommen_data:
        return 1.0
    
    vorkommen_id = vorkommen_data[resource_name]
    
    deposit = db.query(ProvinceDeposit).filter(
        ProvinceDeposit.province_id == province_id,
        ProvinceDeposit.vorkommen_id == vorkommen_id
    ).first()
    
    if not deposit or not deposit.deposit_found:
        return 0.0
    
    quality = getattr(deposit, 'quality', 2)
    return QUALITY_MULTIPLIERS.get(quality, 1.0)

def is_building_rain_dependent(building: BuildingInstance) -> bool:
    """Check if building requires rain to produce."""
    spezial = json.loads(building.type.spezial_eigenschaften)
    return bool(spezial.get("regenabhaengig", False))


def is_building_coastal_only(building: BuildingInstance) -> bool:
    """Check if building only works on coast (like Entsalzungsanlage)."""
    spezial = json.loads(building.type.spezial_eigenschaften)
    return bool(spezial.get("kueste_only", False))

def simulate_round(db: Session, province_id: int, hours: float = 24.0, is_raining: bool = False):
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
        
        if is_building_rain_dependent(building) and not is_raining:
            continue
        
        if is_building_coastal_only(building):
            from app.road_logic import is_coastal_position
            has_ocean = any(
                is_coastal_position(db, province_id, b.x, b.y)
                for b in province.buildings if hasattr(b, 'x')
            )
            terrain = province.terrain or ""
            if "Ozean" not in terrain and "Wasser" not in terrain:
                continue
        
        # Production
        prod_data = json.loads(building.type.produktion)
        for p in prod_data:
            res_name = p['ressource']
            
            vorkommen_mult = get_vorkommen_modifier(db, province_id, building, res_name)
            
            amount = p['menge'] * eff * building.stufe * scale * vorkommen_mult
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
    
    # 3. Generate Arbeitspunkte (AP)
    generate_arbeitspunkte(db, province_id)
    
    # 3. Deduct Time Credit
    player.time_credit -= hours
    
    db.commit()
    return result

def calculate_strassennetz(db: Session, province_id: int) -> int:
    """
    Calculates the strassennetz value by summing wegstufe of all roads in a province.
    """
    roads = db.query(RoadInstance).filter(RoadInstance.provinz_id == province_id).all()
    total_wegstufe = 0
    
    for road in roads:
        props = json.loads(road.type.spezial_eigenschaften)
        wegstufe = props.get("wegstufe", 0)
        total_wegstufe += wegstufe
    
    return total_wegstufe

def generate_arbeitspunkte(db: Session, province_id: int):
    """
    Generates Arbeitspunkte (AP) based on population and road network.
    
    Formula:
      daily_ap = population * 0.1 (base rate)
      ap_max = daily_ap * 3 * (1 + strassennetz/100)
    
    AP are generated per day, so for a 24h tick we generate the full amount.
    """
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        return
    
    strassennetz = calculate_strassennetz(db, province_id)
    
    daily_ap = province.population * 0.1
    ap_max = int(daily_ap * 3 * (1 + strassennetz / 100))
    
    province.arbeitspunkte_max = max(ap_max, 1)
    province.strassennetz = strassennetz
    
    new_ap = int(daily_ap)
    province.arbeitspunkte_current = min(
        province.arbeitspunkte_current + new_ap,
        province.arbeitspunkte_max
    )
