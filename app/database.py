import sqlite3
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Absolute DB path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "verbrannte_zone.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def row_to_dict(row):
    return dict(row)

# SQLAlchemy setup
# Replace backslashes with forward slashes for SQLAlchemy's sqlite URL on Windows
DB_PATH_URL = DB_PATH.replace("\\", "/")
DATABASE_URL = f"sqlite:///{DB_PATH_URL}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()