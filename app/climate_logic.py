import random
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Province, TerrainConfig, ProvinceClimate

TERRAIN_MOISTURE_MAP = {
    "Wüste": 5.0,
    "Ödland": 15.0,
    "Steppe": 35.0,
    "Grasland": 50.0,
    "Wald": 65.0,
    "Sumpf": 85.0,
}

def get_terrain_config(db: Session, terrain_name: str) -> TerrainConfig:
    config = db.query(TerrainConfig).filter(TerrainConfig.name == terrain_name).first()
    if not config:
        config = TerrainConfig(
            name=terrain_name,
            rain_probability=0.3,
            rain_amount=10,
            average_moisture=TERRAIN_MOISTURE_MAP.get(terrain_name, 50.0)
        )
        db.add(config)
        db.commit()
    return config

def init_province_climate(db: Session, province_id: int):
    climate = db.query(ProvinceClimate).filter(ProvinceClimate.province_id == province_id).first()
    if not climate:
        province = db.query(Province).filter(Province.id == province_id).first()
        if not province:
            return None
        
        terrain_config = get_terrain_config(db, province.terrain)
        
        climate = ProvinceClimate(
            province_id=province_id,
            bodenfeuchtigkeit=terrain_config.average_moisture,
            grundwasserspiegel=50.0,
            is_raining_now=0
        )
        db.add(climate)
        db.commit()
    return climate

def process_climate_tick(db: Session, province_id: int) -> dict:
    """
    Processes hourly climate tick: rain check, moisture drain, groundwater.
    Returns dict with is_raining status for buildings to use.
    """
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        return {"is_raining": False}
    
    climate = init_province_climate(db, province_id)
    terrain_config = get_terrain_config(db, province.terrain)
    
    is_raining = False
    
    if random.random() < (terrain_config.rain_probability / 24.0):
        is_raining = True
        climate.bodenfeuchtigkeit += terrain_config.rain_amount
        climate.last_rained = datetime.now()
        climate.is_raining_now = 1
        
        climate.grundwasserspiegel += terrain_config.rain_amount * 0.1
    else:
        climate.is_raining_now = 0
    
    climate.bodenfeuchtigkeit = max(0, min(100, climate.bodenfeuchtigkeit * 0.9958))
    climate.grundwasserspiegel = max(0, min(100, climate.grundwasserspiegel))
    
    db.commit()
    
    return {
        "is_raining": is_raining,
        "bodenfeuchtigkeit": climate.bodenfeuchtigkeit,
        "grundwasserspiegel": climate.grundwasserspiegel
    }

def process_groundwater_consumption(db: Session, province_id: int):
    """
    Process groundwater consumption by wells (Brunnen).
    Should be called after building production tick.
    """
    from app.models import BuildingInstance, BuildingType
    import json
    
    province = db.query(Province).filter(Province.id == province_id).first()
    climate = db.query(ProvinceClimate).filter(ProvinceClimate.province_id == province_id).first()
    
    if not climate:
        return
    
    wells = db.query(BuildingInstance).join(BuildingType).filter(
        BuildingInstance.provinz_id == province_id,
        BuildingType.name.in_(["Brunnen", "Tiefbrunnen"])
    ).all()
    
    for well in wells:
        props = json.loads(well.type.spezial_eigenschaften)
        consumption = props.get("wasserverbrauch", 0) * well.stufe
        
        climate.grundwasserspiegel -= consumption
        climate.grundwasserspiegel = max(0, climate.grundwasserspiegel)
    
    db.commit()

def check_wasser_retry_rule(db: Session, province_id: int):
    """
    Checks if Wasser deposit can be retried.
    Returns True if grundwasserspiegel recovered and water was not found.
    """
    from app.models import ProvinceDeposit, Vorkommen
    
    climate = db.query(ProvinceClimate).filter(ProvinceClimate.province_id == province_id).first()
    if not climate:
        return False
    
    wasser_vorkommen = db.query(Vorkommen).filter(Vorkommen.name == "Wasser").first()
    if not wasser_vorkommen:
        return False
    
    deposit = db.query(ProvinceDeposit).filter(
        ProvinceDeposit.province_id == province_id,
        ProvinceDeposit.vorkommen_id == wasser_vorkommen.id
    ).first()
    
    if deposit and not deposit.deposit_found and climate.grundwasserspiegel >= 30:
        deposit.deposit_searched = 0
        db.commit()
        return True
    
    return False

def get_climate_data(db: Session, province_id: int) -> dict:
    """Returns current climate data for a province."""
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        return None
    
    climate = init_province_climate(db, province_id)
    terrain_config = get_terrain_config(db, province.terrain)
    
    return {
        "province_id": province_id,
        "terrain": province.terrain,
        "bodenfeuchtigkeit": climate.bodenfeuchtigkeit,
        "grundwasserspiegel": climate.grundwasserspiegel,
        "is_raining_now": bool(climate.is_raining_now),
        "last_rained": climate.last_rained.isoformat() if climate.last_rained else None,
        "rain_probability": terrain_config.rain_probability,
        "average_moisture": terrain_config.average_moisture
    }


def irrigate_province(db: Session, province_id: int, water_amount: float):
    """Raises bodenfeuchtigkeit by irrigation."""
    climate = init_province_climate(db, province_id)
    
    if water_amount <= 0:
        raise ValueError("Water amount must be positive")
    
    climate.bodenfeuchtigkeit = min(100, climate.bodenfeuchtigkeit + water_amount)
    db.commit()
    
    return {"success": True, "new_bodenfeuchtigkeit": climate.bodenfeuchtigkeit}