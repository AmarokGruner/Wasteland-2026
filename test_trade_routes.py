"""
Test script for trade routes feature
"""
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from app.models import SessionLocal, Province, Player, ProvinceUnit, UnitType, PopulationCohort, ProvinceLager, Resource
from app.trade_route_logic import (
    create_trade_route,
    get_eligible_settlers,
    depart_route,
    execute_trade_at_destination,
    process_trade_routes
)

def test_trade_route_creation():
    db = SessionLocal()

    try:
        # Check if we have provinces
        provinces = db.query(Province).limit(2).all()
        if len(provinces) < 2:
            print("❌ Need at least 2 provinces to test trade routes")
            return False

        origin = provinces[0]
        destination = provinces[1]

        print(f"✓ Using province {origin.id} as origin")
        print(f"✓ Using province {destination.id} as destination")

        # Check for Handelskarren unit type
        karren_type = db.query(UnitType).filter(UnitType.name == "Handelskarren").first()
        if not karren_type:
            print("❌ Handelskarren unit type not found in database")
            return False
        print(f"✓ Handelskarren type found (id={karren_type.id}, speed={karren_type.geschwindigkeit})")

        # Check for eligible settlers
        eligible_count = get_eligible_settlers(db, origin.id)
        print(f"✓ Eligible settlers (tick_age 4-5): {eligible_count}")

        # Check for Handelskarren units
        karren_units = db.query(ProvinceUnit).filter(
            ProvinceUnit.province_id == origin.id,
            ProvinceUnit.einheiten_typ_id == karren_type.id
        ).first()

        if karren_units:
            print(f"✓ Handelskarren units in province: {karren_units.count}")
        else:
            print("ℹ No Handelskarren units in province - creating test unit")
            karren_units = ProvinceUnit(
                province_id=origin.id,
                einheiten_typ_id=karren_type.id,
                count=2,
                status="idle"
            )
            db.add(karren_units)
            db.commit()
            print("✓ Created 2 Handelskarren units")

        # Create test settlers if needed
        if eligible_count == 0:
            print("ℹ No eligible settlers - creating test cohort")
            cohort = PopulationCohort(
                province_id=origin.id,
                tick_age=4,
                count=5
            )
            db.add(cohort)
            db.commit()
            print("✓ Created 5 settlers (tick_age=4)")
            eligible_count = 5

        # Create test resources for cargo
        test_resource = db.query(Resource).first()
        if not test_resource:
            print("❌ No resources found in database")
            return False

        print(f"✓ Using resource '{test_resource.name}' (id={test_resource.id}) for test cargo")

        # Ensure lager has some resources
        lager_item = db.query(ProvinceLager).filter(
            ProvinceLager.provinz_id == origin.id,
            ProvinceLager.ressource_id == test_resource.id
        ).first()

        if not lager_item or lager_item.menge < 10:
            if not lager_item:
                lager_item = ProvinceLager(
                    provinz_id=origin.id,
                    ressource_id=test_resource.id,
                    menge=50
                )
                db.add(lager_item)
            else:
                lager_item.menge = 50
            db.commit()
            print("✓ Set lager to 50 units of test resource")

        # Test route creation
        print("\n--- Testing Trade Route Creation ---")
        cargo = {str(test_resource.id): 10}

        try:
            route = create_trade_route(
                db,
                origin.id,
                destination.id,
                cargo,
                settler_count=1,
                karren_count=1
            )
            print(f"✅ Trade route created successfully (id={route.id})")
            print(f"   Status: {route.status}")
            print(f"   Settlers: {route.settler_count}")
            print(f"   Karren: {route.karren_count}")

            # Test departure
            print("\n--- Testing Route Departure ---")
            route = depart_route(db, route.id)
            print(f"✅ Route departed successfully")
            print(f"   Status: {route.status}")
            print(f"   Travel ticks: {route.travel_ticks_remaining}")

            # Test tick processing
            print("\n--- Testing Tick Processing ---")
            process_trade_routes(db)
            db.refresh(route)
            print(f"✅ Tick processed")
            print(f"   Travel ticks remaining: {route.travel_ticks_remaining}")

            return True

        except ValueError as e:
            print(f"❌ Error creating trade route: {e}")
            return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Trade Routes Feature Test")
    print("=" * 60)

    success = test_trade_route_creation()

    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
    print("=" * 60)
