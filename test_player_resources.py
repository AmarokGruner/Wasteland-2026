#!/usr/bin/env python3
from app.models import SessionLocal, Player, Province, ProvinceLager
from sqlalchemy import func

db = SessionLocal()

player_id = 4
player = db.query(Player).filter(Player.id == player_id).first()
print(f"Player: {player.name if player else 'Not found'}")

if player:
    print(f"  staatskonto: {getattr(player, 'staatskonto', 'MISSING')}")
    print(f"  time_credit: {getattr(player, 'time_credit', 'MISSING')}")

    provinces = db.query(Province).filter(Province.player_id == player_id).all()
    print(f"  Provinces: {len(provinces)}")

    for p in provinces[:2]:
        print(f"    Province {p.id}: pop={p.population}, moral={p.moral}")

db.close()
