import json
from sqlalchemy.orm import Session
from .models import Army, Province, CombatLog, Player
from .diplomacy_logic import get_effective_relation

def move_army(db: Session, army_id: int, target_province_id: int):
    army = db.query(Army).filter(Army.id == army_id).first()
    if not army:
        raise ValueError("Army not found")
        
    if army.status != "stationed":
        raise ValueError("Army is busy")
        
    # Validation: Move requires path connectivity (adjacent provinces)
    # Simple check: distance = 1 (world_x, world_y)
    origin = army.province
    dest = db.query(Province).filter(Province.id == target_province_id).first()
    if not dest:
        raise ValueError("Target province not found")
        
    dist = abs(origin.world_x - dest.world_x) + abs(origin.world_y - dest.world_y)
    if dist > 1:
        raise ValueError("Target province too far (not adjacent)")
        
    # Diplomacy check: Cannot attack Verbündet province
    relation = get_effective_relation(db, army.owner_id, dest.player_id)
    if relation == "verbündet" and army.owner_id != dest.player_id:
        raise ValueError("Cannot move army to allied province (use diplomacy first)")
        
    # Start movement
    army.status = "marching"
    army.target_province_id = target_province_id
    army.travel_ticks_remaining = 2 # Fixed travel time for now
    
    db.commit()
    return army

def update_armies(db: Session):
    """Called from tick_logic"""
    marching_armies = db.query(Army).filter(Army.status == "marching").all()
    for army in marching_armies:
        army.travel_ticks_remaining -= 1
        if army.travel_ticks_remaining <= 0:
            # Arrival
            army.province_id = army.target_province_id
            army.target_province_id = None
            
            # Check for combat trigger
            dest_province = army.province
            if dest_province.player_id != army.owner_id:
                relation = get_effective_relation(db, army.owner_id, dest_province.player_id)
                if relation == "feind":
                    # TRIGGER COMBAT
                    army.status = "in_combat"
                    new_log = CombatLog(
                        attacker_army_id=army.id,
                        province_id=dest_province.id,
                        status="ongoing"
                    )
                    db.add(new_log)
                else:
                    army.status = "stationed"
            else:
                army.status = "stationed"
    
    db.commit()

def process_combat_ticks(db: Session):
    """Execute combat rounds for active combat logs"""
    from .combat_logic import execute_combat_round
    active_logs = db.query(CombatLog).filter(CombatLog.outcome == "ongoing").all()
    for log in active_logs:
        execute_combat_round(db, log)
    
    db.commit()
