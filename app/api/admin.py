"""
Admin API - Player Management Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import Player, Province, User, SessionLocal

router = APIRouter(prefix="/admin", tags=["admin"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/players")
async def get_all_players(db: Session = Depends(get_db)):
    """Get all players with their provinces count and last login"""
    players = db.query(Player).all()
    result = []
    
    for p in players:
        # Get user info
        user = db.query(User).filter(User.player_id == p.id).first()
        
        result.append({
            "id": p.id,
            "name": p.name,
            "tech_level": p.tech_level,
            "regierungsform": p.regierungsform.name if p.regierungsform else "Unknown",
            "provinces": len(p.provinces),
            "last_login": user.last_login.isoformat() if user and user.last_login else None,
            "status": "active" if user and user.last_login and (datetime.now() - user.last_login).days < 7 else "inactive",
            "health": 100,  # TODO: Get from active province
            "moral": 100   # TODO: Get from active province
        })
    
    return result

@router.post("/player/{player_id}/reset")
async def reset_player(player_id: int, db: Session = Depends(get_db)):
    """Reset a player's account (24h cooldown)"""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # TODO: Check 24h cooldown
    # TODO: Reset player data
    return {"success": True, "message": f"Player {player.name} reset successfully"}

@router.post("/player/{player_id}/ban")
async def ban_player(player_id: int, db: Session = Depends(get_db)):
    """Ban a player permanently"""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # TODO: Set ban flag in User table
    user = db.query(User).filter(User.player_id == player_id).first()
    if user:
        user.role = "banned"
        db.commit()
    
    return {"success": True, "message": f"Player {player.name} banned"}

@router.post("/province/{player_id}/set")
async def set_province_stat(player_id: int, stat: dict, db: Session = Depends(get_db)):
    """Set a statistic for player's province (moral, health, etc.)"""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Get first province
    if not player.provinces:
        raise HTTPException(status_code=400, detail="Player has no provinces")
    
    province = player.provinces[0]
    
    # Set value based on stat type
    stat_key = list(stat.keys())[0]
    value = stat[stat_key]
    
    if stat_key == "moral":
        province.morale = value
    elif stat_key == "health":
        province.health_percentage = value
    else:
        raise HTTPException(status_code=400, detail=f"Unknown stat: {stat_key}")
    
    db.commit()
    return {"success": True, "message": f"{stat_key} set to {value}"}

@router.post("/province/{player_id}/add-mips")
async def add_mips(player_id: int, data: dict, db: Session = Depends(get_db)):
    """Add MIPS to player"""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    amount = data.get("amount", 0)
    player.staatskonto += amount
    db.commit()
    
    return {"success": True, "message": f"Added {amount} MIPS to player {player.name}"}
