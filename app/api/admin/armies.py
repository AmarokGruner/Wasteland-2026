from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import get_db, Army, Player, Province
from typing import List

router = APIRouter(prefix="/armies", tags=["admin-armies"])

@router.get("")
def admin_get_all_armies(token: str, db: Session = Depends(get_db)):
    # In a real app, we'd verify admin role here from token
    # For now, we assume the frontend sends a valid token
    armies = db.query(Army).all()
    
    result = []
    for a in armies:
        import json
        units = json.loads(a.units_json)
        units_count = sum(u.get("count", 0) for u in units)
        
        owner = db.query(Player).filter(Player.id == a.owner_id).first()
        
        result.append({
            "id": a.id,
            "owner_id": a.owner_id,
            "owner_name": owner.name if owner else "Unbekannt",
            "province_id": a.province_id,
            "status": a.status,
            "units_count": units_count
        })
    return result

@router.delete("/{army_id}")
def admin_delete_army(army_id: int, token: str, db: Session = Depends(get_db)):
    army = db.query(Army).filter(Army.id == army_id).first()
    if not army:
        raise HTTPException(status_code=404, detail="Army not found")
    
    db.delete(army)
    db.commit()
    return {"success": True}
