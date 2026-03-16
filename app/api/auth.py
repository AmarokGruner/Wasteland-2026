from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import datetime
from datetime import timedelta, timezone
from jose import JWTError, jwt
import bcrypt

# Diese Imports müssen aus config.py kommen
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from app.database import get_connection

router = APIRouter(prefix="/auth", tags=["Auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    username: str
    player_id: Optional[int]

class RefreshRequest(BaseModel):
    refresh_token: str

def verify_password(plain_password, hashed_password):
    try:
        if isinstance(plain_password, str):
            plain_password = plain_password.encode('utf-8')
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
        return bcrypt.checkpw(plain_password, hashed_password)
    except Exception:
        return False

def get_password_hash(password):
    if isinstance(password, str):
        password = password.encode('utf-8')
    return bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    expire = datetime.datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = data.copy()
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_token_user(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT id FROM users WHERE username=?", (req.username,))
    if cur.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Benutzername bereits vergeben")
    
    hashed = get_password_hash(req.password)
    cur.execute(
        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
        (req.username, hashed, "player")
    )
    user_id = cur.lastrowid
    
    cur.execute("INSERT INTO players (name) VALUES (?)", (req.username,))
    player_id = cur.lastrowid
    
    cur.execute("UPDATE users SET player_id=? WHERE id=?", (player_id, user_id))
    
    conn.commit()
    conn.close()
    
    access_token = create_access_token({"sub": req.username})
    refresh_token = create_refresh_token({"sub": req.username})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        role="player",
        username=req.username,
        player_id=player_id
    )

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM users WHERE username=?", (req.username,))
    row = cur.fetchone()
    
    if not row or not verify_password(req.password, row["password"]):
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = dict(row)
    
    access_token = create_access_token({"sub": req.username})
    refresh_token = create_refresh_token({"sub": req.username})
    
    # Update last_login
    cur.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (row["id"],))
    conn.commit()
    conn.close()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        role=user["role"],
        username=user["username"],
        player_id=user.get("player_id")
    )

@router.post("/refresh", response_model=TokenResponse)
def refresh(req: RefreshRequest):
    try:
        payload = jwt.decode(req.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        username = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = dict(row)
    access_token = create_access_token({"sub": username})
    new_refresh_token = create_refresh_token({"sub": username})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        role=user["role"],
        username=user["username"],
        player_id=user.get("player_id")
    )

@router.post("/logout")
def logout():
    return {"message": "Logged out (client should discard token)"}

# Forgot/Reset Password - Simplified
class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username=?", (req.email,))
    if not cur.fetchone():
        conn.close()
        return {"message": "If email exists, reset link sent"}
    conn.close()
    return {"message": "If email exists, reset link sent"}

@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest):
    try:
        payload = jwt.decode(req.token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    hashed = get_password_hash(req.new_password)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET password=? WHERE username=?", (hashed, username))
    conn.commit()
    conn.close()
    
    return {"message": "Password reset successful"}