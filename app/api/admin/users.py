from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import json

from app.database import get_connection
from app.api.auth import get_token_user, create_access_token

router = APIRouter(tags=["Admin-Data-Editors"])

# --- Helper Functions ---
def require_admin(token: str):
    user = get_token_user(token)
    if not user or user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Nicht autorisiert")
    return user

def log_admin_action(admin_id: int, action: str, target_type: str = None, target_id: str = None, payload: dict = None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO admin_logs (admin_id, action, target_type, target_id, payload) VALUES (?, ?, ?, ?, ?)",
        (admin_id, action, target_type, target_id, json.dumps(payload or {}))
    )
    conn.commit()
    conn.close()

# --- User Models ---
class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "player"
    player_id: Optional[int] = None

# --- User Endpoints ---
@router.get("/users")
def get_users(token: str):
    require_admin(token)
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.id, u.username, u.role, u.player_id, p.name as player_name 
        FROM users u
        LEFT JOIN players p ON u.player_id = p.id
    """)
    rows = cur.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

@router.post("/users")
def create_user(req: UserCreate, token: str):
    require_admin(token)
    
    conn = get_connection()
    cur = conn.cursor()
    
    hashed = req.password
    import bcrypt
    if isinstance(hashed, str):
        hashed = hashed.encode('utf-8')
    hashed = bcrypt.hashpw(hashed, bcrypt.gensalt()).decode('utf-8')
    
    cur.execute(
        "INSERT INTO users (username, password, role, player_id) VALUES (?, ?, ?, ?)",
        (req.username, hashed, req.role, req.player_id)
    )
    user_id = cur.lastrowid
    
    conn.commit()
    conn.close()
    
    log_admin_action(0, "create_user", "user", str(user_id), {"username": req.username})
    
    return {"id": user_id, "username": req.username}

@router.get("/log")
def get_admin_log(token: str):
    require_admin(token)
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM admin_logs ORDER BY id DESC LIMIT 100")
    rows = cur.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]