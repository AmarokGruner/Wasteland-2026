"""
Run this script directly to get the full traceback from the tick engine.
Usage: python run_tick_debug.py
"""
import os
import sys
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from app.database import SessionLocal, engine
from app.models import Base, Province, SystemLock, TickLog, ProvinceLager
import datetime
import time
import json

# Make sure tables exist
Base.metadata.create_all(bind=engine)

db = SessionLocal()

print("=== TICK DEBUG RUN ===")
print(f"DB: {engine.url}")

# Reset lock if stuck
lock = db.query(SystemLock).filter(SystemLock.task_name == "server_tick").first()
if lock and lock.is_running:
    print("Resetting stuck lock...")
    lock.is_running = 0
    db.commit()

provinces = db.query(Province).all()
print(f"Found {len(provinces)} provinces")

for province in provinces:
    print(f"\n--- Processing province {province.id} ---")
    try:
        from app.climate_logic import process_climate_tick
        print("  [1] climate tick...")
        climate_data = process_climate_tick(db, province.id)
        
        from app.sammler_jaeger_logic import check_and_process_feiertag
        print("  [2] feiertag check...")
        check_and_process_feiertag(db, province.id)
        
        from app.round_logic import simulate_round
        print("  [3] simulate_round...")
        result = simulate_round(db, province.id, hours=1.0, is_raining=climate_data.get("is_raining", False))
        
        if result:
            print(f"     Deltas: {result['deltas']}")
            print("  [4] applying lager deltas...")
            for res_id, delta in result['deltas'].items():
                item = db.query(ProvinceLager).filter(
                    ProvinceLager.provinz_id == province.id,
                    ProvinceLager.ressource_id == res_id
                ).first()
                if not item:
                    print(f"     Creating new lager entry for res_id={res_id}")
                    item = ProvinceLager(provinz_id=province.id, ressource_id=res_id, menge=0)
                    db.add(item)
                item.menge = max(0, item.menge + int(delta))
        
        db.commit()
        print(f"  => Province {province.id} OK")
        
    except Exception as e:
        print(f"  => ERROR in province {province.id}:")
        traceback.print_exc()
        db.rollback()

db.close()
print("\n=== DONE ===")
