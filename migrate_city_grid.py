from sqlalchemy import Column, Integer, String, ForeignKey, create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os

DB_PATH = "verbrannte_zone.db"
engine = create_engine(f"sqlite:///{DB_PATH}")

def run_migration():
    # Check if columns exist in provinzen
    with engine.connect() as conn:
        res = conn.execute(text("PRAGMA table_info(provinzen)")).fetchall()
        columns = [r[1] for r in res]
        
        if "current_city_level" not in columns:
            print("Adding current_city_level to provinzen...")
            conn.execute(text("ALTER TABLE provinzen ADD COLUMN current_city_level INTEGER DEFAULT 0"))
        
        if "next_required_building_id" not in columns:
            print("Adding next_required_building_id to provinzen...")
            conn.execute(text("ALTER TABLE provinzen ADD COLUMN next_required_building_id INTEGER REFERENCES gebaeude_typen(id)"))
        
        conn.commit()

    # Tables province_fields and city_expansion_configs are created by Base.metadata.create_all(engine)
    # when importing models. Since we already did a check in the previous step, they should be there.
    from app.models import Base
    Base.metadata.create_all(engine)
    print("Migration complete.")

if __name__ == "__main__":
    run_migration()
