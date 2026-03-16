from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models import get_db, Player, PlayerMessage
from app.api.admin.users import require_admin
from pydantic import BaseModel, constr
from typing import List, Optional
from datetime import datetime

router = APIRouter(tags=["Admin-Broadcast"])

class BroadcastRequest(BaseModel):
    """Request-Body für Admin-Broadcasts.

    Felder:
    - typ: Kennzeichnung/Level der Nachricht (z. B. info, warn, alert)
    - recipient: "all" oder eine Player-ID als String/Zahl
    - subject: Betreffzeile (kurz)
    - body: Nachrichtentext
    """
    typ: constr(strip_whitespace=True, min_length=1) = "info"
    recipient: constr(strip_whitespace=True, min_length=1)
    subject: constr(strip_whitespace=True, min_length=1)
    body: constr(strip_whitespace=True, min_length=1)

@router.post("/admin/broadcast")
def send_broadcast(req: BroadcastRequest, token: str, db: Session = Depends(get_db)):
    require_admin(token)
    
    # In a real app, 'typ' might influence the style of the message or a badge
    # Here we just prepend it to the subject or body for now if needed, 
    # or just store it if the message model supports it.
    # PlayerMessage currently doesn't have a 'type' field, but we can use the subject.
    
    prefix = f"[{req.typ.upper()}] "
    subject = prefix + req.subject
    
    if req.recipient == "all":
        players = db.query(Player).all()
        for p in players:
            msg = PlayerMessage(
                sender_id=0, # 0 = System/Admin
                recipient_id=p.id,
                subject=subject,
                body=req.body
            )
            db.add(msg)
    else:
        try:
            player_id = int(req.recipient)
            msg = PlayerMessage(
                sender_id=0,
                recipient_id=player_id,
                subject=subject,
                body=req.body
            )
            db.add(msg)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid recipient ID")
            
    db.commit()
    return {"success": True, "sent_to": req.recipient}

@router.get("/admin/broadcast/history")
def get_broadcast_history(token: str, db: Session = Depends(get_db)):
    require_admin(token)
    # Broadcasts are messages from sender_id=0
    msgs = db.query(PlayerMessage).filter(PlayerMessage.sender_id == 0).order_by(PlayerMessage.sent_at.desc()).limit(50).all()
    
    result = []
    for m in msgs:
        recipient_name = "Alle" if m.recipient_id is None else db.query(Player.name).filter(Player.id == m.recipient_id).scalar()
        result.append({
            "id": m.id,
            "sent_at": m.sent_at,
            "recipient": recipient_name,
            "subject": m.subject,
            "body": m.body
        })
    return result
