from app.models import SessionLocal, CityExpansionConfig, BuildingType, Province
import json

def seed_city_config():
    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(CityExpansionConfig).count() > 0:
            print("CityExpansionConfig already seeded.")
            return

        # Define 15x15 grid center at (7,7)
        # Level 1 (Camp): 5 fields cross
        l1 = [7*15+7, 6*15+7, 8*15+7, 7*15+6, 7*15+8]
        # Level 2 (Siedlung): Diagonals
        l2 = [6*15+6, 6*15+8, 8*15+6, 8*15+8]
        # Level 3 (Dorf): Inner circle expand
        l3 = [5*15+7, 9*15+7, 7*15+5, 7*15+9]
        # Level 4 (Kleinstadt): Expand outer cross
        l4 = [4*15+7, 10*15+7, 7*15+4, 7*15+10]
        # Level 5 (Stadt): Expand outer corners
        l5 = [5*15+5, 5*15+9, 9*15+5, 9*15+9]
        # Level 6 (Großstadt): Random fill
        l6 = [4*15+4, 4*15+10, 10*15+4, 10*15+10, 6*15+5, 8*15+5, 6*15+9, 8*15+9]
        # Level 7 (Metropole): Ring expand
        l7 = [3*15+7, 11*15+7, 7*15+3, 7*15+11, 4*15+5, 4*15+9, 10*15+5, 10*15+9]
        # Level 8 (Megapolis): Random fill outer
        l8 = [3*15+3, 3*15+11, 11*15+3, 11*15+11, 2*15+7, 12*15+7, 7*15+2, 7*15+12]

        configs = [
            CityExpansionConfig(level=1, unlocked_fields_json=json.dumps(l1)),
            CityExpansionConfig(level=2, unlocked_fields_json=json.dumps(l2)),
            CityExpansionConfig(level=3, unlocked_fields_json=json.dumps(l3)),
            CityExpansionConfig(level=4, unlocked_fields_json=json.dumps(l4)),
            CityExpansionConfig(level=5, unlocked_fields_json=json.dumps(l5)),
            CityExpansionConfig(level=6, unlocked_fields_json=json.dumps(l6)),
            CityExpansionConfig(level=7, unlocked_fields_json=json.dumps(l7)),
            CityExpansionConfig(level=8, unlocked_fields_json=json.dumps(l8))
        ]
        
        db.add_all(configs)
        
        # Ensure 'Siedlung' building exists and set as next_required for level 0
        # This is just for testing if next_required_building works
        # In a real scenario, this would be part of a larger seed
        
        db.commit()
        print("CityExpansionConfig seeded successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_city_config()
