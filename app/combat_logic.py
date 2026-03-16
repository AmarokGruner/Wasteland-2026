import json
import random
from math import floor
from sqlalchemy.orm import Session
from .models import Province, Army, CombatLog, Unit, BuildingInstance

def get_unit_stats(db: Session, einheiten_typ_id: int):
    # This would normally query seed_einheiten or similar
    # For now, we use defaults or a mock mapping
    # nahkampf_staerke, nahkampf_panzerung, fernkampf_panzerung
    stats = {
        "soldier": {"atk": 10, "def_bonus": 0},
        "default": {"atk": 5, "def_bonus": 0}
    }
    # In a real scenario, we would have a table for UnitType specs
    return stats.get("soldier")

def calculate_army_power(units: list):
    """
    atk_power = sum(unit.count * unit.nahkampf_staerke * (unit.training/100) * (unit.fitness/100))
    """
    total_power = 0.0
    for unit in units:
        # Assuming nahkampf_staerke = 10 for now as per docs logic example
        atk = 10 
        training_mod = unit.get("training", 50) / 100.0
        fitness_mod = unit.get("fitness", 100) / 100.0
        total_power += unit.get("count", 0) * atk * training_mod * fitness_mod
    return total_power

def get_province_defensive_power(db: Session, province: Province):
    """
    Defender power (province garrison + buildings)
    """
    # 1. Garrison (Units table in province)
    garrison_power = 0.0
    for unit in province.units:
        atk = 10
        garrison_power += unit.count * atk * (unit.training/100.0) * (unit.fitness/100.0)
    
    # 2. Stationed Armies (Defender owner)
    army_power = 0.0
    for army in province.stationed_armies:
        if army.owner_id == province.player_id and army.status != "marching":
            army_power += calculate_army_power(json.loads(army.units_json))
            
    total_def_power = garrison_power + army_power
    
    # 3. Defense bonuses
    # Palisade (festung=1)
    has_palisade = db.query(BuildingInstance).join(BuildingInstance.type).filter(
        BuildingInstance.provinz_id == province.id,
        BuildingInstance.type.name.like("%Palisade%")
    ).first() is not None
    
    if has_palisade:
        total_def_power *= 1.2
        
    # Bunker
    if hasattr(province, "is_bunker_province") and province.is_bunker_province:
        total_def_power *= 1.3
        
    # Security bonus from buildings
    total_def_power += (province.security_bonus or 0) * 0.5
    
    return total_def_power

def distribute_losses(units: list, total_losses: int):
    if not units or total_losses <= 0:
        return units, 0
    
    total_count = sum(u.get("count", 0) for u in units)
    if total_count <= 0:
        return units, 0
    
    actual_losses = min(total_losses, total_count)
    remaining_losses = actual_losses
    
    new_units = []
    for unit in units:
        if remaining_losses <= 0:
            new_units.append(unit)
            continue
        
        share = unit.get("count", 0) / total_count
        loss = round(actual_losses * share)
        if loss > unit.get("count", 0):
            loss = unit.get("count", 0)
            
        unit["count"] -= loss
        remaining_losses -= loss
        if unit["count"] > 0:
            new_units.append(unit)
            
    # If there are still losses due to rounding, take from first available
    if remaining_losses > 0 and new_units:
        new_units[0]["count"] = max(0, new_units[0]["count"] - remaining_losses)
        if new_units[0]["count"] <= 0:
            new_units.pop(0)

    return new_units, actual_losses

