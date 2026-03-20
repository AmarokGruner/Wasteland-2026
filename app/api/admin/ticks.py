from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import get_db, SystemLock, TickLog
from app.api.admin.users import require_admin
from app.tick_logic import run_tick
from typing import List

router = APIRouter(tags=["Admin-Ticks"])

@router.get("/ticks/status")
def get_tick_status(token: str, db: Session = Depends(get_db)):
    require_admin(token)
    lock = db.query(SystemLock).filter(SystemLock.task_name == "server_tick").first()
    if not lock:
        return {
            "is_running": False,
            "last_run": None,
            "error_count": 0,
            "last_tick_duration": 0,
            "last_tick_status": -1
        }
    
    # Get last log for duration and status
    last_log = db.query(TickLog).order_by(TickLog.timestamp.desc()).first()
    
    return {
        "is_running": bool(lock.is_running),
        "last_run": lock.last_run.isoformat() if lock.last_run else None,
        "error_count": lock.error_count,
        "last_tick_duration": last_log.duration_ms if last_log else 0,
        "last_tick_status": last_log.status if last_log else -1
    }

@router.get("/ticks")
def get_tick_history(token: str, limit: int = 50, db: Session = Depends(get_db)):
    require_admin(token)
    logs = db.query(TickLog).order_by(TickLog.timestamp.desc()).limit(limit).all()
    return logs

@router.post("/ticks/force")
def force_tick(token: str, db: Session = Depends(get_db)):
    require_admin(token)
    success = run_tick(db)
    if success:
        return {"success": True, "message": "Tick erfolgreich erzwungen"}
    else:
        return {"success": False, "message": "Tick läuft bereits oder Fehler"}
