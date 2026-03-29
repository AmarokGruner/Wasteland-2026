import os
import sys

# Absolute path setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from app.database import SessionLocal, engine
from app.models import Base
from app.tick_logic import run_tick

def test():
    print(f"--- Running Tick Test (Root: {BASE_DIR}) ---")
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        print("Starting run_tick(db)...")
        run_tick(db)
        print("run_tick(db) finished. Check logs.")
    except Exception as e:
        import traceback
        print(f"FAILED with Exception: {e}")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test()
