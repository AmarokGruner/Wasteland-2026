from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models import get_db, GameLogEntry, Player, PlayerNotificationSettings
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/gamelog", tags=["gamelog"])

class GameLogEntryResponse(BaseModel):
    id: int
    event_type: str
    province_id: Optional[int]
    player_id: Optional[int]
    message: str
    visibility: str
    created_at: datetime
    is_system: bool

    class Config:
        from_attributes = True

class NotificationSettingsUpdate(BaseModel):
    show_war: Optional[bool] = None
    show_trade: Optional[bool] = None
    show_system: Optional[bool] = None
    max_entries: Optional[int] = None

@router.get("/", response_model=List[GameLogEntryResponse])
def get_gamelog(
    type: Optional[str] = None,
    player: Optional[int] = None,
    limit: int = Query(50, ge=10, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(GameLogEntry)
    
    if type:
        query = query.filter(GameLogEntry.event_type == type)
    
    if player:
        # Show public events OR events for this specific player
        query = query.filter((GameLogEntry.visibility == "all") | (GameLogEntry.player_id == player))
    else:
        # Only public events if no player specified
        query = query.filter(GameLogEntry.visibility == "all")

    return query.order_by(GameLogEntry.created_at.desc()).limit(limit).all()

@router.get("/search", response_model=List[GameLogEntryResponse])
def search_gamelog(
    q: str,
    player: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(GameLogEntry).filter(GameLogEntry.message.contains(q))
    
    if player:
        query = query.filter((GameLogEntry.visibility == "all") | (GameLogEntry.player_id == player))
    else:
        query = query.filter(GameLogEntry.visibility == "all")
        
    return query.order_by(GameLogEntry.created_at.desc()).limit(100).all()

@router.post("/settings/{player_id}")
def update_notification_settings(
    player_id: int, 
    settings: NotificationSettingsUpdate, 
    db: Session = Depends(get_db)
):
    db_settings = db.query(PlayerNotificationSettings).filter(PlayerNotificationSettings.player_id == player_id).first()
    if not db_settings:
        db_settings = PlayerNotificationSettings(player_id=player_id)
        db.add(db_settings)
    
    if settings.show_war is not None:
        db_settings.show_war = settings.show_war
    if settings.show_trade is not None:
        db_settings.show_trade = settings.show_trade
    if settings.show_system is not None:
        db_settings.show_system = settings.show_system
    if settings.max_entries is not None:
        db_settings.max_entries = settings.max_entries
        
    db.commit()
    return {"success": True}

@router.get("/settings/{player_id}")
def get_notification_settings(player_id: int, db: Session = Depends(get_db)):
    db_settings = db.query(PlayerNotificationSettings).filter(PlayerNotificationSettings.player_id == player_id).first()
    if not db_settings:
        return {
            "player_id": player_id,
            "show_war": True,
            "show_trade": True,
            "show_system": True,
            "max_entries": 50
        }
    return db_settings
