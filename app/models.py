from sqlalchemy import Column, Integer, Float, String, ForeignKey, JSON, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
import json

Base = declarative_base()

class Player(Base):
    __tablename__ = 'players'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    time_credit = Column(Float, default=240.0)
    tech_level = Column(Integer, default=0)
    provinces = relationship("Province", back_populates="player")

class Province(Base):
    __tablename__ = 'provinzen'
    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    world_x = Column(Integer, nullable=False)
    world_y = Column(Integer, nullable=False)
    name = Column(String, default='')
    terrain = Column(String, default='Grasland')
    population = Column(Integer, default=10)
    mips = Column(Integer, default=0)
    moral = Column(Integer, default=50)
    gesundheit = Column(Integer, default=50)
    marktpunkte = Column(Integer, default=0)
    strassennetz = Column(Integer, default=0)
    einheiten_count = Column(Integer, default=0)
    
    player = relationship("Player", back_populates="provinces")
    buildings = relationship("BuildingInstance", back_populates="province")
    lager = relationship("ProvinceLager", back_populates="province")

class BuildingType(Base):
    __tablename__ = 'gebaeude_typen'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    produktion = Column(String, default='[]') # JSON string
    rohstoffverbrauch = Column(String, default='[]') # JSON string
    arbeiter = Column(Integer, default=0)
    wohnraum = Column(Integer, default=0)
    lagerkapazitaet = Column(Integer, default=0)
    terrain_effektivitaet = Column(String, default='{}') # JSON string

class BuildingInstance(Base):
    __tablename__ = 'provinz_gebaeude'
    id = Column(Integer, primary_key=True, autoincrement=True)
    provinz_id = Column(Integer, ForeignKey('provinzen.id'), nullable=False)
    gebaeude_typ_id = Column(Integer, ForeignKey('gebaeude_typen.id'), nullable=False)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    stufe = Column(Integer, default=1)
    
    province = relationship("Province", back_populates="buildings")
    type = relationship("BuildingType")

class Resource(Base):
    __tablename__ = 'ressourcen'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    typ = Column(String, nullable=False) # Getränk, Nahrung, etc.
    wert = Column(Integer, default=0)

class ProvinceLager(Base):
    __tablename__ = 'provinz_lager'
    id = Column(Integer, primary_key=True, autoincrement=True)
    provinz_id = Column(Integer, ForeignKey('provinzen.id'), nullable=False)
    ressource_id = Column(Integer, ForeignKey('ressourcen.id'), nullable=False)
    menge = Column(Integer, default=0)
    
    province = relationship("Province", back_populates="lager")
    resource = relationship("Resource")

class SystemLock(Base):
    __tablename__ = 'system_locks'
    task_name = Column(String, primary_key=True)
    is_running = Column(Integer, default=0)
    last_run = Column(DateTime)
    error_count = Column(Integer, default=0)

class TickLog(Base):
    __tablename__ = 'tick_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, server_default=func.now())
    duration_ms = Column(Integer)
    status = Column(Integer) # 1=Success, 0=Failed
    provinces_processed = Column(Integer)
    details = Column(String)

# Engine setup
engine = create_engine('sqlite:///verbrannte_zone.db')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
