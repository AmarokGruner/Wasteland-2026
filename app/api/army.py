from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.models import get_db, Army, Province, CombatLog, Player

router = APIRouter(prefix="/army", tags=["army"])

class MoveArmyRequest(BaseModel):
    target_province_id: int

class ArmyUnit(BaseModel):
    einheiten_typ_id: int
    count: int
    training: float
    fitness: float

class ArmyStatusResponse(BaseModel):
    id: int
    province_id: int
    status: str
    units: List[dict]
    target_province_id: Optional[int]
    travel_ticks_remaining: int

@router.post("/{army_id}/move")
def post_move_army(army_id: int, request: MoveArmyRequest, db: Session = Depends(get_db)):
    from app.army_logic import move_army
    try:
        army = move_army(db, army_id, request.target_province_id)
        return {"success": True, "status": army.status, "ticks": army.travel_ticks_remaining}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{army_id}/status")
def get_army_status(army_id: int, db: Session = Depends(get_db)):
    import json
    army = db.query(Army).filter(Army.id == army_id).first()
    if not army:
        raise HTTPException(status_code=404, detail="Army not found")
    
    return {
        "id": army.id,
        "province_id": army.province_id,
        "status": army.status,
        "units": json.loads(army.units_json),
        "target_province_id": army.target_province_id,
        "travel_ticks_remaining": army.travel_ticks_remaining
    }

@router.post("/{army_id}/retreat")
def post_retreat_army(army_id: int, db: Session = Depends(get_db)):
    army = db.query(Army).filter(Army.id == army_id).first()
    if not army:
        raise HTTPException(status_code=404, detail="Army not found")
    
    if army.status != "in_combat":
        raise HTTPException(status_code=400, detail="Army not in combat")
        
    # Check fitness (requirement: retreat possible only if fitness > 0)
    import json
    units = json.loads(army.units_json)
    avg_fitness = sum(u.get("fitness", 0) for u in units) / len(units) if units else 0
    if avg_fitness <= 0:
         raise HTTPException(status_code=400, detail="Army too exhausted to retreat")

    # Manual retreat
    army.status = "stationed"
    # Find active combat log and set outcome
    log = db.query(CombatLog).filter(
        CombatLog.attacker_army_id == army_id,
        CombatLog.outcome == "ongoing"
    ).first()
    if log:
        log.outcome = "defender_wins"
        from sqlalchemy import func
        log.resolved_at = func.now()
        
    db.commit()
    return {"success": True, "message": "Army retreated"}

@router.get("/player/{player_id}/armies")
def get_player_armies(player_id: int, db: Session = Depends(get_db)):
    armies = db.query(Army).filter(Army.owner_id == player_id).all()
    import json
    return [{
        "id": a.id,
        "province_id": a.province_id,
        "status": a.status,
        "units_count": sum(u.get("count", 0) for u in json.loads(a.units_json)),
        "location": a.province_id
    } for a in armies]

# Province combat status
@router.get("/province/{province_id}/combat/status")
def get_province_combat_status(province_id: int, db: Session = Depends(get_db)):
    log = db.query(CombatLog).filter(
        CombatLog.province_id == province_id,
        CombatLog.outcome == "ongoing"
    ).first()
    
    if not log:
        return {"active": False}
        
    import json
    return {
        "active": True,
        "combat_log_id": log.id,
        "attacker_army_id": log.attacker_army_id,
        "rounds_completed": len(json.loads(log.rounds_json)),
        "attacker_losses": log.attacker_losses,
        "defender_losses": log.defender_losses
    }