def execute_combat_round(db: Session, combat_log: CombatLog):
    attacker_army = combat_log.attacker_army
    province = combat_log.province
    
    atk_units = json.loads(attacker_army.units_json)
    atk_power = calculate_army_power(atk_units)
    
    def_power = get_province_defensive_power(db, province)
    
    # Losses (proportional)
    # atk_losses = floor(def_power / 10 * random.uniform(0.8, 1.2))
    # def_losses = floor(atk_power / 10 * random.uniform(0.8, 1.2))
    
    atk_loss_val = floor((def_power / 10.0) * random.uniform(0.8, 1.2))
    def_loss_val = floor((atk_power / 10.0) * random.uniform(0.8, 1.2))
    
    # Apply losses to attacker
    new_atk_units, actual_atk_losses = distribute_losses(atk_units, atk_loss_val)
    attacker_army.units_json = json.dumps(new_atk_units)
    combat_log.attacker_losses += actual_atk_losses
    
    # Apply losses to defender (garrison first, then armies?)
    # For simplicity, we distribute among all defenders proportional to power
    # Garrison update
    total_def_units_count = sum(u.count for u in province.units)
    # Plus armies
    for army in province.stationed_armies:
        if army.owner_id == province.player_id:
            total_def_units_count += sum(u.get("count", 0) for u in json.loads(army.units_json))
            
    actual_def_losses_total = 0
    if total_def_units_count > 0:
        # Garrison losses
        for g_unit in province.units:
            share = g_unit.count / total_def_units_count
            loss = min(g_unit.count, round(def_loss_val * share))
            g_unit.count -= loss
            actual_def_losses_total += loss
        
        # Armies losses
        for d_army in province.stationed_armies:
            if d_army.owner_id == province.player_id:
                d_units = json.loads(d_army.units_json)
                new_d_units, a_losses = distribute_losses(d_units, def_loss_val) # This needs better sharing
                # share calculation should be global... but let's keep it simple for now
                d_army.units_json = json.dumps(new_d_units)
                actual_def_losses_total += a_losses
                
    combat_log.defender_losses += actual_def_losses_total
    
    # Fitness drain: all_combatants.fitness -= 5 per round
    for u in new_atk_units:
        u["fitness"] = max(0, u.get("fitness", 100) - 5)
    attacker_army.units_json = json.dumps(new_atk_units)
    
    for g_unit in province.units:
        g_unit.fitness = max(0, g_unit.fitness - 5)
    
    for d_army in province.stationed_armies:
        if d_army.owner_id == province.player_id:
            d_units = json.loads(d_army.units_json)
            for du in d_units:
                du["fitness"] = max(0, du.get("fitness", 100) - 5)
            d_army.units_json = json.dumps(d_units)

    # Save round in log
    rounds = json.loads(combat_log.rounds_json)
    rounds.append({
        "round": len(rounds) + 1,
        "atk_power": atk_power,
        "def_power": def_power,
        "atk_losses": actual_atk_losses,
        "def_losses": actual_def_losses_total
    })
    combat_log.rounds_json = json.dumps(rounds)
    
    # Check Outcome
    atk_total = sum(u.get("count", 0) for u in new_atk_units)
    def_total = sum(u.count for u in province.units)
    for d_army in province.stationed_armies:
        if d_army.owner_id == province.player_id:
            def_total += sum(u.get("count", 0) for u in json.loads(d_army.units_json))
            
    if atk_total <= 0:
        combat_log.outcome = "defender_wins"
        combat_log.resolved_at = func.now()
        attacker_army.status = "stationed" # Or retreat?
    elif def_total <= 0:
        combat_log.outcome = "attacker_wins"
        combat_log.resolved_at = func.now()
        conquer_province(db, province, attacker_army.owner_id)
        attacker_army.status = "stationed"

    db.commit()

def conquer_province(db: Session, province: Province, new_owner_id: int):
    # if province.has_bunker: destroy bunker
    if province.has_bunker:
        from .bunker_logic import destroy_bunker
        destroy_bunker(db, province)
        
    # province.owner = attacker.owner
    province.player_id = new_owner_id
    # moral of conquered province = 10
    province.moral = 10
    
    # Log event
    from .trade_route_logic import log_game_event
    log_game_event(db, province.id, "PROVINCE_CONQUERED", f"Province {province.id} has been conquered by player {new_owner_id}")
