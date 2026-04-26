from sqlalchemy.orm import Session
from app.models import GameLogEntry, PlayerNotificationSettings
from typing import Optional

def log_event(
    db: Session,
    event_type: str,
    message: str,
    player_id: Optional[int] = None,
    province_id: Optional[int] = None,
    visibility: str = "player",
    is_system: bool = False
):
    """
    Erstellt einen neuen Gamelog-Eintrag.
    
    visibility: "player" (nur für den Spieler sichtbar), 
                "all" (für alle sichtbar, z.B. Kriegserklärungen),
                "admin" (nur für Admins sichtbar)
    """
    # Check if we should log this based on player settings (optional optimization)
    # For now, we log everything and filter on retrieval
    
    new_entry = GameLogEntry(
        event_type=event_type,
        player_id=player_id,
        province_id=province_id,
        message=message,
        visibility=visibility,
        is_system=is_system
    )
    db.add(new_entry)
    db.commit()
    return new_entry

def determine_visibility(event_type: str) -> str:
    """Bestimmt die Standard-Sichtbarkeit für einen Event-Typ"""
    public_events = ["WAR_DECLARED", "PEACE_TREATY", "PROVINCE_COLONIZED", "GLOBAL_EVENT"]
    admin_events = ["SYSTEM_CLEANUP", "ADMIN_ACTION"]
    
    if event_type in public_events:
        return "all"
    if event_type in admin_events:
        return "admin"
    return "player"
