from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models import get_db, Player

router = APIRouter(prefix="/player", tags=["player"])

class SetRegierungsformRequest(BaseModel):
    form_id: int


@router.get("/{player_id}/tech")
def get_player_tech(player_id: int, db: Session = Depends(get_db)):
    """Get player's tech level and daily tech production per province"""
    from app.kultur_bildung_logic import process_player_tech_level, get_regierungsform
    
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    reg = get_regierungsform(db, player_id)
    forschungs_mult = reg.forschungsfortschritt if reg else 1.0
    
    province_details = []
    total_daily_tech = 0
    for province in player.provinces:
        tech_prod = province.tech_production or 0
        daily_tech = int(tech_prod * forschungs_mult)
        total_daily_tech += daily_tech
        
        province_details.append({
            "province_id": province.id,
            "name": province.name,
            "tech_production_base": tech_prod,
            "daily_tech_expected": daily_tech
        })
    
    return {
        "player_id": player_id,
        "total_tech_level": player.tech_level,
        "daily_tech_total": total_daily_tech,
        "forschungs_mult": forschungs_mult,
        "provinces": province_details
    }


@router.post("/{player_id}/regierungsform")
def set_regierungsform(player_id: int, request: SetRegierungsformRequest, db: Session = Depends(get_db)):
    """Set player's regierungsform"""
    from app.kultur_bildung_logic import set_player_regierungsform
    
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    result = set_player_regierungsform(db, player_id, request.form_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
    
    return result


@router.get("/{player_id}/regierungsform")
def get_player_regierungsform(player_id: int, db: Session = Depends(get_db)):
    """Get player's current regierungsform with all active modifiers"""
    from app.regierungsform_logic import get_current_regierungsform_data
    
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    data = get_current_regierungsform_data(db, player_id)
    
    if not data:
        raise HTTPException(status_code=404, detail="Regierungsform not found")
    
    return data


@router.get("/{player_id}/regierungsform/preview")
def get_regierungsform_preview(player_id: int, form_id: int, db: Session = Depends(get_db)):
    """Get preview of what modifiers a regierungsform would provide"""
    from app.regierungsform_logic import get_regierungsform_preview
    
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    preview = get_regierungsform_preview(db, player_id, form_id)
    
    if not preview:
        raise HTTPException(status_code=404, detail="Regierungsform not found")
    
    return preview


@router.get("/{player_id}/regierungsformen")
def get_available_regierungsformen(player_id: int, db: Session = Depends(get_db)):
    """Get all available regierungsformen with player eligibility"""
    from app.regierungsform_logic import get_all_regierungsformen
    
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    forms = get_all_regierungsformen(db, player_id)
    
    return {"player_id": player_id, "regierungsformen": forms}


class SetDiplomacyRequest(BaseModel):
    target_player_id: int
    status: str


class DiplomacyRelationResponse(BaseModel):
    id: int
    player_id: int
    target_player_id: int
    status: str
    effective_relation: str | None = None
    updated_at: str | None = None


@router.get("/{player_id}/diplomacy")
def get_player_diplomacy(player_id: int, db: Session = Depends(get_db)):
    """Get all diplomacy relations for a player"""
    from app.diplomacy_logic import get_player_relations
    
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    relations = get_player_relations(db, player_id)
    
    return {"player_id": player_id, "relations": relations}


@router.post("/{player_id}/diplomacy")
def set_diplomacy(player_id: int, request: SetDiplomacyRequest, db: Session = Depends(get_db)):
    """Set a diplomacy relation for a player"""
    from app.diplomacy_logic import set_diplomacy_relation
    
    result = set_diplomacy_relation(db, player_id, request.target_player_id, request.status)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
    
    return result


@router.get("/{player_id}/diplomacy/{target_player_id}")
def get_diplomacy_relation(player_id: int, target_player_id: int, db: Session = Depends(get_db)):
    """Get the effective bilateral diplomacy relation between two players"""
    from app.diplomacy_logic import get_effective_relation
    
    player = db.query(Player).filter(Player.id == player_id).first()
    target = db.query(Player).filter(Player.id == target_player_id).first()
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    if not target:
        raise HTTPException(status_code=404, detail="Target player not found")
    
    effective = get_effective_relation(db, player_id, target_player_id)
    
    return {
        "player_id": player_id,
        "target_player_id": target_player_id,
        "effective_relation": effective
    }


@router.get("/{player_id}/diplomacy/enemies")
def get_player_enemies(player_id: int, db: Session = Depends(get_db)):
    """Get all enemies (feind/unerwünscht) for quick combat lookup"""
    from app.diplomacy_logic import get_enemies
    
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    enemies = get_enemies(db, player_id)
    
    return {"player_id": player_id, "enemies": enemies}


router.include_router(router)