from app.models import Base, create_engine, SessionLocal
import os

DB_PATH = "verbrannte_zone.db"
engine = create_engine(f"sqlite:///{DB_PATH}")

def migrate():
    print("Möchte Tabellen für Marktplatz und Handel erstellen...")
    # This will create all tables that don't exist yet
    Base.metadata.create_all(bind=engine)
    print("Migration abgeschlossen.")

if __name__ == "__main__":
    migrate()
