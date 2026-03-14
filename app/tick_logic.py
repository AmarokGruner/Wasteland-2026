import time
import datetime
import json
from sqlalchemy.orm import Session
from .models import Province, SystemLock, TickLog, ProvinceLager, Player
from .round_logic import simulate_round
from .climate_logic import process_climate_tick
from .animal_logic import process_wild_animal_feeding, process_breeding

def run_tick(db: Session):
    """
    Background task to process one game tick (1 hour).
    """
    task_name = "server_tick"
    lock = db.query(SystemLock).filter(SystemLock.task_name == task_name).first()
    
    if not lock:
        lock = SystemLock(task_name=task_name, is_running=0)
        db.add(lock)
        db.commit()
    
    if lock.is_running:
        print(f"Tick already running (last run: {lock.last_run}). Skipping.")
        return False
    
    # Start tick
    start_time = time.time()
    lock.is_running = 1
    lock.last_run = datetime.datetime.now()
    db.commit()
    
    provinces_total = 0
    errors = []
    
    try:
        # Process in chunks of 100
        chunk_size = 100
        offset = 0
        
        while True:
            provinces = db.query(Province).offset(offset).limit(chunk_size).all()
            if not provinces:
                break
            
            for province in provinces:
                try:
                    # 1 hour tick - climate
                    climate_data = process_climate_tick(db, province.id)
                    
                    # Check feiertag expiry
                    from app.sammler_jaeger_logic import check_and_process_feiertag
                    check_and_process_feiertag(db, province.id)
                    
                    # 1 hour tick - production
                    result = simulate_round(db, province.id, hours=1.0, is_raining=climate_data.get("is_raining", False))
                    if not result:
                        continue
                    
                    # Apply results (copied logic from apply_round but WITHOUT time credit deduction)
                    # 1. Update Lager
                    for res_id, delta in result['deltas'].items():
                        item = db.query(ProvinceLager).filter(
                            ProvinceLager.provinz_id == province.id, 
                            ProvinceLager.ressource_id == res_id
                        ).first()
                        if not item:
                            continue
                    
                    # Sammeln/Jagen logic (once per day at midnight)
                    now = datetime.datetime.now()
                    if now.hour == 0:
                        from app.sammler_jaeger_logic import get_sammeln_loot, get_jagd_loot
                        from app.models import ProvinceSettings
                        settings = db.query(ProvinceSettings).filter(
                            ProvinceSettings.province_id == province.id
                        ).first()
                        if settings:
                            worker_mode = settings.worker_mode or "idle"
                            if worker_mode == "sammeln" and not settings.feiertag_active:
                                get_sammeln_loot(db, province.id)
                            elif worker_mode == "jagen" and not settings.feiertag_active:
                                get_jagd_loot(db, province.id)
                    
                    # Animal feeding and breeding (once per day at midnight)
                    if now.hour == 0:
                        process_wild_animal_feeding(db, province.id)
                        process_breeding(db, province.id)
                    
                    provinces_total += 1
                except Exception as e:
                    errors.append(f"Error in province {province.id}: {str(e)}")
            
            offset += chunk_size
            db.commit() # Commit per chunk
            
        status = 1 if not errors else 0
        details = json.dumps({"errors": errors}) if errors else "Success"
        
    except Exception as e:
        status = 0
        details = f"Critical tick error: {str(e)}"
        print(details)
    finally:
        duration = int((time.time() - start_time) * 1000)
        
        # Log tick
        tick_log = TickLog(
            duration_ms=duration,
            status=status,
            provinces_processed=provinces_total,
            details=details
        )
        db.add(tick_log)
        
        # Release lock
        lock.is_running = 0
        if status == 0:
            lock.error_count += 1
        db.commit()
        
    return True
