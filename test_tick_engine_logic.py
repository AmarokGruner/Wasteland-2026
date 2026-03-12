import sys
import os

# Add parent directory to path to import app modules
sys.path.append(os.getcwd())

from app.models import SessionLocal, Province, ProvinceLager
from app.tick_logic import run_tick

def test_tick():
    db = SessionLocal()
    try:
        print("Starting manual tick test...")
        
        # 1. Check initial state of a province
        province = db.query(Province).first()
        if not province:
            print("No provinces found in DB. Cannot test.")
            return
        
        print(f"Testing with Province {province.id} ({province.name})")
        
        initial_lager = {l.ressource_id: l.menge for l in province.lager}
        print(f"Initial Lager: {initial_lager}")
        
        # 2. Run tick
        success = run_tick(db)
        print(f"Tick execution success: {success}")
        
        # 3. Check final state
        db.refresh(province)
        final_lager = {l.ressource_id: l.menge for l in province.lager}
        print(f"Final Lager: {final_lager}")
        
        # Determine if anything changed
        changed = False
        for res_id, amount in final_lager.items():
            if amount != initial_lager.get(res_id, 0):
                print(f"Resource {res_id} changed: {initial_lager.get(res_id, 0)} -> {amount}")
                changed = True
        
        if not changed:
            print("No changes detected in lager. (Note: This could be normal if no production buildings exist or missing resources)")
        else:
            print("Tick logic successfully updated the database!")
            
    finally:
        db.close()

if __name__ == "__main__":
    test_tick()
