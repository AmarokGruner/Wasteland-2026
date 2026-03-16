from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import get_db, Player, Province, Army, GameLogEntry
from app.api.admin.users import require_admin
import datetime

router = APIRouter(tags=["Admin-Dashboard"])

@router.get("/admin/dashboard")
def get_dashboard_stats(token: str, db: Session = Depends(get_db)):
    require_admin(token)
    
    # KPIs
    total_provinces = db.query(Province).count()
    active_combats = db.query(Army).filter(Army.status.in_(["besieging", "in_combat"])).count()
    
    # active_players_today (users who logged in today)
    today = datetime.datetime.now(datetime.timezone.utc).date()
    # Since sqlite last_login is TIMESTAMP, we compare dates
    # We'll use a raw query or just fetch users
    conn = db.get_bind().raw_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE date(last_login) = date('now')")
    active_players_today = cur.fetchone()[0]
    cur.close()

    # Warning Lists
    
    # ⚠️ Revolten-Risiko -> Spieler mit avg Moral < 25
    revolt_risks = []
    low_moral_provinces = db.query(Province).filter(Province.moral < 25).all()
    for p in low_moral_provinces:
        owner = db.query(Player).filter(Player.id == p.player_id).first()
        revolt_risks.append({
            "player": owner.name if owner else "Unknown",
            "province": p.name or f"Prov {p.id}",
            "moral": p.moral
        })

    # 🍖 Hunger-Alarm -> Provinzen mit Hunger-Warning (< 48h)
    # Placeholder for now as it needs complex logic
    hunger_warnings = []

    # 💤 Inaktiv > 7 Tage
    inactive_players = []
    cur = conn.cursor()
    cur.execute("""
        SELECT u.username, u.last_login, (SELECT COUNT(*) FROM provinzen WHERE player_id = u.player_id) as prov_count 
        FROM users u 
        WHERE u.last_login < date('now', '-7 days') OR u.last_login IS NULL
        ORDER BY u.last_login ASC
    """)
    for row in cur.fetchall():
        inactive_players.append({
            "player": row[0],
            "last_login": row[1],
            "province_count": row[2]
        })
    cur.close()

    return {
        "active_players_today": active_players_today,
        "total_provinces": total_provinces,
        "active_combats": active_combats,
        "open_revolts": len(revolt_risks),
        "revolt_risks": revolt_risks,
        "hunger_warnings": hunger_warnings,
        "inactive_players": inactive_players
    }
