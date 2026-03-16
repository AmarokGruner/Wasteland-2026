from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models import get_db, PlayerMessage, Player
from pydantic import BaseModel, constr
from datetime import datetime

router = APIRouter(prefix="/messages", tags=["messages"])

class PlayerMessageResponse(BaseModel):
    id: int
    sender_id: int
    sender_name: Optional[str]
    recipient_id: int
    recipient_name: Optional[str]
    subject: str
    body: str
    read: bool
    sent_at: datetime

    class Config:
        from_attributes = True

class SendMessageRequest(BaseModel):
    recipient_id: int
    subject: constr(min_length=1, max_length=100)
    body: constr(min_length=1, max_length=2000)

@router.post("/send")
def send_message(
    sender_id: int,  # This should normally be taken from the auth token
    req: SendMessageRequest,
    db: Session = Depends(get_db)
):
    if sender_id == req.recipient_id:
        raise HTTPException(status_code=400, detail="Cannot message self")
    
    # Check if recipient exists
    recipient = db.query(Player).filter(Player.id == req.recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
        
    new_message = PlayerMessage(
        sender_id=sender_id,
        recipient_id=req.recipient_id,
        subject=req.subject,
        body=req.body
    )
    db.add(new_message)
    db.commit()
    return {"success": True, "message_id": new_message.id}

@router.get("/inbox/{player_id}", response_model=List[PlayerMessageResponse])
def get_inbox(player_id: int, db: Session = Depends(get_db)):
    messages = db.query(PlayerMessage).filter(
        PlayerMessage.recipient_id == player_id,
        PlayerMessage.deleted_recipient == False
    ).order_by(PlayerMessage.sent_at.desc()).all()
    
    results = []
    for msg in messages:
        sender_name = db.query(Player.name).filter(Player.id == msg.sender_id).scalar()
        results.append({
            "id": msg.id,
            "sender_id": msg.sender_id,
            "sender_name": sender_name,
            "recipient_id": msg.recipient_id,
            "recipient_name": None, # Could be added if needed
            "subject": msg.subject,
            "body": msg.body,
            "read": msg.read,
            "sent_at": msg.sent_at
        })
    return results

@router.get("/outbox/{player_id}", response_model=List[PlayerMessageResponse])
def get_outbox(player_id: int, db: Session = Depends(get_db)):
    messages = db.query(PlayerMessage).filter(
        PlayerMessage.sender_id == player_id,
        PlayerMessage.deleted_sender == False
    ).order_by(PlayerMessage.sent_at.desc()).all()
    
    results = []
    for msg in messages:
        recipient_name = db.query(Player.name).filter(Player.id == msg.recipient_id).scalar()
        results.append({
            "id": msg.id,
            "sender_id": msg.sender_id,
            "sender_name": None,
            "recipient_id": msg.recipient_id,
            "recipient_name": recipient_name,
            "subject": msg.subject,
            "body": msg.body,
            "read": msg.read,
            "sent_at": msg.sent_at
        })
    return results

@router.get("/{message_id}")
def get_message(message_id: int, player_id: int, db: Session = Depends(get_db)):
    msg = db.query(PlayerMessage).filter(PlayerMessage.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Check permission
    if msg.sender_id != player_id and msg.recipient_id != player_id:
        raise HTTPException(status_code=403, detail="Forbidden")
        
    # Mark as read if recipient
    if msg.recipient_id == player_id and not msg.read:
        msg.read = True
        db.commit()
        
    sender_name = db.query(Player.name).filter(Player.id == msg.sender_id).scalar()
    recipient_name = db.query(Player.name).filter(Player.id == msg.recipient_id).scalar()
    
    return {
        "id": msg.id,
        "sender_id": msg.sender_id,
        "sender_name": sender_name,
        "recipient_id": msg.recipient_id,
        "recipient_name": recipient_name,
        "subject": msg.subject,
        "body": msg.body,
        "read": msg.read,
        "sent_at": msg.sent_at
    }

@router.delete("/{message_id}")
def delete_message(message_id: int, player_id: int, db: Session = Depends(get_db)):
    msg = db.query(PlayerMessage).filter(PlayerMessage.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    
    if msg.sender_id == player_id:
        msg.deleted_sender = True
    elif msg.recipient_id == player_id:
        msg.deleted_recipient = True
    else:
        raise HTTPException(status_code=403, detail="Forbidden")
        
    db.commit()
    return {"success": True}

@router.get("/unread-count/{player_id}")
def get_unread_count(player_id: int, db: Session = Depends(get_db)):
    count = db.query(PlayerMessage).filter(
        PlayerMessage.recipient_id == player_id,
        PlayerMessage.read == False,
        PlayerMessage.deleted_recipient == False
    ).count()
    return {"unread_count": count}
