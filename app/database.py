import sqlite3
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

# Absolute DB path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "verbrannte_zone.db")

def get_connection():
    """Get a raw SQLite connection with foreign keys enabled.
    
    IMPORTANT: PRAGMA foreign_keys=ON must be set for every new connection,
    as SQLite disables FK enforcement by default.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Enable foreign key constraints for this connection
    conn.execute("PRAGMA foreign_keys=ON")
    
    return conn

def row_to_dict(row):
    return dict(row)

# SQLAlchemy setup
# Replace backslashes with forward slashes for SQLAlchemy's sqlite URL on Windows
DB_PATH_URL = DB_PATH.replace("\\", "/")
DATABASE_URL = f"sqlite:///{DB_PATH_URL}"

# Create engine with check_same_thread=False for multi-threaded access
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Enable foreign key constraints at the SQLAlchemy engine level
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign key constraints for all SQLAlchemy connections."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
