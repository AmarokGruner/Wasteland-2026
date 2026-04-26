from sqlalchemy.orm import Session
from .models import Province, Unit, BuildingInstance, BuildingType
from app.gamelog_logic import log_event
import json

def get_military_status(db: Session, province_id: int):
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        return None
    
    units = db.query(Unit).filter(Unit.province_id == province_id).all()
    total_soldiers = sum(u.count for u in units if u.type == "soldier")
    
    # Simple average training/fitness for status display
    if total_soldiers > 0:
        avg_training = sum(u.training * u.count for u in units if u.type == "soldier") / total_soldiers
        avg_fitness = sum(u.fitness * u.count for u in units if u.type == "soldier") / total_soldiers
    else:
        avg_training = 0
        avg_fitness = 100
        
    security_ratio = total_soldiers / max(1, province.population)
    
    return {
        "units": total_soldiers,
        "training": avg_training,
        "fitness": avg_fitness,
        "security_ratio": security_ratio,
        "security_bonus": province.security_bonus
    }

def train_units(db: Session, province_id: int, unit_type: str, count: int):
    # Check for Ausbildungscamp/Kaserne
    # The requirement says: Training requires Ausbildungscamp (ausbaukostenmips spezialeigenschaft)
    # We'll check if any building has 'spezialeigenschaft' containing 'Ausbildungscamp' or similar
    
    buildings = db.query(BuildingInstance).filter(BuildingInstance.provinz_id == province_id).all()
    has_training_facility = False
    for b in buildings:
        spec = json.loads(b.gebaeude_typ.spezial_eigenschaften) if b.gebaeude_typ.spezial_eigenschaften else {}
        if spec.get("spezialeigenschaft") == "Ausbildungscamp" or "ausbildung" in spec:
            has_training_facility = True
            break
            
    if not has_training_facility:
        raise ValueError("No training facility in province")
        
    # In a real implementation, we'd add to a queue. 
    # For now, let's assume immediate training for the "train" endpoint as per doc?
    # Doc says: Training buildings auto-train existing units when no new recruits queued
    # And: Ausbildungscamp trains 2 recruits/24h per building
    
    # We'll implement a simple version where we just create/update the Unit record
    # Actually, the recruits need to come from the population? 
    # Usually, military training converts citizens to soldiers.
    
    province = db.query(Province).filter(Province.id == province_id).first()
    if province.population < count:
        raise ValueError("Not enough population for training")
        
    province.population -= count
    
    unit = db.query(Unit).filter(Unit.province_id == province_id, Unit.type == unit_type).first()
    if not unit:
        unit = Unit(province_id=province_id, count=count, training=0, fitness=100, type=unit_type)
        db.add(unit)
    else:
        # Weighted average for training if new recruits added
        new_total = unit.count + count
        unit.training = (unit.training * unit.count) / new_total
        unit.count = new_total
        
    db.commit()
    
    # Log Event
    log_event(
        db, 
        event_type="UNITS_TRAINED", 
        message=f"{count} {unit_type} in {province.name} ausgebildet.",
        player_id=province.player_id,
        province_id=province_id
    )
    
    return unit

def dismiss_units(db: Session, province_id: int, count: int):
    province = db.query(Province).filter(Province.id == province_id).first()
    unit = db.query(Unit).filter(Unit.province_id == province_id, Unit.type == "soldier").first()
    
    if not unit or unit.count < count:
        raise ValueError("Not enough units to dismiss")
        
    if unit.count - count < province.min_soldiers:
        raise ValueError(f"Cannot dismiss below minimum soldiers ({province.min_soldiers})")
        
    unit.count -= count
    province.population += count
    db.commit()
    
    # Log Event
    log_event(
        db, 
        event_type="UNITS_DISMISSED", 
        message=f"{count} Einheiten in {province.name} entlassen.",
        player_id=province.player_id,
        province_id=province_id
    )
    
    return unit

def process_military_tick(db: Session, province_id: int):
    province = db.query(Province).filter(Province.id == province_id).first()
    units = db.query(Unit).filter(Unit.province_id == province_id).all()
    
    # 1. Update security bonus from buildings
    total_sec_bonus = 0
    buildings = db.query(BuildingInstance).filter(BuildingInstance.provinz_id == province_id).all()
    for b in buildings:
        spec = json.loads(b.gebaeude_typ.spezial_eigenschaften) if b.gebaeude_typ.spezial_eigenschaften else {}
        total_sec_bonus += spec.get("security_bonus", 0)
    province.security_bonus = total_sec_bonus
    
    # 2. Training logic
    # Training buildings auto-train existing units when no new recruits queued (max training=100)
    # increase training by (ausbildung_total / unit_count) per tick, cap 100
    
    training_power = 0
    for b in buildings:
        spec = json.loads(b.gebaeude_typ.spezial_eigenschaften) if b.gebaeude_typ.spezial_eigenschaften else {}
        if spec.get("spezialeigenschaft") == "Ausbildungscamp":
             # "scales with ausbaukostenmips level" - let's say 2 base + 1 per level
             training_power += 2 * b.level
             
    for unit in units:
        if unit.type == "soldier" and unit.count > 0:
            # Simple training increase
            unit.training = min(100, unit.training + (training_power / max(1, unit.count)))
            
            # 3. Fitness logic
            # idle units: fitness += 1/tick, cap 100
            unit.fitness = min(100, unit.fitness + 1)
            
    # 4. Security & Moral
    total_soldiers = sum(u.count for u in units if u.type == "soldier")
    security_ratio = total_soldiers / max(1, province.population)
    
    if security_ratio >= 0.1:
        province.moral = min(100, province.moral + province.security_bonus // 10) # Scaling bonus
    else:
        # proportional_malus
        malus = int((0.1 - security_ratio) * 100)
        province.moral = max(0, province.moral - malus)
        
    db.commit()
