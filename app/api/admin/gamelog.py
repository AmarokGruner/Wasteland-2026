from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.models import get_db, GameLogEntry, Player, Province
from app.api.admin.users import require_admin
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/admin/gamelog", tags=["Admin-Gamelog"])

class AdminGameLogResponse(BaseModel):
    id: int
    created_at: datetime
    player_name: Optional[str]
    event_type: str
    province_name: Optional[str]
    message: str

    class Config:
        from_attributes = True

@router.get("", response_model=List[AdminGameLogResponse])
def get_admin_gamelog(
    token: str,
    player_id: Optional[int] = None,
    event_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    require_admin(token)
    
    query = db.query(GameLogEntry)
    
    if player_id:
        query = query.filter(GameLogEntry.player_id == player_id)
    
    if event_type:
        query = query.filter(GameLogEntry.event_type == event_type)
        
    if search:
        query = query.filter(GameLogEntry.message.ilike(f"%{search}%"))
        
    entries = query.order_by(GameLogEntry.created_at.desc()).limit(limit).all()
    
    result = []
    for e in entries:
        player = db.query(Player).filter(Player.id == e.player_id).first() if e.player_id else None
        province = db.query(Province).filter(Province.id == e.province_id).first() if e.province_id else None
        
        result.append({
            "id": e.id,
            "created_at": e.created_at,
            "player_name": player.name if player else None,
            "event_type": e.event_type,
            "province_name": province.name if province else None,
            "message": e.message
        })
        
    return result
